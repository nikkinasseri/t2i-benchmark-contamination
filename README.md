# t2i-benchmark-contamination

I wanted to know whether the prompts we use to evaluate text-to-image models show up in the data those models are trained on. So I took the prompts from three popular benchmarks (DrawBench, GenEval, T2I-CompBench) and searched for them in 1.39B web captions from [DataComp-1B](https://huggingface.co/datasets/mlfoundations/datacomp_1b) and 1.83M user prompts from [DiffusionDB](https://github.com/poloclub/diffusiondb).

Short version: web captions are basically clean, but 63 of DrawBench's 200 prompts (31.5%) appear word for word in DiffusionDB.

![leak rate by benchmark](figures/leak_rate_by_benchmark.png)

| | prompts | in DataComp-1B | in DiffusionDB |
|---|--:|--:|--:|
| DrawBench | 200 | 4 | 63 |
| GenEval | 553 | 0 | 0 |
| T2I-CompBench | 2,399 | 0 | 0 |

My guess is that DrawBench came out with Imagen in May 2022, and DiffusionDB was scraped from the Stable Diffusion Discord in August 2022. People trying out a new model paste in the famous test prompts, and the prompt log records them. The two other benchmarks are from 2023, so they couldn't have leaked into DiffusionDB.

The most famous prompts leaked the most. All 10 of DrawBench's "Gary Marcus et al." prompts are in there (the donkey and octopus playing tug-of-war, the Supreme Court justices playing baseball against the FBI), and so are two of its intentional typos, "Tcennis rpacket" and "Bzaseball galove", which are not accidental typos.

![drawbench leaks by category](figures/drawbench_leaks_by_category.png)

The 4 DrawBench hits in DataComp are all from the "Descriptions" category, which uses dictionary definitions ("A mechanical or electrical device for measuring time."). Stock photo sites caption their images with the same definitions, so that's a coincidence, not a leak.

## How it works

Everything gets lowercased and stripped of punctuation, then I match all 3,152 prompts at once with Aho-Corasick. A prompt counts if it shows up as the whole caption or as a whole-word span inside a longer one.

DataComp is about 340GB of parquet, too big for my laptop, so `match_corpus.py` downloads one file at a time, scans it, and deletes it. The full run took about 6 hours on a MacBook with 8GB of RAM and no GPU.

Raw matches include a lot of noise. "a photo of a teddy bear" (GenEval) obviously shows up in web captions. So every match for a prompt of 6+ words, plus every short DrawBench match, got labeled as a leak or as generic. That's 111 matches in total, all in [`results/review.csv`](results/review.csv). The rule was ~ whole distinctive prompt copied = leak; short everyday phrase inside an unrelated caption = generic. The labels were done by rule plus a pass with Claude, and I spot-checked them. The `labeled_by` column says which.

## Caveats

- Being in a dataset doesn't mean a given model trained on it, or that its scores are inflated.
- I only catch near-exact copies, so paraphrased leaks are missed and these numbers are a lower bound.
- I haven't checked LAION (the original was taken down in 2023) or Midjourney prompts (JourneyDB) yet.

## Running it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/build_prompts.py data/raw data/prompts.jsonl
.venv/bin/python scripts/match_corpus.py data/prompts.jsonl results/matches /tmp/dl     # ~6 hrs, restartable
.venv/bin/python scripts/match_diffusiondb.py data/prompts.jsonl results/diffusiondb_matches /tmp/dl_ddb
.venv/bin/python scripts/summarize.py data/prompts.jsonl results/matches results
.venv/bin/python scripts/summarize.py data/prompts.jsonl results/diffusiondb_matches results/diffusiondb
.venv/bin/python scripts/final_counts.py
.venv/bin/python scripts/make_charts.py
```

Benchmarks: DrawBench (Saharia et al. 2022), GenEval (Ghosh et al. 2023), T2I-CompBench (Huang et al. 2023). Data: DataComp (Gadre et al. 2023, CC-BY-4.0), DiffusionDB (Wang et al. 2022, CC0).
