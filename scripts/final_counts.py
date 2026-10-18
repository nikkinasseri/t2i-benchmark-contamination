"""Count confirmed leaks per dataset and benchmark from the labeled review sheet."""
import collections, csv, json

P = [json.loads(l) for l in open("data/prompts.jsonl")]
size = collections.Counter(x["benchmark"] for x in P)
leaks = collections.defaultdict(set)
for x in csv.DictReader(open("results/review.csv")):
    if x["final_label"] == "leak":
        leaks[(x["where_found"].split()[0], x["benchmark"])].add(x["test_prompt"])
summary = {f"{d}|{b}": {"leaked_prompts": len(leaks[(d, b)]), "benchmark_size": size[b]}
           for d in ("DataComp", "DiffusionDB") for b in size}
json.dump(summary, open("results/final_leaks.json", "w"), indent=1)
for k, v in summary.items():
    print(f"{k:28} {v['leaked_prompts']:3}/{v['benchmark_size']:<5} {100*v['leaked_prompts']/v['benchmark_size']:5.1f}%")
