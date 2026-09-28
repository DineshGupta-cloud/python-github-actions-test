const $=s=>document.querySelector(s);
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));$("#"+b.dataset.tab).classList.add("active")});
async function json(url){const r=await fetch(url);return r.json()}
function row(c){return "<tr><td>"+c.symbol+"</td><td>₹"+c.price+"</td><td>"+c.high_52w+"</td><td>"+c.fall_pct+"%</td><td>"+c.ema9+"</td><td>"+c.ema25+"</td><td>"+c.ema99+"</td><td>"+c.rsi+"</td><td>"+c.volume_ratio+"x</td></tr>"}
async function load(){const d=await json("/api/screener");$("#dataDate").textContent=d.data[0]?.date||"—";$("#movers tbody").innerHTML=d.data.slice(0,10).map(c=>"<tr><td>"+c.symbol+"</td><td>₹"+c.price+"</td><td>"+c.change_pct+"%</td><td>"+c.rsi+"</td><td>"+c.volume_ratio+"x</td></tr>").join("");render(d.data)}
function render(data){$("#screen tbody").innerHTML=data.map(row).join("")}
$("#run").onclick=async()=>{const d=await json("/api/screener?min_fall="+$("#fall").value+"&max_rsi="+$("#rsi").value+"&min_volume_ratio="+$("#vol").value);render(d.data)}
$("#loadOptions").onclick=async()=>{const d=await json("/api/option-chain/"+$("#optSymbol").value);$("#optionMeta").textContent=d.expiry?"Expiry: "+d.expiry:"No option data";const map=new Map(d.calls.map(x=>[x.strike,x]));const puts=new Map(d.puts.map(x=>[x.strike,x]));const strikes=[...new Set([...map.keys(),...puts.keys()])].sort((a,b)=>a-b);$("#chain tbody").innerHTML=strikes.map(s=>{const c=map.get(s)||{},p=puts.get(s)||{};return "<tr><td>"+(c.openInterest||0)+"</td><td>"+(c.lastPrice||0)+"</td><td><b>"+s+"</b></td><td>"+(p.lastPrice||0)+"</td><td>"+(p.openInterest||0)+"</td></tr>"}).join("")}
load();
