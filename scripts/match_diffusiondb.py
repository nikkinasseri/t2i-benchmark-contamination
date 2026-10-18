"""Find benchmark prompts inside DiffusionDB user prompts (Stable Diffusion Discord).

Downloads the two prompt-metadata files, matches unique prompts, then deletes the downloads.
Output has the same shape as match_corpus.py, so summarize.py works on it.

Usage: match_diffusiondb.py PROMPTS.jsonl OUT_DIR DOWNLOAD_DIR
"""
import json, os, re, subprocess, sys

import ahocorasick
import pyarrow.parquet as pq

REPO = "poloclub/diffusiondb"
FILES = ["metadata.parquet", "metadata-large.parquet"]
MAX_EXAMPLES = 20

prompts_path, out_dir, dl_dir = sys.argv[1:4]
os.makedirs(out_dir, exist_ok=True)
os.makedirs(dl_dir, exist_ok=True)

PUNCT = re.compile(r"[^\w\s]")
SPACE = re.compile(r"\s+")

def norm(s):
    return SPACE.sub(" ", PUNCT.sub(" ", s.lower())).strip()

by_norm = {}
for p in map(json.loads, open(prompts_path)):
    by_norm.setdefault(p["norm"], []).append(p["id"])
auto = ahocorasick.Automaton()
for text in by_norm:
    auto.add_word(f" {text} ", text)
auto.make_automaton()

# Each prompt was used for several images, so count unique prompt texts.
seen = set()
counts, examples = {}, {}
for name in FILES:
    local = os.path.join(dl_dir, name)
    url = f"https://huggingface.co/datasets/{REPO}/resolve/main/{name}"
    try:
        subprocess.run(["curl", "-sfL", "--retry", "3", "-o", local, url], check=True)
        pf = pq.ParquetFile(local)
        for rg in range(pf.num_row_groups):
            for text in pf.read_row_group(rg, columns=["prompt"]).column("prompt").to_pylist():
                if not text or text in seen:
                    continue
                seen.add(text)
                cap = norm(text)
                for ptext in {m for _, m in auto.iter(f" {cap} ")}:
                    kind = "exact" if cap == ptext else "contained"
                    c = counts.setdefault(ptext, {"exact": 0, "contained": 0})
                    c[kind] += 1
                    ex = examples.setdefault(ptext, [])
                    if len(ex) < MAX_EXAMPLES:
                        ex.append({"kind": kind, "uid": "", "url": "", "text": text})
        print(f"{name}: {len(seen):,} unique prompts so far", flush=True)
    finally:
        if os.path.exists(local):
            os.remove(local)

result = {"file": "diffusiondb", "n_captions": len(seen),
          "matches": [{"norm": k, "prompt_ids": by_norm[k], **v, "examples": examples[k]}
                      for k, v in counts.items()]}
with open(os.path.join(out_dir, "diffusiondb.json"), "w") as f:
    json.dump(result, f)
print(f"done: {len(counts)} benchmark prompts matched")
