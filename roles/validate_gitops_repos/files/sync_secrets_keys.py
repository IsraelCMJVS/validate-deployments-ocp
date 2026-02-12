#!/usr/bin/env python3
import argparse, sys, yaml

def load_yaml_docs(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return list(yaml.safe_load_all(content)) if content.strip() else []

def find_secret_doc(docs):
    # If multi-doc, we apply to all Secrets; for simplicity, we only support single Secret per file
    for d in docs:
        if isinstance(d, dict) and d.get("kind") == "Secret":
            return d
    return None

def get_keys(secret):
    keys = set()
    data = secret.get("data") or {}
    sdata = secret.get("stringData") or {}
    if isinstance(data, dict):
        keys |= set(data.keys())
    if isinstance(sdata, dict):
        keys |= set(sdata.keys())
    return keys

def ensure_keys_only(prod_secret, drp_secret):
    """
    Add missing keys from prod into drp WITHOUT overwriting existing values.
    Missing keys are added into stringData with empty string "".
    """
    prod_keys = get_keys(prod_secret)
    drp_keys = get_keys(drp_secret)

    missing = sorted(list(prod_keys - drp_keys))
    if not missing:
        return False

    # Keep existing data/stringData untouched, add missing into stringData
    sdata = drp_secret.get("stringData")
    if not isinstance(sdata, dict):
        sdata = {}
    for k in missing:
        # empty value placeholder (won't overwrite anything)
        sdata[k] = ""
    drp_secret["stringData"] = sdata
    return True

def create_skeleton_from_prod(prod_secret):
    """
    Create secret manifest with same metadata/name/type and ONLY keys (empty stringData values).
    """
    out = {
        "apiVersion": prod_secret.get("apiVersion", "v1"),
        "kind": "Secret",
        "metadata": prod_secret.get("metadata", {}),
        "type": prod_secret.get("type", "Opaque"),
        "stringData": {}
    }
    for k in sorted(list(get_keys(prod_secret))):
        out["stringData"][k] = ""
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["sync", "create"], required=True)
    ap.add_argument("--prod", required=True)
    ap.add_argument("--drp", required=True)
    args = ap.parse_args()

    prod_docs = load_yaml_docs(args.prod)
    prod_secret = find_secret_doc(prod_docs)
    if prod_secret is None:
        # not a secret file -> do nothing
        print("CHANGED=0")
        sys.exit(0)

    if args.mode == "create":
        # Create skeleton in DRP path
        skel = create_skeleton_from_prod(prod_secret)
        with open(args.drp, "w", encoding="utf-8") as f:
            yaml.safe_dump(skel, f, sort_keys=False)
        print("CHANGED=1")
        sys.exit(0)

    # sync mode
    drp_docs = load_yaml_docs(args.drp)
    drp_secret = find_secret_doc(drp_docs)
    if drp_secret is None:
        # If DRP file exists but no Secret kind, create skeleton (safer)
        skel = create_skeleton_from_prod(prod_secret)
        with open(args.drp, "w", encoding="utf-8") as f:
            yaml.safe_dump(skel, f, sort_keys=False)
        print("CHANGED=1")
        sys.exit(0)

    changed = ensure_keys_only(prod_secret, drp_secret)
    if changed:
        # write back full docs (preserve other docs if present)
        new_docs = []
        for d in drp_docs:
            if isinstance(d, dict) and d.get("kind") == "Secret":
                new_docs.append(drp_secret)
            else:
                new_docs.append(d)
        with open(args.drp, "w", encoding="utf-8") as f:
            yaml.safe_dump_all(new_docs, f, sort_keys=False)
        print("CHANGED=1")
    else:
        print("CHANGED=0")

if __name__ == "__main__":
    main()
