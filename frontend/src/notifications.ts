const BASE_TITLE='Local Transcript AI';
let blinkTimer:number|undefined;
let stopTimer:number|undefined;
let stopListeners:(()=>void)|undefined;

function setFavicon(color:string,symbol:string){
 let link=document.querySelector<HTMLLinkElement>('link[data-process-favicon]');
 if(!link){link=document.createElement('link');link.rel='icon';link.dataset.processFavicon='true';document.head.appendChild(link)}
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="${color}"/><text x="32" y="43" text-anchor="middle" font-size="34" fill="white" font-family="Arial">${symbol}</text></svg>`;
 link.href=`data:image/svg+xml,${encodeURIComponent(svg)}`;
}

function stopBlink(){
 if(blinkTimer)window.clearInterval(blinkTimer);
 if(stopTimer)window.clearTimeout(stopTimer);
 blinkTimer=undefined;stopTimer=undefined;
 document.title=BASE_TITLE;
 setFavicon('#20251d','✓');
 stopListeners?.();stopListeners=undefined;
}

export function requestNotificationPermission(){
 if('Notification' in window&&Notification.permission==='default')Notification.requestPermission().catch(()=>{});
}

export function notifyProcessFinished(label:string,kind:'success'|'error'='success'){
 stopBlink();
 const isError=kind==='error';
 const color=isError?'#c65449':'#779653';
 const symbol=isError?'!':'✓';
 const prefix=isError?'Ошибка':'Готово';
 let bright=false;
 const paint=()=>{bright=!bright;document.title=bright?`● ${prefix}: ${label}`:`○ ${label} — ${BASE_TITLE}`;setFavicon(bright?color:'#20251d',bright?symbol:'•')};
 paint();blinkTimer=window.setInterval(paint,650);
 const onFocus=()=>stopBlink();
 const onVisibility=()=>{if(document.visibilityState==='visible')stopBlink()};
 window.addEventListener('focus',onFocus,{once:true});
 document.addEventListener('visibilitychange',onVisibility);
 stopListeners=()=>{window.removeEventListener('focus',onFocus);document.removeEventListener('visibilitychange',onVisibility)};
 // Если пользователь уже смотрит на вкладку, всё равно показываем несколько миганий.
 if(document.hasFocus())stopTimer=window.setTimeout(stopBlink,7000);
 else stopTimer=window.setTimeout(stopBlink,60000);
 if('Notification' in window&&Notification.permission==='granted'){
  const notification=new Notification(`${prefix} — Local Transcript AI`,{body:label,tag:'local-transcript-process',silent:true});
  notification.onclick=()=>{window.focus();stopBlink();notification.close()};
 }
}
