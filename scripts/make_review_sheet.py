"""Merge both hand-check sheets into one simple review sheet with a pre-filled guess."""
import csv, sys

out = sys.argv[1]
rows = []
for dataset, path in [("DataComp (web captions)", "results/handcheck.csv"),
                      ("DiffusionDB (user prompts)", "results/diffusiondb/handcheck.csv")]:
    for r in csv.DictReader(open(path)):
        n, exact = int(r["n_words"]), int(r["exact_hits"]) > 0
        if r["prompt"].lower().startswith("a photo of") or (n <= 7 and not exact):
            guess = "generic"   # common everyday phrase, would appear by chance
        elif exact or n >= 10:
            guess = "leak"      # long or word-for-word: someone copied the benchmark
        else:
            guess = "unclear"
        rows.append([dataset, r["benchmark"], r["prompt"], r["example_caption"], guess, ""])
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["where_found", "benchmark", "test_prompt", "text_we_found",
                "my_guess", "your_answer (leave blank if you agree)"])
    w.writerows(rows)
from collections import Counter
print(len(rows), "rows", Counter(r[4] for r in rows))
