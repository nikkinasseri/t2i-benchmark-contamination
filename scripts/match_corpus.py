"""Stream DataComp-1B caption files and find benchmark prompts inside captions.

For each parquet file: download, scan every caption, save matches, delete the file.
Already-processed files are skipped, so the script can be stopped and restarted.

Usage: match_corpus.py PROMPTS.jsonl OUT_DIR DOWNLOAD_DIR [MAX_FILES]
"""
import json, os, re, subprocess, sys, time, urllib.request

import ahocorasick
import pyarrow.parquet as pq

REPO = "mlfoundations/datacomp_1b"
MAX_EXAMPLES = 20  # matched captions kept per prompt per file; counts are always complete

prompts_path, out_dir, dl_dir = sys.argv[1:4]
max_files = int(sys.argv[4]) if len(sys.argv) > 4 else None
os.makedirs(out_dir, exist_ok=True)
os.makedirs(dl_dir, exist_ok=True)
# Remove partial downloads left by an interrupted earlier run.
for leftover in os.listdir(dl_dir):
    if leftover.endswith(".parquet"):
        os.remove(os.path.join(dl_dir, leftover))

PUNCT = re.compile(r"[^\w\s]")
SPACE = re.compile(r"\s+")

def norm(s):
    return SPACE.sub(" ", PUNCT.sub(" ", s.lower())).strip()

prompts = [json.loads(l) for l in open(prompts_path)]
# Several benchmarks can share a normalized prompt; map each text to all its ids.
by_norm = {}
for p in prompts:
    by_norm.setdefault(p["norm"], []).append(p["id"])
auto = ahocorasick.Automaton()
for text, ids in by_norm.items():
    auto.add_word(f" {text} ", text)  # padded so matches land on word boundaries
auto.make_automaton()

# The tree API returns 1000 entries per page; follow the Link header to get them all.
files, page = [], f"https://huggingface.co/api/datasets/{REPO}/tree/main"
while page:
    with urllib.request.urlopen(page) as resp:
        files += [f["path"] for f in json.load(resp) if f["path"].endswith(".parquet")]
        nxt = re.search(r'<([^>]+)>;\s*rel="next"', resp.headers.get("Link", ""))
    page = nxt.group(1) if nxt else None
files.sort()
if max_files:
    files = files[:max_files]

for i, name in enumerate(files):
    out_path = os.path.join(out_dir, name.replace(".parquet", ".json"))
    if os.path.exists(out_path):
        continue
    t0 = time.time()
    local = os.path.join(dl_dir, name)
    url = f"https://huggingface.co/datasets/{REPO}/resolve/main/{name}"
    if subprocess.run(["curl", "-sfL", "--retry", "3", "-o", local, url]).returncode != 0:
        print(f"[{i+1}/{len(files)}] {name}: download failed, skipping", flush=True)
        if os.path.exists(local):
            os.remove(local)
        continue

    counts = {}  # prompt norm -> {"exact": n, "contained": n}
    examples = {}
    n_captions = 0
    pf = pq.ParquetFile(local)
    for rg in range(pf.num_row_groups):
        t = pf.read_row_group(rg, columns=["uid", "url", "text"])
        for uid, url_, text in zip(*(t.column(c).to_pylist() for c in ("uid", "url", "text"))):
            if not text:
                continue
            n_captions += 1
            cap = norm(text)
            hits = {m for _, m in auto.iter(f" {cap} ")}
            for ptext in hits:
                kind = "exact" if cap == ptext else "contained"
                c = counts.setdefault(ptext, {"exact": 0, "contained": 0})
                c[kind] += 1
                ex = examples.setdefault(ptext, [])
                if len(ex) < MAX_EXAMPLES:
                    ex.append({"kind": kind, "uid": uid, "url": url_, "text": text})
    os.remove(local)

    result = {"file": name, "n_captions": n_captions,
              "matches": [{"norm": k, "prompt_ids": by_norm[k], **v, "examples": examples[k]}
                          for k, v in counts.items()]}
    with open(out_path + ".tmp", "w") as f:
        json.dump(result, f)
    os.replace(out_path + ".tmp", out_path)
    print(f"[{i+1}/{len(files)}] {name}: {n_captions} captions, {len(counts)} prompts hit, "
          f"{time.time() - t0:.0f}s", flush=True)
