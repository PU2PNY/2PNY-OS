#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.resolve(__dirname,'..');
const langPath=path.join(root,'src/ui-language-0.3.27.js');
let source=fs.readFileSync(langPath,'utf8');
if(!source.includes('const D={'))throw new Error('i18n catalog D not found');
source=source.replace('const D={','const D=window.__PNY_D={');

function load(language){
  const storage=new Map([['pu2pny-language',language]]);
  const document={body:{},documentElement:{lang:'',classList:{remove(){},add(){}}},
    getElementById(){return null},querySelectorAll(){return []},
    createTreeWalker(){return {nextNode(){return null}}},addEventListener(){}};
  const context={window:{},document,NodeFilter:{SHOW_TEXT:4},Node:{TEXT_NODE:3},
    MutationObserver:class{constructor(cb){this.cb=cb}observe(){}},
    localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,String(v))},
    fetch:()=>Promise.reject(new Error('offline-i18n-gate')),queueMicrotask:()=>{},
    console,setTimeout,clearTimeout,URLSearchParams};
  context.window.document=document;context.window.localStorage=context.localStorage;
  vm.createContext(context);vm.runInContext(source,context,{filename:path.basename(langPath)});
  if(!context.window.__PNY_D||typeof context.window.PNYT!=='function')throw new Error('i18n exports unavailable');
  return {D:context.window.__PNY_D,t:context.window.PNYT};
}
const en=load('en'),es=load('es');
const D=en.D;
const errors=[];
const enPtLeak=/[ãõç]|(?:não|senha|salvar|atualizar|reiniciar|desligar|horário|relógio|rede|conexão|configuração|mensagem|ajuda|voltar|falha|aguardando|atualização|potência|chamada|recebida|restaurado|região)/i;
const esPtLeak=/[ãõç]|(?:não|senha|salvar|atualizar|reiniciar|desligar|horário|relógio|rede|conexão|configuração|mensagem|ajuda|voltar|falha|aguardando|atualização|potência|chamada|recebida|restaurado)/i;

for(const [pt,pair] of Object.entries(D)){
  if(!Array.isArray(pair)||pair.length!==2||!String(pair[0]||'').trim()||!String(pair[1]||'').trim()){
    errors.push(`catalog incomplete: ${pt}`);continue;
  }
  const a=en.t(pt),b=es.t(pt);
  if(a!==pair[0])errors.push(`EN lookup mismatch: ${pt}`);
  if(b!==pair[1])errors.push(`ES lookup mismatch: ${pt}`);
  if(enPtLeak.test(String(pair[0])))errors.push(`Portuguese leak in EN: ${pt} => ${pair[0]}`);
  if(esPtLeak.test(String(pair[1])))errors.push(`Portuguese leak in ES: ${pt} => ${pair[1]}`);
}
if(Object.keys(D).length<100)errors.push(`catalog unexpectedly small: ${Object.keys(D).length}`);

// Select the newest semantic-versioned HTML for each page family so historical
// files do not create false failures while the installed/current source is gated.
function versionOf(name){const m=name.match(/-0\.(\d+)\.(\d+)(?:\.(\d+))?\.html$/);return m?[+m[1],+m[2],+(m[3]||0)]:null;}
function cmp(a,b){for(let i=0;i<3;i++){if(a[i]!==b[i])return a[i]-b[i]}return 0;}
const srcDir=path.join(root,'src');const newest=new Map();
for(const file of fs.readdirSync(srcDir).filter(x=>x.endsWith('.html'))){
  const v=versionOf(file);if(!v)continue;const family=file.replace(/-0\.\d+\.\d+(?:\.\d+)?\.html$/,'.html');
  const prev=newest.get(family);if(!prev||cmp(v,prev.v)>0)newest.set(family,{file,v});
}
const tagRe=/<(h1|h2|h3|button|label|option|summary|small|span|p)(?:\s[^>]*)?>([\s\S]*?)<\/\1>/gi;
const portugueseVisible=/[ãõç]|(?:não|senha|salvar|atualizar|reiniciar|desligar|horário|relógio|rede|conexão|configuração|mensagem|ajuda|voltar|falha|aguardando|atualização|potência|chamada|recebida|servidor|fuso)/i;
let covered=0;
for(const {file} of newest.values()){
  let html=fs.readFileSync(path.join(srcDir,file),'utf8').replace(/<script[\s\S]*?<\/script>/gi,'').replace(/<style[\s\S]*?<\/style>/gi,'');
  let m;while((m=tagRe.exec(html))){
    const text=m[2].replace(/<[^>]+>/g,' ').replace(/&nbsp;|&#160;/g,' ').replace(/&[a-z]+;/gi,' ').replace(/\s+/g,' ').trim();
    if(!text||!portugueseVisible.test(text))continue;
    covered++;
    if(!Object.prototype.hasOwnProperty.call(D,text))errors.push(`${file}: visible PT text has no exact EN/ES catalog entry: ${text}`);
  }
}
if(covered<20)errors.push(`page i18n inventory unexpectedly small: ${covered}`);
if(errors.length){console.error(errors.join('\n'));process.exit(1);}
console.log(`I18N_PT_EN_ES_OK catalog=${Object.keys(D).length} visible=${covered} pages=${newest.size}`);
