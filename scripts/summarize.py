"""Aggregate per-file match results into a summary and a hand-check sheet."""
import csv, glob, json, os, sys
from collections import defaultdict

prompts_path, match_dir, out_dir = sys.argv[1:4]
prompts = [json.loads(l) for l in open(prompts_path)]
tot = defaultdict(lambda: {"exact": 0, "contained": 0, "examples": []})
n_captions = n_files = 0
for p in glob.glob(os.path.join(match_dir, "*.json")):
    r = json.load(open(p))
    n_files += 1
    n_captions += r["n_captions"]
    for m in r["matches"]:
        t = tot[m["norm"]]
        t["exact"] += m["exact"]; t["contained"] += m["contained"]
        if len(t["examples"]) < 20:
            t["examples"] += m["examples"][:20 - len(t["examples"])]

def bucket(n):
    return "1-5 words" if n <= 5 else "6-9 words" if n <= 9 else "10+ words"

table = defaultdict(lambda: {"prompts": 0, "any_match": 0, "exact_match": 0})
for p in prompts:
    t = tot.get(p["norm"])
    for key in [(p["benchmark"], "all"), (p["benchmark"], bucket(p["n_words"])), ("ALL", "all"), ("ALL", bucket(p["n_words"]))]:
        row = table[key]
        row["prompts"] += 1
        if t:
            row["any_match"] += 1
            row["exact_match"] += t["exact"] > 0
summary = {"n_files": n_files, "n_captions": n_captions,
           "table": [{"benchmark": b, "length": l, **v} for (b, l), v in sorted(table.items())]}
json.dump(summary, open(os.path.join(out_dir, "summary.json"), "w"), indent=1)

# Hand-check sheet: every matched prompt with 6+ words, longest first.
rows = []
for p in prompts:
    t = tot.get(p["norm"])
    if t and p["n_words"] >= 6:
        ex = t["examples"][0]
        rows.append([p["benchmark"], p["category"], p["n_words"], p["prompt"], t["exact"], t["contained"],
                     ex["text"], ex["url"], ""])
rows.sort(key=lambda r: -r[2])
with open(os.path.join(out_dir, "handcheck.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["benchmark", "category", "n_words", "prompt", "exact_hits", "contained_hits",
                "example_caption", "example_url", "your_verdict (leak / generic / unclear)"])
    w.writerows(rows)

print(f"{n_files} files, {n_captions:,} captions")
print(f"{'benchmark':14} {'length':10} {'prompts':>7} {'matched':>8} {'%':>6} {'exact':>6}")
for r in summary["table"]:
    print(f"{r['benchmark']:14} {r['length']:10} {r['prompts']:7} {r['any_match']:8} "
          f"{100*r['any_match']/r['prompts']:5.1f}% {r['exact_match']:6}")
print(f"hand-check rows (6+ word prompts with a match): {len(rows)}")
