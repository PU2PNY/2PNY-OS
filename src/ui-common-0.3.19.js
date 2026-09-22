(function(){
  document.title='PU2PNY-OS';
  function q(id){return document.getElementById(id)}
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  async function getj(url,opt,timeout){var ctl=window.AbortController?new AbortController():null,timer=null,o=Object.assign({cache:'no-store'},opt||{}),method=String(o.method||'GET').toUpperCase(),auto=null;if(method!=='GET'&&!o.pnySilent&&!q('pnyOperationOverlay'))auto=operation('Aplicando alteração','Enviando, validando e aguardando confirmação do sistema...');delete o.pnySilent;if(ctl){o.signal=ctl.signal;timer=setTimeout(function(){ctl.abort()},timeout||8000)}try{var r=await fetch(url,o),j=await r.json().catch(function(){return {}});if(!r.ok){var m=j.error||j.message||('HTTP '+r.status);if(/signal is aborted|AbortError|aborted without reason/i.test(m))m='A operação foi interrompida antes da confirmação. O estado anterior foi preservado; tente novamente.';throw new Error(m)}if(auto)auto.done(j.message||'Alteração aplicada.');return j}catch(e){var m=String(e&&e.message||e||'');if(/signal is aborted|AbortError|aborted without reason/i.test(m))e=new Error('A operação foi interrompida antes da confirmação. O estado anterior foi preservado; tente novamente.');if(auto)auto.error(e.message);throw e}finally{if(timer)clearTimeout(timer)}}
  function setTheme(t){document.documentElement.setAttribute('data-theme',t);localStorage.setItem('pu2pny-theme',t);var b=q('themeToggle');if(b)b.textContent=t==='dark'?'☀ Claro':'☾ Escuro'}
  function initTheme(){setTheme(localStorage.getItem('pu2pny-theme')||'dark');var b=q('themeToggle');if(b)b.onclick=function(){setTheme(document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark')}}
  function flagUrl(code){var cc=String(code||'').toLowerCase();return /^[a-z]{2}$/.test(cc)?'/flags/4x3/'+cc+'.svg':''}
  function fmtTime(v){if(!v)return'—';try{return new Date(v).toLocaleString()}catch(e){return String(v)}}
  function ensureGlobalCSS(){
    if(q('pnyGlobalPatch'))return;
    var st=document.createElement('style');st.id='pnyGlobalPatch';
    st.textContent='.topnav{min-height:52px;height:auto;padding-top:7px;padding-bottom:7px}.topnav .nav{min-width:0;overflow-x:auto;flex-wrap:nowrap;scrollbar-width:thin}.topnav .nav a{white-space:nowrap;flex:0 0 auto;padding:7px 9px;font-size:13px}.navtools{flex:0 0 auto;white-space:nowrap}.navtools .pill,#clockLocal{white-space:nowrap;min-width:88px;text-align:center;display:inline-block}.pny-health{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:10px 0 4px}.pny-healthitem{padding:9px 10px;border:1px solid var(--line);border-radius:10px;background:var(--card2);min-width:0}.pny-healthitem .big{font-size:18px}.pny-meter{height:7px;border-radius:999px;background:var(--line);overflow:hidden;margin-top:6px}.pny-meter i{display:block;height:100%;background:var(--blue);width:0}.pny-profiledetails{margin-top:7px}.pny-profiledetails summary{cursor:pointer;color:var(--muted);font-size:12px;font-weight:850}.pny-profilebar{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0 0}.pny-profilebar .btn{padding:6px 9px;font-size:12px}.pny-profilebar button.active{outline:2px solid var(--green)}@media(max-width:760px){.pny-health{grid-template-columns:1fr 1fr}.topnav{align-items:flex-start}.navtools{margin-left:auto}}@media(max-width:480px){.pny-health{grid-template-columns:1fr}}';
    document.head.appendChild(st);
  }
  function ensureTools(active){
    ensureGlobalCSS();
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
    var a=document.createElement('a');a.id='pnyAprsToast';a.href='/aprs?to='+encodeURIComponent(m.station||'');
    a.style.cssText='position:fixed;right:18px;top:84px;z-index:3000;width:min(360px,calc(100vw - 36px));display:block;text-decoration:none;border:1px solid var(--green);background:var(--card);color:var(--text);border-radius:14px;padding:13px 15px;box-shadow:var(--shadow)';
    a.innerHTML='<b style="display:block;margin-bottom:4px">Nova mensagem APRS · '+esc(m.station||'—')+'</b><span style="display:block;color:var(--muted)">'+esc(m.text||'Nova mensagem')+'</span><small style="display:block;margin-top:6px;color:var(--blue)">Clique para abrir APRS e responder</small>';
    document.body.appendChild(a);
    setTimeout(function(){if(a&&a.parentNode)a.remove()},5000)
  }
  var aprsWatchStarted=false;
  function startAPRSWatch(){
    if(location.pathname==='/aprs'||aprsWatchStarted)return;aprsWatchStarted=true;
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

  function operation(title,message){
    var old=q('pnyOperationOverlay');if(old)old.remove();
    var ov=document.createElement('div');ov.id='pnyOperationOverlay';
    ov.style.cssText='position:fixed;inset:0;z-index:5000;background:rgba(0,0,0,.64);display:grid;place-items:center;padding:18px';
    var box=document.createElement('div');box.style.cssText='width:min(560px,100%);background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:var(--shadow)';
    box.innerHTML='<h2 id="pnyOpTitle" style="margin-top:0">'+esc(title||'Executando')+'</h2><div style="height:6px;background:var(--card2);border-radius:999px;overflow:hidden"><i id="pnyOpPulse" style="display:block;width:35%;height:100%;background:var(--blue);animation:pnyop 1.2s ease-in-out infinite alternate"></i></div><p id="pnyOpMessage" style="margin-bottom:0">'+esc(message||'Aguarde…')+'</p><button class="btn hidden" id="pnyOpClose" style="margin-top:14px">Fechar</button>';
    var style=document.createElement('style');style.textContent='@keyframes pnyop{from{transform:translateX(-80%)}to{transform:translateX(220%)}}';ov.appendChild(style);ov.appendChild(box);document.body.appendChild(ov);
    function set(state,msg){
      var m=q('pnyOpMessage'),pulse=q('pnyOpPulse'),close=q('pnyOpClose');if(m)m.textContent=msg||'';
      if(state==='done'||state==='error'){if(pulse){pulse.style.animation='none';pulse.style.width='100%';pulse.style.transform='none';pulse.style.background=state==='done'?'var(--green)':'var(--red)'}if(close){close.classList.remove('hidden');close.onclick=function(){ov.remove()}}}
    }
    return {step:function(msg){set('running',msg)},progress:function(percent,msg){var p=Number(percent);if(!Number.isFinite(p))return set('running',msg);p=Math.max(0,Math.min(100,p));var pulse=q('pnyOpPulse');if(pulse){pulse.style.animation='none';pulse.style.transform='none';pulse.style.width=p+'%';pulse.style.background='var(--blue)'}set('running',(msg||'Executando…')+' · '+Math.round(p)+'%')},done:function(msg,delay){set('done',msg||'Concluído.');setTimeout(function(){if(ov.parentNode)ov.remove()},delay==null?1200:delay)},error:function(msg){set('error',msg||'Não foi possível concluir.')},close:function(){if(ov.parentNode)ov.remove()}};
  }
  function footer(){
    if(q('pnyFooter'))return;
    var f=document.createElement('footer');f.id='pnyFooter';
    f.style.cssText='margin:28px auto 12px;max-width:1400px;padding:12px 18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;text-align:center';
    f.textContent='PU2PNY-OS · versão…';document.body.appendChild(f);
    getj('/api/status').then(function(s){f.textContent='PU2PNY-OS · '+(s.version||'versão indisponível')}).catch(function(){f.textContent='PU2PNY-OS'});
  }
  function nav(active){var items=[['/dashboard','Ao Vivo','live'],['/internet','Internet','internet'],['/hotspot','Protocolos','hotspot'],['/direct','Direct','direct'],['/aprs','APRS / D-PRS','aprs'],['/history','Histórico','history'],['/display','Display','display'],['/system','Sistema','system']];var n=q('mainNav');if(n)n.innerHTML=items.map(function(x){return '<a '+(x[2]===active?'class="active" ':'')+'href="'+x[0]+'">'+x[1]+'</a>'}).join('');ensureTools(active);startClock();startAPRSWatch();setTimeout(enhanceCurrentPage,0)}
  var clockStarted=false,clockServerUTC=0,clockSyncAt=0,clockTZ='';
  function renderClock(){
    var l=q('clockLocal'),u=q('clockUTC');if(!l&&!u)return;
    var ms=clockServerUTC?clockServerUTC+(Date.now()-clockSyncAt):Date.now(),d=new Date(ms);
    if(l){try{l.textContent=new Intl.DateTimeFormat('pt-BR',{timeZone:clockTZ||undefined,hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(d)}catch(e){l.textContent=d.toLocaleTimeString()}}
    if(u)u.textContent=d.toISOString().slice(11,19)+' UTC'
  }
  async function syncClock(){
    try{var s=await getj('/api/system',null,4500),utc=Date.parse(s.utc||'');if(Number.isFinite(utc)){clockServerUTC=utc;clockSyncAt=Date.now()}clockTZ=s.timezone||clockTZ}catch(e){}
    renderClock()
  }
  function startClock(){if(clockStarted)return;clockStarted=true;syncClock();setInterval(renderClock,1000);setInterval(function(){if(!document.hidden)syncClock()},60000);document.addEventListener('visibilitychange',function(){if(!document.hidden)syncClock()})}

  function qualityClass(v){v=String(v||'').toLowerCase();return /ótim|great|excellent/.test(v)?'green':/bom|good/.test(v)?'blue':/ruim|poor|offline/.test(v)?'red':'yellow'}
  function rfPct(rssi){var n=Number(rssi);if(!Number.isFinite(n))return 0;return Math.max(0,Math.min(100,(n+125)*2))}
  function ensureHealth(){
    if(location.pathname!='/dashboard'||q('pnyHealth'))return;
    var live=q('liveBox');if(!live)return;
    var sec=document.createElement('div');sec.id='pnyHealth';
    sec.innerHTML='<div class="pny-health"><div class="pny-healthitem" id="pnyRFHealth"><small class="muted">Sinal RF</small><div class="big" id="pnyRFValue">—</div><div class="pny-meter"><i id="pnyRFBar"></i></div><small id="pnyRFMeta" class="muted">Aguardando RX do rádio</small></div><div class="pny-healthitem" id="pnyWiFiHealth" role="button" tabindex="0"><small class="muted">Wi-Fi / Uplink</small><div class="big" id="pnyWiFiValue">—</div><div class="pny-meter"><i id="pnyWiFiBar"></i></div><small id="pnyWiFiMeta" class="muted">—</small></div><div class="pny-healthitem" id="pnyNetHealth" role="button" tabindex="0"><small class="muted">Internet</small><div class="big" id="pnyNetValue">—</div><div class="pny-meter"><i id="pnyNetBar"></i></div><small id="pnyNetMeta" class="muted">—</small></div></div><details class="pny-profiledetails"><summary>Trocar perfil rapidamente</summary><div class="pny-profilebar" id="pnyProfiles"></div></details>';
    var status=live.querySelector('.statusbar');if(status)status.insertAdjacentElement('afterend',sec);else live.insertBefore(sec,live.firstChild);
    function goInternet(){location.href='/internet'}
    q('pnyWiFiHealth').onclick=goInternet;q('pnyNetHealth').onclick=goInternet;
    loadConnectivity();loadProfiles()
  }
  async function loadConnectivity(){
    if(!q('pnyWiFiValue'))return;
    try{
      var c=await getj('/api/connectivity',null,4000);
      if(c.default_interface&&/^e(n|th)/.test(c.default_interface)){q('pnyWiFiValue').textContent='Ethernet';q('pnyWiFiMeta').textContent='Link ativo';q('pnyWiFiBar').style.width='100%'}
      else{q('pnyWiFiValue').textContent=c.wifi_quality||'—';q('pnyWiFiMeta').textContent=(c.wifi_ssid||'Wi-Fi')+(c.wifi_signal?(' · '+c.wifi_signal+'%'):'');q('pnyWiFiBar').style.width=(c.wifi_signal||0)+'%'}
      q('pnyNetValue').textContent=c.internet?c.internet_quality:'Offline';q('pnyNetMeta').textContent=c.internet_latency_ms?c.internet_latency_ms+' ms':'sem resposta';q('pnyNetBar').style.width=c.internet?Math.max(12,100-Math.min(90,(c.internet_latency_ms||0)/3))+'%':'0%';
    }catch(e){}
  }
  function applyLiveHealth(d){
    if(!q('pnyRFValue'))return;var a=d&&d.active||{},dir=String(a.direction||'').toUpperCase(),rv=a.rssi_avg!=null?a.rssi_avg:a.rssi,ber=a.ber;
    if(dir==='RF'&&rv!=null){q('pnyRFValue').textContent=Math.round(Number(rv))+' dBm';q('pnyRFBar').style.width=rfPct(rv)+'%';q('pnyRFMeta').textContent=(ber!=null?'BER '+Number(ber).toFixed(1)+'% · ':'')+(a.protocol||'RF')}
    else{q('pnyRFValue').textContent=dir==='RF'?'RSSI —':'—';q('pnyRFBar').style.width='0%';q('pnyRFMeta').textContent=dir==='RF'?'RSSI indisponível':'Aguardando RX do rádio'}
  }
  var pnyLiveES=null;
  function startHealthStream(){
    if(location.pathname!='/dashboard'||pnyLiveES||!window.EventSource)return;
    try{pnyLiveES=new EventSource('/api/live/events');pnyLiveES.addEventListener('live',function(e){try{applyLiveHealth(JSON.parse(e.data))}catch(_){}});pnyLiveES.onerror=function(){}}catch(e){}
  }
  async function loadProfiles(){
    if(!q('pnyProfiles'))return;
    try{
      var d=await getj('/api/protocol/profiles'),profiles=d.profiles||{},cfg=await getj('/api/config').catch(function(){return{}}),active=String(cfg.protocol||'').toUpperCase();
      var ps=['DMR','DSTAR','YSF','P25','NXDN','POCSAG'];
      q('pnyProfiles').innerHTML=ps.map(function(p){var x=profiles[p]||{},ok=!!x.rx_hz,label=p==='DSTAR'?'D-Star':p==='YSF'?'YSF/C4FM':p;return '<button class="btn '+(p===active?'active':'')+'" data-p="'+p+'" data-ok="'+(ok?'1':'0')+'">'+label+(ok?'':' · configurar')+'</button>'}).join('');
      q('pnyProfiles').querySelectorAll('button').forEach(function(b){b.onclick=async function(){var p=b.dataset.p;if(b.dataset.ok!=='1'){location.href='/hotspot?protocol='+encodeURIComponent(p)+'#protocols';return}var op=operation('Ativando '+p,'Aplicando o perfil de forma transacional...');try{await getj('/api/protocol/profiles',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'activate',protocol:p})},70000);op.done('Perfil ativado.');setTimeout(loadProfiles,900)}catch(e){op.error(e.message)}}})
    }catch(e){}
  }
  function enhanceHotspot(){ return }
  function enhanceEmbedded(){
    if(window.self===window.top)return;var h=document.querySelector('.topnav,header');if(h)h.style.display='none';var f=q('pnyFooter');if(f)f.style.display='none';var m=document.querySelector('main');if(m){m.style.maxWidth='none';m.style.padding='10px'}
  }
  function enhanceCurrentPage(){ensureGlobalCSS();enhanceEmbedded();ensureHealth();enhanceHotspot();if(location.pathname==='/dashboard'){loadConnectivity();startHealthStream();setInterval(function(){if(!document.hidden)loadConnectivity()},15000)}}

  window.PNY={q:q,esc:esc,getj:getj,setTheme:setTheme,initTheme:initTheme,flagUrl:flagUrl,fmtTime:fmtTime,nav:nav,startClock:startClock,operation:operation};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',enhanceCurrentPage);else setTimeout(enhanceCurrentPage,0);
})();