// SachAI client utils
async function postJSON(url, data){
  const r = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  if(!r.ok) throw new Error((await r.json()).detail || 'Request failed');
  return r.json();
}
async function delJSON(url){
  const r = await fetch(url,{method:'DELETE'});
  return r.json();
}

function setActive(tabsEl, btn){
  tabsEl.querySelectorAll('button').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
}

function animatedCounter(el, target, dur=1500){
  const start = performance.now();
  function tick(t){
    const p = Math.min(1,(t-start)/dur);
    el.textContent = Math.floor(target*p).toLocaleString('en-IN');
    if(p<1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function verdictClass(v){
  if(!v) return 'verdict-UNVERIFIABLE';
  v = v.toUpperCase();
  if(v.startsWith('PARTIALLY')) return 'verdict-PARTIALLY';
  if(v==='TRUE') return 'verdict-TRUE';
  if(v==='FALSE') return 'verdict-FALSE';
  if(v==='MISLEADING') return 'verdict-MISLEADING';
  return 'verdict-UNVERIFIABLE';
}

function arc(svgId, pct){
  const c = document.getElementById(svgId);
  if(!c) return;
  const r = 70, circ = 2*Math.PI*r;
  const fg = c.querySelector('.arc-fg');
  fg.setAttribute('stroke-dasharray', circ);
  fg.setAttribute('stroke-dashoffset', circ);
  setTimeout(()=>fg.setAttribute('stroke-dashoffset', circ*(1-pct/100)),100);
}
