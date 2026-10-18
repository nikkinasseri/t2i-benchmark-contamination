"""Combine DrawBench, GenEval and T2I-CompBench prompts into data/prompts.jsonl."""
import csv, glob, json, os, re, sys

RAW = sys.argv[1]
OUT = sys.argv[2]

def norm(s):
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

rows = []
with open(os.path.join(RAW, "drawbench.csv"), newline="") as f:
    for r in csv.DictReader(f):
        rows.append(("drawbench", r["Category"], r["Prompts"]))
with open(os.path.join(RAW, "geneval_metadata.jsonl")) as f:
    for line in f:
        r = json.loads(line)
        rows.append(("geneval", r["tag"], r["prompt"]))
for path in sorted(glob.glob(os.path.join(RAW, "t2icomp_*_val.txt"))):
    cat = os.path.basename(path)[len("t2icomp_"):-len("_val.txt")]
    with open(path) as f:
        for line in f:
            if line.strip():
                rows.append(("t2i_compbench", cat, line.strip()))

seen, n_dup = set(), 0
with open(OUT, "w") as out:
    for i, (bench, cat, p) in enumerate(rows):
        key = (bench, norm(p))
        if key in seen:
            n_dup += 1
            continue
        seen.add(key)
        out.write(json.dumps({"id": i, "benchmark": bench, "category": cat, "prompt": p,
                              "norm": norm(p), "n_words": len(norm(p).split())}) + "\n")
print(f"wrote {len(seen)} prompts ({n_dup} within-benchmark duplicates dropped)")
