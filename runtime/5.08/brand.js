/* PU2PNY-OS 5.08 (UI-058): favicon, touch icon and header logo on every page; falls back to the text brand. */
;(function(){try{
  var d=document,h=d.head||d.documentElement;
  [['icon','/brand/favicon.png','image/png','32x32'],['icon','/brand/favicon-192.png','image/png','192x192'],['apple-touch-icon','/brand/apple-touch-icon.png','','180x180']].forEach(function(x){
    var l=d.createElement('link');l.rel=x[0];l.href=x[1];if(x[2])l.type=x[2];l.sizes=x[3];h.appendChild(l)});
  function logo(){
    var targets=[[d.querySelector('.topnav .brand'),26],[d.querySelector('.brand strong'),34]];
    targets.forEach(function(t){
      var el=t[0];if(!el||el.querySelector('img.pny-logo'))return;
      var text=el.textContent,small=el.querySelector('small'),img=new Image();
      img.className='pny-logo';img.alt='PU2PNY-OS';img.src='/brand/logo.png';
      img.style.cssText='height:'+t[1]+'px;width:auto;display:block';
      img.onload=function(){el.textContent='';el.appendChild(img);if(small)el.appendChild(small)};
      img.onerror=function(){};
    });
  }
  if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',logo);else logo();
}catch(e){}})();
