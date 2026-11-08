(function(){
 var $=function(i){return document.getElementById(i)};
 if(!$('consoleButtons'))return;
 var last='';
 function show(t){last=t;$('consoleOut').textContent=t;$('consoleCopy').disabled=$('consoleSave').disabled=!t}
 async function run(id,btn){
  var old=btn&&btn.textContent;if(btn){btn.disabled=true;btn.textContent='Rodando...'}
  show('Rodando '+id+'...');
  try{
   var r=await fetch('/api/expert/cmd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id})});
   var j=await r.json();show(j.ok?j.output:('Erro: '+(j.error||r.status)));
  }catch(e){show('Erro: '+e.message)}finally{if(btn){btn.disabled=false;btn.textContent=old}}
 }
 fetch('/api/expert/cmd',{cache:'no-store'}).then(function(r){return r.json()}).then(function(j){
  var box=$('consoleButtons');box.textContent='';
  (j.commands||[]).filter(function(c){return c.id!=='all'}).forEach(function(c){
   var b=document.createElement('button');b.className='btn';b.type='button';b.textContent=c.label;b.onclick=function(){run(c.id,b)};box.appendChild(b)});
 }).catch(function(){$('consoleButtons').textContent='Diagnóstico indisponível.'});
 $('consoleAll').onclick=function(){run('all',$('consoleAll'))};
 $('consoleCopy').onclick=async function(){try{await navigator.clipboard.writeText(last)}catch(e){var ta=document.createElement('textarea');ta.value=last;document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove()}this.textContent='Copiado';var b=this;setTimeout(function(){b.textContent='Copiar tudo'},1500)};
 $('consoleSave').onclick=function(){var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([last],{type:'text/plain'}));a.download='pu2pny-diagnostico.txt';a.click()};
})();
