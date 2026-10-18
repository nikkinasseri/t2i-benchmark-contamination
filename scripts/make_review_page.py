"""Turn results/review.csv into a click-through review page."""
import csv, json, sys

rows = list(csv.DictReader(open(sys.argv[1])))
data = [{"where": r["where_found"], "bench": r["benchmark"], "prompt": r["test_prompt"],
         "found": r["text_we_found"], "guess": r["my_guess"]} for r in rows]
html = """<!doctype html><html><head><meta charset="utf-8"><title>Leak Review</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#fafaf8;--card:#fff;--ink:#1d1d1b;--mute:#6b6b66;--line:#e4e2dc;--leak:#c2410c;--gen:#2f6f4f;--unc:#8a6d1b;--sel:#1d1d1b}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,system-ui,sans-serif}
main{max-width:820px;margin:0 auto;padding:24px 16px 80px}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mute);margin:0 0 20px}
.bar{position:sticky;top:0;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);margin-bottom:16px;font-weight:600}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:12px}
.meta{font-size:12px;color:var(--mute);text-transform:uppercase;letter-spacing:.04em}
.lbl{font-size:12px;color:var(--mute);margin-top:8px}.txt{margin:2px 0}
.found{background:#f3f1ec;border-radius:6px;padding:6px 8px}
.guess{margin-top:10px;font-size:14px}.g-leak{color:var(--leak)}.g-generic{color:var(--gen)}.g-unclear{color:var(--unc)}
.btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
button{font:inherit;border:1px solid var(--line);background:#fff;border-radius:999px;padding:5px 14px;cursor:pointer}
button.on{background:var(--sel);color:#fff;border-color:var(--sel)}
</style></head><body><main>
<h1>Leak review</h1>
<p class="sub">Each card: a <b>test question</b> from an AI benchmark, and <b>text we found</b> in training data.
My guess is shown. Click <b>Agree</b> if it looks right, or pick a different answer.<br>
<b>leak</b> = clearly copied &nbsp;·&nbsp; <b>generic</b> = common phrase, coincidence &nbsp;·&nbsp; <b>unclear</b> = can't tell</p>
<div class="bar"><span id="bar"></span> <button id="copy" onclick="copyChanges()">Copy my answers</button></div><div id="list"></div></main>
<script>
const DATA=__DATA__;
let ans={};try{ans=JSON.parse(localStorage.getItem("review")||"{}")}catch(e){}
const esc=s=>s.replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
function render(){
  const done=Object.keys(ans).length;
  document.getElementById("bar").textContent=`${done} of ${DATA.length} reviewed`+(done===DATA.length?" — all done! Tell Claude you're finished.":"");
  document.getElementById("list").innerHTML=DATA.map((d,i)=>`<div class="card">
    <div class="meta">#${i+1} · ${esc(d.where)} · ${esc(d.bench)}</div>
    <div class="lbl">Test question</div><p class="txt">${esc(d.prompt)}</p>
    <div class="lbl">Text we found</div><p class="txt found">${esc(d.found)}</p>
    <div class="guess">My guess: <b class="g-${d.guess}">${d.guess}</b></div>
    <div class="btns">${["agree","leak","generic","unclear"].map(o=>`<button class="${ans[i]===o?"on":""}" onclick="pick(${i},'${o}')">${o==="agree"?"Agree":o}</button>`).join("")}</div>
  </div>`).join("");
}
function pick(i,o){ans[i]=o;try{localStorage.setItem("review",JSON.stringify(ans))}catch(e){}render()}
function copyChanges(){
  const ch=DATA.map((d,i)=>ans[i]&&ans[i]!=="agree"&&ans[i]!==d.guess?`#${i+1} ${ans[i]}`:null).filter(Boolean);
  const done=Object.keys(ans).length;
  const msg=`Review: ${done}/${DATA.length} reviewed. Changes: ${ch.length?ch.join(", "):"none, I agree with the rest"}`;
  const b=document.getElementById("copy");
  navigator.clipboard.writeText(msg).then(()=>{b.textContent="Copied! Paste it to Claude"},()=>{prompt("Copy this and paste it to Claude:",msg)});
}
window.getAnswers=()=>DATA.map((d,i)=>({...d,answer:ans[i]==="agree"?d.guess:(ans[i]||"")}));
render();
</script></body></html>"""
open(sys.argv[2], "w").write(html.replace("__DATA__", json.dumps(data).replace("</", "<\\/")))
print("wrote", sys.argv[2], len(data), "cards")
