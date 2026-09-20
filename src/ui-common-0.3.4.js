(function(){
  function q(id){return document.getElementById(id)}
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  async function getj(url,opt,timeout){var ctl=window.AbortController?new AbortController():null,timer=null,o=Object.assign({cache:'no-store'},opt||{});if(ctl){o.signal=ctl.signal;timer=setTimeout(function(){ctl.abort()},timeout||8000)}try{var r=await fetch(url,o),j=await r.json().catch(function(){return {}});if(!r.ok)throw new Error(j.error||j.message||('HTTP '+r.status));return j}finally{if(timer)clearTimeout(timer)}}
  function setTheme(t){document.documentElement.setAttribute('data-theme',t);localStorage.setItem('pu2pny-theme',t);var b=q('themeToggle');if(b)b.textContent=t==='dark'?'☀ Claro':'☾ Escuro'}
  function initTheme(){setTheme(localStorage.getItem('pu2pny-theme')||'dark');var b=q('themeToggle');if(b)b.onclick=function(){setTheme(document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark')}}
  function flagUrl(code){var cc=String(code||'').toLowerCase();return /^[a-z]{2}$/.test(cc)?'/flags/4x3/'+cc+'.svg':''}
  function fmtTime(v){if(!v)return'—';try{return new Date(v).toLocaleString()}catch(e){return String(v)}}
  function ensureTools(active){
    var tools=document.querySelector('.navtools');if(!tools)return;
    if(!q('language')){
      var s=document.createElement('select');s.id='language';s.setAttribute('aria-label','Idioma');
      s.innerHTML='<option value="pt">PT</option><option value="en">EN</option><option value="es">ES</option>';
      tools.insertBefore(s,tools.firstChild)
    }
    if(!q('modeToggle')){
      var b=document.createElement('button');b.className='btn';b.id='modeToggle';tools.appendChild(b)
    }
    q('modeToggle').textContent=active==='expert'?'Básico':'Expert';
    q('modeToggle').onclick=function(){location.href=active==='expert'?'/dashboard':'/expert'};
    footer();
    if(!document.querySelector('script[data-pny-language]')){
      var sc=document.createElement('script');sc.src='/ui-language.js';sc.dataset.pnyLanguage='1';document.body.appendChild(sc)
    }else if(window.translateNavigation){window.translateNavigation()}
  }
  function footer(){
    if(q('pnyFooter'))return;
    var f=document.createElement('footer');f.id='pnyFooter';
    f.style.cssText='margin:28px auto 12px;max-width:1400px;padding:12px 18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;text-align:center';
    f.textContent='PU2PNY-OS · versão…';document.body.appendChild(f);
    getj('/api/status').then(function(s){f.textContent='PU2PNY-OS · '+(s.version||'versão indisponível')}).catch(function(){f.textContent='PU2PNY-OS'});
  }
  function nav(active){var items=[['/dashboard','Ao Vivo','live'],['/internet','Internet','internet'],['/hotspot','Hotspot','hotspot'],['/protocols','Protocolos','protocols'],['/aprs','APRS / D-PRS','aprs'],['/history','Histórico','history'],['/display','Display','display'],['/system','Sistema','system']];var n=q('mainNav');if(!n)return;n.innerHTML=items.map(function(x){return '<a '+(x[2]===active?'class="active" ':'')+'href="'+x[0]+'">'+x[1]+'</a>'}).join('');ensureTools(active)}
  async function clock(){var l=q('clockLocal'),u=q('clockUTC');if(!l&&!u)return;var d=new Date();if(l)l.textContent=d.toLocaleTimeString();if(u)u.textContent=d.toISOString().slice(11,19)+' UTC'}
  function startClock(){clock();setInterval(clock,1000)}
  window.PNY={q:q,esc:esc,getj:getj,setTheme:setTheme,initTheme:initTheme,flagUrl:flagUrl,fmtTime:fmtTime,nav:nav,startClock:startClock};
})();