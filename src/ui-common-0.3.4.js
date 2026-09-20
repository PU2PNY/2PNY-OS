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
  function showAPRSToast(m){
    var old=q('pnyAprsToast');if(old)old.remove();
    var a=document.createElement('a');a.id='pnyAprsToast';a.href='/aprs';
    a.style.cssText='position:fixed;right:18px;top:84px;z-index:3000;width:min(360px,calc(100vw - 36px));display:block;text-decoration:none;border:1px solid var(--green);background:var(--card);color:var(--text);border-radius:14px;padding:13px 15px;box-shadow:var(--shadow)';
    a.innerHTML='<b style="display:block;margin-bottom:4px">Nova mensagem APRS · '+esc(m.station||'—')+'</b><span style="display:block;color:var(--muted)">'+esc(m.text||'Nova mensagem')+'</span><small style="display:block;margin-top:6px;color:var(--blue)">Clique para abrir APRS e responder</small>';
    document.body.appendChild(a);
    setTimeout(function(){if(a&&a.parentNode)a.remove()},5000)
  }
  var aprsWatchStarted=false;
  function startAPRSWatch(){
    if(aprsWatchStarted)return;aprsWatchStarted=true;
    async function poll(){
      if(document.hidden)return;
      try{
        var d=await getj('/api/aprs',null,3500),st=d.status||{},rows=(st.messages||[]).filter(function(x){return x.direction==='in'}),m=rows.length?rows[rows.length-1]:null;
        if(!m)return;
        var sig=[m.timestamp||'',m.station||'',m.id||'',m.text||''].join('|'),old=localStorage.getItem('pu2pny-aprs-last-message');
        if(!old){localStorage.setItem('pu2pny-aprs-last-message',sig);return}
        if(sig!==old){localStorage.setItem('pu2pny-aprs-last-message',sig);showAPRSToast(m)}
      }catch(e){}
    }
    poll();setInterval(poll,5000)
  }
  function footer(){
    if(q('pnyFooter'))return;
    var f=document.createElement('footer');f.id='pnyFooter';
    f.style.cssText='margin:28px auto 12px;max-width:1400px;padding:12px 18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;text-align:center';
    f.textContent='PU2PNY-OS · versão…';document.body.appendChild(f);
    getj('/api/status').then(function(s){f.textContent='PU2PNY-OS · '+(s.version||'versão indisponível')}).catch(function(){f.textContent='PU2PNY-OS'});
  }
  function nav(active){var items=[['/dashboard','Ao Vivo','live'],['/internet','Internet','internet'],['/hotspot','Hotspot','hotspot'],['/protocols','Protocolos','protocols'],['/aprs','APRS / D-PRS','aprs'],['/history','Histórico','history'],['/display','Display','display'],['/system','Sistema','system']];var n=q('mainNav');if(!n)return;n.innerHTML=items.map(function(x){return '<a '+(x[2]===active?'class="active" ':'')+'href="'+x[0]+'">'+x[1]+'</a>'}).join('');ensureTools(active);startAPRSWatch()}
  async function clock(){var l=q('clockLocal'),u=q('clockUTC');if(!l&&!u)return;var d=new Date();if(l)l.textContent=d.toLocaleTimeString();if(u)u.textContent=d.toISOString().slice(11,19)+' UTC'}
  function startClock(){clock();setInterval(clock,1000)}
  window.PNY={q:q,esc:esc,getj:getj,setTheme:setTheme,initTheme:initTheme,flagUrl:flagUrl,fmtTime:fmtTime,nav:nav,startClock:startClock};
})();