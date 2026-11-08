(function(){
 var $=function(i){return document.getElementById(i)};
 if(!$('oledSave'))return;
 function say(t,c){$('oledMsg').textContent=t;$('oledMsg').className='statusmsg '+(c||'')}
 fetch('/api/oled/config',{cache:'no-store'}).then(function(r){return r.json()}).then(function(c){
  if(c&&c.type){$('oledType').value=c.type}
  if(c&&c.lcd_cols){$('oledSize').value=c.lcd_cols+'x'+c.lcd_rows}else if(c&&c.height){$('oledSize').value=String(c.height)}
 }).catch(function(){});
 $('oledSave').onclick=async function(){
  var type=$('oledType').value,size=$('oledSize').value,body={type:type};
  if(type==='lcd'){body.lcd=/x/.test(size)?size:'20x4'}else if(type==='ssd1306'||type==='sh1106'){body.height=/x/.test(size)?64:parseInt(size,10)}
  $('oledSave').disabled=true;say('Aplicando...','');
  try{
   var r=await fetch('/api/oled/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
   var j=await r.json().catch(function(){return {}});
   say(r.ok&&j.ok?'Aplicado. A tela reinicia em alguns segundos.':(j.error||('Falha ('+r.status+')')),r.ok&&j.ok?'statusok':'statusbad');
  }catch(e){say(e.message,'statusbad')}finally{$('oledSave').disabled=false}
 };
})();
