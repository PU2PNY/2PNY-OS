// CLOCK-056: on opening System, align zone and (if NTP is not synchronized) time with the browser.
// A manual zone choice is respected by the server. Silent on success; errors go to the page message.
(function(){
  async function auto506(){
    try{
      var zone='';try{zone=Intl.DateTimeFormat().resolvedOptions().timeZone||''}catch(_){}
      if(!zone)return;
      var s=await PNY.getj('/api/system',null,8000),cs=s.clock_settings||{};
      if(cs.timezone_source==='manual')return;
      var drift=Math.abs(Date.parse(s.utc||'')-Date.now());
      var needTz=zone!==s.timezone,needTime=s.ntp_synchronized!==true&&Number.isFinite(drift)&&drift>120000;
      if(!needTz&&!needTime)return;
      var r=await PNY.getj('/api/clock/browser',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({timezone:zone,epoch_ms:Date.now()}),pnySilent:true},30000);
      var m=PNY.q('timeResult');
      if(m&&r&&r.ok&&!r.skipped)m.textContent='Fuso e hora ajustados automaticamente pelo navegador: '+zone+'.';
      if(typeof load==='function')await load();
    }catch(e){var m2=PNY.q('timeResult');if(m2)m2.textContent='Ajuste automático do relógio falhou: '+(e&&e.message||e)}
  }
  setTimeout(auto506,1200);
})();
