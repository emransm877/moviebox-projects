/* Anonymous short-lived presence. No app telemetry or GitHub asset downloads. */
(() => {
  'use strict';
  const badge=document.getElementById('live-presence'),number=document.getElementById('presence-value');
  if(!badge||!number)return;
  const endpoint='https://moviebox-live-presence-emran.superannotat-0952.chatgpt.site',storageKey='moviebox.presence.v1',validId=/^[a-f0-9]{32}$/;
  let memory=null,timer=null,busy=false,stopped=false;
  const state=(kind,text)=>{badge.dataset.state=kind;badge.title=text;badge.setAttribute('aria-label',text);};
  if(location.hostname!=='emransm877.github.io'||navigator.webdriver||new URLSearchParams(location.search).get('presence')==='off'){
    state('off','Live presence is excluded for this preview or automated check.');return;
  }
  function read(){try{return JSON.parse(localStorage.getItem(storageKey))||memory;}catch{return memory;}}
  function save(value){memory=value;try{localStorage.setItem(storageKey,JSON.stringify(value));}catch{}}
  function randomId(){const bytes=new Uint8Array(16);crypto.getRandomValues(bytes);return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');}
  async function post(path,body){
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),8000);
    try{const response=await fetch(endpoint+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),credentials:'omit',cache:'no-store',referrerPolicy:'no-referrer',signal:controller.signal});if(!response.ok){const error=new Error('Presence unavailable');error.status=response.status;throw error;}return await response.json();}finally{clearTimeout(timeout);}
  }
  async function session(){
    const renew=async()=>{
      const now=Date.now();let value=read();
      if(!value||!validId.test(value.id)||!Number.isFinite(value.lastSeen)||now-value.lastSeen>30*60_000)value={id:randomId(),lastSeen:now};
      if(typeof value.token!=='string'||!Number.isFinite(value.expiresAt)||value.expiresAt<now+60_000){const issued=await post('/api/session',{id:value.id});if(typeof issued.token!=='string'||!Number.isFinite(issued.expiresAt))throw new Error('Invalid presence session');value={...value,token:issued.token,expiresAt:issued.expiresAt};}
      value.lastSeen=now;save(value);return value;
    };
    return navigator.locks? navigator.locks.request(storageKey,renew):renew();
  }
  async function tick(){
    clearTimeout(timer);if(stopped||busy)return;
    if(document.hidden){number.textContent='—';state('paused','Live presence pauses while this page is in the background.');return;}
    if(!navigator.onLine){number.textContent='—';state('offline','Live count unavailable while offline.');return;}
    busy=true;
    try{
      let current=await session(),result;
      try{result=await post('/api/presence',{token:current.token});}catch(error){if(error.status!==401)throw error;save({...current,token:null,expiresAt:0});current=await session();result=await post('/api/presence',{token:current.token});}
      if(!Number.isSafeInteger(result.count)||result.count<0||result.windowSeconds!==90)throw new Error('Invalid presence count');
      if(!document.hidden&&!stopped){number.textContent=result.count.toLocaleString();state('live',result.count+' active browser'+(result.count===1?'':'s')+' in the last 90 seconds. Shared across open tabs; not an exact people count.');}
    }catch{number.textContent='—';state('unavailable','Live visitor count is temporarily unavailable.');}
    finally{busy=false;if(!stopped&&!document.hidden)timer=setTimeout(tick,25_000);}
  }
  document.addEventListener('visibilitychange',()=>{clearTimeout(timer);tick();});
  window.addEventListener('offline',()=>{clearTimeout(timer);number.textContent='—';state('offline','Live count unavailable while offline.');});
  window.addEventListener('online',tick);
  window.addEventListener('pagehide',()=>{stopped=true;clearTimeout(timer);});
  window.addEventListener('pageshow',()=>{stopped=false;tick();});
  tick();
})();
