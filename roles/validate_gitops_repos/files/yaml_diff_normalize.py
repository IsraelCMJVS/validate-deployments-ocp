#!/usr/bin/env python3
import argparse, sys, yaml, json

def load_all(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # allow empty files
    if not content.strip():
        return []
    docs = list(yaml.safe_load_all(content))
    return docs

def norm(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    args = ap.parse_args()

    try:
        a_docs = load_all(args.a)
        b_docs = load_all(args.b)
    except Exception as e:
        print(f"ERROR parsing yaml: {e}", file=sys.stderr)
        # fallback: treat as different
        sys.exit(1)

    if len(a_docs) != len(b_docs):
        sys.exit(1)

    for ad, bd in zip(a_docs, b_docs):
        if norm(ad) != norm(bd):
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
