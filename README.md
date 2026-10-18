# Are text-to-image benchmark prompts in the training data?

A contamination audit of three widely used text-to-image benchmarks against 1.39 billion web captions and 1.83 million user-written prompts.

**Finding:** DrawBench has leaked heavily into user-prompt data: **63 of its 200 prompts (31.5%) appear word for word in DiffusionDB**, including all 10 prompts in its "Gary Marcus et al." category and two of its deliberate misspellings. In 1.39B web captions (DataComp-1B), only 4 DrawBench prompts appear, all dictionary definitions. GenEval and T2I-CompBench are clean in both datasets.

![Leak rate by benchmark and dataset](figures/leak_rate_by_benchmark.png)

## Research question

Do the prompts used to evaluate text-to-image models appear in public data that such models are trained on, and if so, where, how often, and how closely?

1. What share of each benchmark's prompts appears in the data?
2. Are matches long, distinctive prompts (real leaks) or short, generic phrases (coincidence)?
3. Does web-scraped caption data differ from user-written prompt data?

## Data

| | What it is | Size | License |
|---|---|---|---|
| **Benchmarks** | DrawBench (May 2022), GenEval (2023), T2I-CompBench (2023, eval split) | 3,152 prompts | from each project |
| **DataComp-1B** | Image–caption pairs filtered from Common Crawl, used to train CLIP-style models | 1,387,173,656 captions | CC-BY-4.0 |
| **DiffusionDB** | Prompts typed into Stable Diffusion on Discord, collected August 2022 | 1,830,184 unique prompts | CC0 |

Only caption and prompt text was downloaded, never images.

## Method

1. **Normalize** every prompt and caption: lowercase, strip punctuation, collapse whitespace.
2. **Match** with an Aho-Corasick automaton over all 3,152 prompts. A match is either *exact* (the caption is the prompt) or *contained* (the prompt appears as a whole-word span inside a longer caption).
3. **Stream** DataComp's 2,664 parquet files one at a time (download, scan, delete), so the full 1.39B-caption scan runs on an 8 GB laptop with under 150 MB of disk in use. Total runtime was about 6 hours, with no GPU.
4. **Label** every match as *leak* (the benchmark prompt was copied) or *generic* (a common phrase that would occur by chance). All 111 matches (every match for a prompt of 6+ words, plus every match for a short DrawBench prompt) are labeled in [`results/review.csv`](results/review.csv).

### Labeling rules

- **Leak:** the caption contains essentially the whole benchmark prompt, and the prompt is distinctive (long, unusual, or containing DrawBench's deliberate typos such as "Tcennis rpacket").
- **Generic:** the benchmark prompt is a short everyday phrase ("a photo of a teddy bear") that sits inside a longer, unrelated caption.
- **Dates:** a match can only be a copy if the benchmark was public before the data was collected. GenEval and T2I-CompBench (2023) postdate DiffusionDB (August 2022), so their DiffusionDB matches are coincidences by construction.

Labels were assigned by rule, reviewed match by match by Claude (an AI assistant), and spot-checked by the author. The `labeled_by` column records which.

## Results

| Benchmark | Prompts | Leaked into DataComp-1B | Leaked into DiffusionDB |
|---|---:|---:|---:|
| DrawBench | 200 | 4 (2.0%) | **63 (31.5%)** |
| GenEval | 553 | 0 | 0 |
| T2I-CompBench | 2,399 | 0 | 0 |

Raw match rates before labeling are higher, because short generic prompts match often: 49.6% of GenEval's 1–5 word prompts appear somewhere in DataComp (mostly "a photo of a …"). None of the 863 GenEval or T2I-CompBench prompts with 10+ words appear in either dataset.

![DrawBench leaks by category](figures/drawbench_leaks_by_category.png)

**Examples of DrawBench prompts found word for word in DiffusionDB:**

- "A donkey and an octopus are playing a game. The donkey is holding a rope on one end, the octopus is holding onto the other…"
- "Supreme Court Justices play a baseball game with the FBI. The FBI is at bat, the justices are on the field…"
- "Painting of Mona Lisa but the view is from behind of Mona Lisa."
- "Tcennis rpacket." and "Bzaseball galove." (DrawBench's intentional misspellings)

**Why DataComp has DrawBench prompts at all:** DrawBench's "Descriptions" category uses dictionary definitions ("A mechanical or electrical device for measuring time."). Stock-photo sites caption images with the same definitions, so they appear in web data independently of the benchmark.

## Interpretation

- **Web captions are not where benchmark contamination happens.** In 1.39B captions, no distinctive benchmark prompt appears.
- **User-prompt data is.** People testing a new model paste the well-known test prompts, and prompt logs record them. DrawBench, the only benchmark public before DiffusionDB was collected, is heavily present; the hardest, most famous prompts leak most.
- **Why it matters:** prompt logs like DiffusionDB are reused to build fine-tuning sets, preference data, and reward models. A model or scorer trained on them may have seen roughly a third of DrawBench, including its signature hard cases, so DrawBench results for such pipelines should be read with care.

## Limitations

- **Presence is not training.** This shows the prompts are in the data, not that any specific model was trained on them or that its scores are inflated.
- **Only near-verbatim matches.** Paraphrased leaks ("a horse is riding an astronaut") are not counted, so leak counts are lower bounds.
- **Two datasets.** LAION-5B, the data behind Stable Diffusion, was withdrawn in 2023; Re-LAION and JourneyDB (Midjourney prompts) are natural next checks.
- **Labeling** was done by rule and AI review with author spot checks, not a full independent human annotation.

## Reproduce

Requires Python 3.9+, about 1 GB of free disk, and an internet connection. DataComp streams about 340 GB in total.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/build_prompts.py data/raw data/prompts.jsonl
.venv/bin/python scripts/match_corpus.py data/prompts.jsonl results/matches /tmp/dl
.venv/bin/python scripts/match_diffusiondb.py data/prompts.jsonl results/diffusiondb_matches /tmp/dl_ddb
.venv/bin/python scripts/summarize.py data/prompts.jsonl results/matches results
.venv/bin/python scripts/summarize.py data/prompts.jsonl results/diffusiondb_matches results/diffusiondb
.venv/bin/python scripts/final_counts.py
.venv/bin/python scripts/make_charts.py
```

`match_corpus.py` skips files it has already processed, so it can be stopped and restarted.

## Repository layout

```
data/raw/            benchmark prompt files as downloaded
data/prompts.jsonl   all 3,152 prompts, normalized
scripts/             matching, summary, review and chart scripts
results/review.csv   every labeled match (the core evidence)
results/final_leaks.json, results/summary.json, results/diffusiondb/summary.json
figures/             charts
```

## Credits

Benchmarks: DrawBench (Saharia et al., 2022), GenEval (Ghosh et al., 2023), T2I-CompBench (Huang et al., 2023). Data: DataComp (Gadre et al., 2023), DiffusionDB (Wang et al., 2022).
