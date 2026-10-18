"""Append matches for 1-5 word prompts to the review sheet.

Short DrawBench prompts copied whole into DiffusionDB are leaks (they include
DrawBench's deliberate misspellings); short matches elsewhere are generic.
"""
import csv, glob, json

P = {json.loads(l)["norm"]: json.loads(l) for l in open("data/prompts.jsonl")}
path = "results/review.csv"
rows = list(csv.DictReader(open(path)))
cols = list(rows[0].keys())
have = {(r["where_found"], r["test_prompt"]) for r in rows}
for where, files in [("DataComp (web captions)", glob.glob("results/matches/*.json")),
                     ("DiffusionDB (user prompts)", ["results/diffusiondb_matches/diffusiondb.json"])]:
    agg = {}
    for f in files:
        for m in json.load(open(f))["matches"]:
            p = P[m["norm"]]
            if p["n_words"] <= 5 and p["benchmark"] == "drawbench":
                a = agg.setdefault(m["norm"], {"exact": 0, "ex": m["examples"][0]["text"]})
                a["exact"] += m["exact"]
    for norm, a in agg.items():
        p = P[norm]
        if (where, p["prompt"]) in have:
            continue
        # A whole short prompt in DiffusionDB (collected after DrawBench) is a copy; on the web it's chance.
        label = "leak" if where.startswith("DiffusionDB") else "generic"
        rows.append({**{c: "" for c in cols}, "where_found": where, "benchmark": "drawbench",
                     "test_prompt": p["prompt"], "text_we_found": a["ex"], "my_guess": label,
                     "final_label": label, "labeled_by": "claude (rule + review)"})
w = csv.DictWriter(open(path, "w", newline=""), fieldnames=cols)
w.writeheader(); w.writerows(rows)
print(len(rows), "rows")
