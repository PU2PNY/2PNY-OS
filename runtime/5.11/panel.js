(function(){'use strict';
const q=id=>document.getElementById(id);
async function request(url,data){const r=await fetch(url,data===undefined?{cache:'no-store'}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const out=await r.json();if(!r.ok||out.ok===false)throw Error(out.error||'Não foi possível aplicar a alteração.');return out;}
function message(id,text){const e=q(id);if(e)e.textContent=text;}
async function apply(mode,destination,code,create,nxdn){return request('/api/mode/settings',{mode:mode,destination:destination||'',code:code||'',create:!!create,nxdn_id:nxdn||''});}
if(q('cmMode511')){
 const select=q('cmMode511');async function destinations(){const mode=select.value;const dmr=mode==='ysf2dmr';q('cmNXDNLabel511').hidden=mode!=='ysf2nxdn';q('cmTG511').hidden=!dmr;q('cmDest511').hidden=dmr;if(dmr)return;const proto=mode.endsWith('ysf')?'YSF':mode.endsWith('p25')?'P25':'NXDN';try{const out=await request('/api/mode/destinations?protocol='+proto);q('cmDest511').replaceChildren();for(const row of out.destinations||[]){const o=document.createElement('option');o.value=row.id||row.designator;o.textContent=(row.id||row.designator)+' · '+row.name;q('cmDest511').append(o);}if(!q('cmDest511').options.length)message('cmStatus511','Nenhum destino disponível na lista local.');}catch(e){message('cmStatus511',e.message);}}
 select.onchange=destinations;destinations();
 q('cmStart511').onclick=async function(){this.disabled=true;message('cmStatus511','Aplicando e verificando o processo…');try{await apply(select.value,select.value==='ysf2dmr'?q('cmTG511').value:q('cmDest511').value,'',false,q('cmNXDN511').value);message('cmStatus511','Processo ativo. Conexão remota e áudio RF precisam de teste.');}catch(e){message('cmStatus511',e.message);}finally{this.disabled=false;}};
 q('cmOff511').onclick=async()=>{try{await apply('off');message('cmStatus511','Modo normal restaurado.');}catch(e){message('cmStatus511',e.message);}};
}
if(q('group511')){
 q('legacyOn511').onclick=async()=>{try{await apply('legacy-on');message('groupStatus511','Direct individual habilitado.');}catch(e){message('groupStatus511',e.message);}};
 q('legacyOff511').onclick=async()=>{try{await apply('legacy-off');message('groupStatus511','Direct individual desligado.');}catch(e){message('groupStatus511',e.message);}};
 async function join(create){message('groupStatus511','Iniciando Direct em grupo…');try{const out=await apply('direct-group','',q('groupCode511').value,create);if(out.code)q('groupCode511').value=out.code;message('groupStatus511','Procurando participantes na DHT.');}catch(e){message('groupStatus511',e.message);}}
 q('groupCreate511').onclick=()=>join(true);q('groupJoin511').onclick=()=>join(false);
 q('groupCopy511').onclick=async()=>{try{await navigator.clipboard.writeText(q('groupCode511').value);message('groupStatus511','Código copiado.');}catch(e){q('groupCode511').type='text';q('groupCode511').select();message('groupStatus511','Selecione e copie o código.');}};
 q('groupOff511').onclick=async()=>{try{await apply('off');message('groupStatus511','DMR normal restaurado.');q('groupPeers511').replaceChildren();}catch(e){message('groupStatus511',e.message);}};
 async function status(){try{const out=await request('/api/mode/status');const list=q('groupPeers511');list.replaceChildren();if(out.mode&&out.mode.mode==='direct-group'){const state=out.direct||{};message('groupStatus511',(state.encryption||'Procurando participantes')+(state.encryption&&state.encryption.startsWith('HMAC')?' · áudio autenticado, sem cifra.':''));for(const p of state.peers||[]){const li=document.createElement('li');li.textContent=p.endpoint+' · '+p.state+' · '+p.via;list.append(li);}}}catch(e){}if(!document.hidden)setTimeout(status,10000);}
 status();document.addEventListener('visibilitychange',()=>{if(!document.hidden)status();});
}
if(q('voiceDMR511')){
 request('/api/voice/settings').then(v=>{for(const [id,key] of [['voiceDMR511','dmr'],['voiceDStar511','dstar'],['voiceP25511','p25'],['voiceNXDN511','nxdn']])q(id).checked=v[key]===undefined?(key==='dmr'?v.enabled!==false:key==='dstar'):v[key]!==false;q('voiceHourly').checked=!!v.hourly;q('voiceLang').value=v.language||'pt';}).catch(()=>{});
 q('voiceSave').onclick=async()=>{message('voiceResult','Aplicando voz…');try{await request('/api/voice/settings',{dmr:q('voiceDMR511').checked,dstar:q('voiceDStar511').checked,p25:q('voiceP25511').checked,nxdn:q('voiceNXDN511').checked,hourly:q('voiceHourly').checked,language:q('voiceLang').value});message('voiceResult','Voz aplicada aos perfis disponíveis.');}catch(e){message('voiceResult',e.message);}};
}
})();
