#!/usr/bin/env python3
import argparse, sys, yaml

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--kinds", required=True)   # comma separated
    ap.add_argument("--replicas", type=int, required=True)
    args = ap.parse_args()

    kinds = set([k.strip() for k in args.kinds.split(",") if k.strip()])
    changed = False

    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()

    docs = list(yaml.safe_load_all(content)) if content.strip() else []
    out_docs = []

    for d in docs:
        if not isinstance(d, dict):
            out_docs.append(d)
            continue
        kind = d.get("kind")
        if kind in kinds:
            spec = d.setdefault("spec", {})
            # if spec exists and replicas differs => patch
            if spec.get("replicas") != args.replicas:
                spec["replicas"] = args.replicas
                changed = True
        out_docs.append(d)

    if changed:
        with open(args.file, "w", encoding="utf-8") as f:
            yaml.safe_dump_all(out_docs, f, sort_keys=False)
        print("CHANGED=1")
    else:
        print("CHANGED=0")

if __name__ == "__main__":
    main()
