(function(){
 var $=function(i){return document.getElementById(i)};
 if(!$('idSave'))return;
 function say(t,c){$('idResult').textContent=t;$('idResult').className='statusmsg '+(c||'')}
 fetch('/api/config',{cache:'no-store'}).then(function(r){return r.json()}).then(function(c){
  if(c&&c.callsign){$('idCall').value=c.callsign}if(c&&c.dmr_id){$('idDmr').value=c.dmr_id}
 }).catch(function(){});
 async function waitDone(){
  for(var i=0;i<80;i++){
   await new Promise(function(r){setTimeout(r,2000)});
   try{var s=await (await fetch('/api/rf',{cache:'no-store'})).json();
    if(s.state==='applied')return {ok:true,message:s.message};
    if(s.state==='error')return {ok:false,message:s.message};}catch(e){}
  }
  return {ok:false,message:'Tempo esgotado. Confira o estado no painel principal.'};
 }
 $('idSave').onclick=async function(){
  var call=$('idCall').value.trim().toUpperCase(),id=$('idDmr').value.trim();
  if(!/^[A-Z0-9\/-]{3,16}$/.test(call)){say('Indicativo inválido: use 3 a 16 letras, números, / ou -.','statusbad');return}
  if(!/^[0-9]{6,9}$/.test(id)){say('DMR ID inválido: use 6 a 9 dígitos.','statusbad');return}
  $('idSave').disabled=true;say('Aplicando... não desligue o hotspot.','');
  try{
   var r=await fetch('/api/identity/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({callsign:call,dmr_id:id})});
   var j=await r.json().catch(function(){return {}});
   if(!r.ok||!j.ok){say(j.error||('Falha ('+r.status+')'),'statusbad');return}
   var d=await waitDone();say(d.message||(d.ok?'Aplicado.':'Falhou.'),d.ok?'statusok':'statusbad');
  }catch(e){say(e.message,'statusbad')}finally{$('idSave').disabled=false}
 };
})();
