const {chromium}=require('playwright');const fs=require('fs'),http=require('http'),assert=require('assert');
const root=process.cwd();
const person={callsign:'PU2PNY',id:'7241465',name:'Dario Nunes',city:'Santa Isabel',state:'SP',country:'Brasil'};
const call={active:true,source:'7241465',protocol:'DMR',direction:'RF',slot:2,target:'TG 6',timestamp:new Date().toISOString(),duration:35,operator:person,quality:{label:'Aguardando BER/RSSI',score:0}};
const responses={
 '/api/dashboard':{version:'0.2.7-alpha',radio_active:true,dmrgateway_active:true,display_active:true,mqtt_active:true,config:{callsign:'PU2PNY',protocol:'DMR',dmr_id:7241465,rx_hz:439125000,dmr_slot:'2'},connectivity:{internet:true,internet_quality:'Ótimo',ipv4:['192.168.100.22'],ethernet:true},telemetry:{cpu_percent:4,temperature:48,memory_used_mb:120,memory_total_mb:1024}},
 '/api/live':{network:{state:'connected'},rx:call,tx:{...call,direction:'NETWORK'},history:[call]},
 '/api/contacts':{contacts:[person]},'/api/config':{callsign:'PU2PNY',protocol:'DMR'},'/api/status':{},'/api/connectivity':{internet:true,ethernet:true},'/api/network/connect/status':{},'/api/hardware/status':{state:'complete'},'/api/servers':{servers:[{name:'XLX_026',kind:'XLX',address:'example.test',port:62030},{name:'BM_Test',kind:'BrandMeister',address:'example.test',port:62031}]}
};
const server=http.createServer((req,res)=>{let path=req.url.split('?')[0];res.setHeader('Content-Type',path.startsWith('/api/')?'application/json':path.endsWith('.js')?'application/javascript':'text/html');if(path.startsWith('/api/'))return res.end(JSON.stringify(responses[path]||{}));let file=path==='/wizard'?'wizard-0.2.7.html':path==='/ui-language.js'?'ui-language-0.2.7.js':'dashboard-0.2.7.html';res.end(fs.readFileSync(root+'/src/'+file))});
(async()=>{await new Promise(r=>server.listen(8766,'127.0.0.1',r));let browser=await chromium.launch({headless:true});let page=await browser.newPage();let errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 fs.mkdirSync('/tmp/pu2pny-ui',{recursive:true});
 for(let width of [1366,390]){
  await page.setViewportSize({width,height:900});await page.goto('http://127.0.0.1:8766/dashboard');await page.locator('#splash').waitFor({state:'hidden'});
  assert((await page.title()).includes('PU2PNY'));assert(await page.locator('#rxName').innerText()==='Dario Nunes');assert(await page.locator('#events tbody tr').count()===1);
  assert(await page.locator('#rxCard').evaluate(e=>getComputedStyle(e).borderTopColor)==='rgb(251, 66, 101)');assert(await page.locator('#txCard').evaluate(e=>getComputedStyle(e).borderTopColor)==='rgb(25, 201, 135)');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'horizontal page overflow '+width);
  await page.locator('#viewMode').click();assert(await page.locator('#sshKey').isVisible());await page.locator('#viewMode').click();assert(!(await page.locator('#sshKey').isVisible()));
  await page.locator('#language').selectOption('en');assert(await page.locator('.top h1').innerText()==='Dashboard');await page.locator('#language').selectOption('pt');
  await page.screenshot({path:'/tmp/pu2pny-ui/dashboard-'+width+'.png',fullPage:true});
 }
 await page.goto('http://127.0.0.1:8766/wizard?step=3');await page.locator('#networkFilters').getByText('BrandMeister',{exact:true}).click();assert(await page.locator('#serverSelect option').count()===2);assert((await page.locator('#serverSelect').innerText()).includes('BM_Test'));assert(!(await page.locator('#serverSelect').innerText()).includes('XLX_026'));
 await page.locator('#networkFilters').getByText('XLX',{exact:true}).click();assert((await page.locator('#serverSelect').innerText()).includes('XLX_026'));
 await page.screenshot({path:'/tmp/pu2pny-ui/wizard.png',fullPage:true});assert.deepStrictEqual(errors,[]);console.log('UI OK: desktop/mobile, live colors, identity/history, expert, language and filters; no JS errors');
}finally{await browser.close();server.close()}})().catch(e=>{console.error(e);server.close();process.exit(1)});
