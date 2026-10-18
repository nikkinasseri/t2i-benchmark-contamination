"""Draw the two README charts from results/final_leaks.json and results/review.csv."""
import collections, csv, json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, MUTED, GRID, SURFACE = "#1d1d1b", "#6b6b66", "#e4e2dc", "#fcfcfb"
WEB, USER = "#2a78d6", "#eb6834"  # validated categorical slots 1 and 2
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 11, "text.color": INK,
                     "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED})

def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)

# 1. Leak rate by benchmark and dataset
s = json.load(open("results/final_leaks.json"))
benches = [("drawbench", "DrawBench\n(May 2022)"), ("geneval", "GenEval\n(2023)"),
           ("t2i_compbench", "T2I-CompBench\n(2023)")]
fig, ax = plt.subplots(figsize=(7.5, 4.2), facecolor=SURFACE)
style(ax)
w = 0.36
for j, (ds, label, color) in enumerate([("DataComp", "DataComp-1B web captions (1.39B)", WEB),
                                        ("DiffusionDB", "DiffusionDB user prompts (1.83M)", USER)]):
    for i, (b, _) in enumerate(benches):
        v = s[f"{ds}|{b}"]
        pct = 100 * v["leaked_prompts"] / v["benchmark_size"]
        x = i + (j - 0.5) * (w + 0.03)
        ax.bar(x, pct, w, color=color, label=label if i == 0 else None, zorder=2)
        ax.text(x, pct + 0.6, f"{pct:.1f}%\n({v['leaked_prompts']}/{v['benchmark_size']})",
                ha="center", va="bottom", fontsize=9, color=INK)
ax.set_xticks(range(len(benches)), [b[1] for b in benches])
ax.set_ylim(0, 40)
ax.set_ylabel("Benchmark prompts copied word for word (%)")
ax.yaxis.grid(True, color=GRID, zorder=0)
ax.legend(frameon=False, loc="upper right", fontsize=10)
fig.suptitle("DrawBench prompts leaked into user-prompt data, not web captions",
             x=0.02, ha="left", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig("figures/leak_rate_by_benchmark.png", dpi=200, facecolor=SURFACE)

# 2. DrawBench leaks in DiffusionDB, by category
cat_of = {json.loads(l)["prompt"]: json.loads(l)["category"].strip()
          for l in open("data/prompts.jsonl") if '"drawbench"' in l}
total = collections.Counter(cat_of.values())
leaked = collections.Counter()
for r in csv.DictReader(open("results/review.csv")):
    if r["final_label"] == "leak" and r["where_found"].startswith("DiffusionDB") and r["benchmark"] == "drawbench":
        leaked[cat_of[r["test_prompt"]]] += 1
cats = sorted(total, key=lambda c: leaked[c] / total[c])
fig, ax = plt.subplots(figsize=(7.5, 4.6), facecolor=SURFACE)
style(ax)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(True)
ax.barh(range(len(cats)), [100 * leaked[c] / total[c] for c in cats], 0.62, color=USER, zorder=2)
for i, c in enumerate(cats):
    ax.text(100 * leaked[c] / total[c] + 1.5, i, f"{leaked[c]}/{total[c]}", va="center", fontsize=9)
ax.set_yticks(range(len(cats)), cats)
ax.set_xlim(0, 110)
ax.set_xlabel("Prompts in category found word for word in DiffusionDB (%)")
ax.xaxis.grid(True, color=GRID, zorder=0)
fig.suptitle("Every 'Gary Marcus et al.' prompt in DrawBench appears in DiffusionDB",
             x=0.02, ha="left", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig("figures/drawbench_leaks_by_category.png", dpi=200, facecolor=SURFACE)
print(dict(leaked))
