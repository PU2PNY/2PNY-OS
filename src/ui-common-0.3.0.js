(function(){
  function q(id){return document.getElementById(id)}
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  async function getj(url,opt,timeout){var ctl=window.AbortController?new AbortController():null,timer=null,o=Object.assign({cache:'no-store'},opt||{});if(ctl){o.signal=ctl.signal;timer=setTimeout(function(){ctl.abort()},timeout||8000)}try{var r=await fetch(url,o),j=await r.json().catch(function(){return {}});if(!r.ok)throw new Error(j.error||j.message||('HTTP '+r.status));return j}finally{if(timer)clearTimeout(timer)}}
  function setTheme(t){document.documentElement.setAttribute('data-theme',t);localStorage.setItem('pu2pny-theme',t);var b=q('themeToggle');if(b)b.textContent=t==='dark'?'☀ Claro':'☾ Escuro'}
  function initTheme(){setTheme(localStorage.getItem('pu2pny-theme')||'dark');var b=q('themeToggle');if(b)b.onclick=function(){setTheme(document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark'}}
  function flagUrl(code){var cc=String(code||'').toLowerCase();return /^[a-z]{2}$/.test(cc)?'/flags/4x3/'+cc+'.svg':''}
  function fmtTime(v){if(!v)return'—';try{return new Date(v).toLocaleString()}catch(e){return String(v)}}
  function nav(active){var items=[['/dashboard','Ao Vivo','live'],['/internet','Internet','internet'],['/protocols','Protocolos','protocols'],['/history','Mais usado','history'],['/aprs','APRS','aprs'],['/system','Sistema','system'],['/expert','Expert','expert']];var n=q('mainNav');if(!n)return;n.innerHTML=items.map(function(x){return '<a '+(x[2]===active?'class="active" ':'')+'href="'+x[0]+'">'+x[1]+'</a>'}).join('')}
  async function clock(){var l=q('clockLocal'),u=q('clockUTC');if(!l&&!u)return;var d=new Date();if(l)l.textContent=d.toLocaleTimeString();if(u)u.textContent=d.toISOString().slice(11,19)+' UTC'}
  function startClock(){clock();setInterval(clock,1000)}
  window.PNY={q:q,esc:esc,getj:getj,setTheme:setTheme,initTheme:initTheme,flagUrl:flagUrl,fmtTime:fmtTime,nav:nav,startClock:startClock};
})();