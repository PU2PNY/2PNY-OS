#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.resolve(__dirname,'..');
const langSource=fs.readFileSync(path.join(root,'src/ui-language-0.3.24.js'),'utf8');
const common=fs.readFileSync(path.join(root,'src/ui-common-0.3.24.js'),'utf8');
if(!langSource.includes('STRICT_I18N_FALLBACK=true'))throw new Error('strict i18n gate missing');
if(!langSource.includes('window.PNYSetLanguage=setLanguage'))throw new Error('server/local language synchronization missing');
if(!common.includes("cs.timezone_source!=='manual'"))throw new Error('manual timezone priority missing');

function translator(language){
 const storage=new Map([['pu2pny-language',language]]);
 const document={
   body:{},
   documentElement:{lang:'',classList:{remove(){}}},
   getElementById(){return null},
   querySelectorAll(){return []},
   createTreeWalker(){return {nextNode(){return null}}}
 };
 const context={
   window:{},document,NodeFilter:{SHOW_TEXT:4},
   MutationObserver:class{constructor(cb){this.cb=cb}observe(){}},
   localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,String(v))},
   fetch:()=>Promise.reject(new Error('offline-test')),
   queueMicrotask:()=>{},console,setTimeout,clearTimeout
 };
 vm.createContext(context);
 vm.runInContext(langSource,context,{filename:'ui-language-0.3.24.js'});
 if(typeof context.window.PNYT!=='function')throw new Error('PNYT not exported');
 return context.window.PNYT;
}
const en=translator('en'),es=translator('es');
const ptLeak=/[ãõç]|(?:não|sim|aplicar|salvar|fuso|horário|relógio|rede|servidor|indicativo|cidade|país|estado|erro|falha|aguardando|conectando|desconectado|atualizar|configuração|senha|mensagem|ajuda|voltar|continuar|reiniciar|desligar|ligado|idioma|histórico|protocolo|frequência|potência|sinal|chamada|recebida|aceitação|rádio|anterior|restaurado|manual|automática|região)/i;
const genericEN='System message.',genericES='Mensaje del sistema.';
const tagRe=/<(h1|h2|h3|button|label|option|summary|small|span)(?:\s[^>]*)?>([\s\S]*?)<\/\1>/gi;
const files=fs.readdirSync(path.join(root,'src')).filter(f=>f.endsWith('.html'));
let checked=0;const failures=[];
for(const file of files){
 const html=fs.readFileSync(path.join(root,'src',file),'utf8').replace(/<script[\s\S]*?<\/script>/gi,'').replace(/<style[\s\S]*?<\/style>/gi,'');
 let m;
 while((m=tagRe.exec(html))){
   const text=m[2].replace(/<[^>]+>/g,' ').replace(/&nbsp;/g,' ').replace(/\s+/g,' ').trim();
   if(!text||!ptLeak.test(text))continue;
   checked++;
   const a=en(text),b=es(text);
   if(ptLeak.test(a)||ptLeak.test(b))failures.push(file+': mixed-language leak: '+text+' => '+a+' / '+b);
   if((a===genericEN||b===genericES)&&text.length<100)failures.push(file+': actionable text lacks full translation: '+text);
 }
}
for(const sample of [
 'Detectar região e sincronizar',
 'Aplicar fuso manual',
 'Aplicar data/hora manual',
 'Chamada recebida',
 'Aguardando aceitação pelo rádio',
 'Depois do QSO, o gateway anterior é restaurado automaticamente.'
]){
 const a=en(sample),b=es(sample);
 if(ptLeak.test(a)||ptLeak.test(b)||a===sample||b===sample)throw new Error('required translation failed: '+sample+' => '+a+' / '+b);
}
if(checked<20)failures.push('i18n inventory unexpectedly small: '+checked);
if(failures.length){console.error(failures.join('\n'));process.exit(1)}
console.log('I18N_0324_OK actionable='+checked);
