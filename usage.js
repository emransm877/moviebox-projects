/* Optional aggregate events. No analytics is sent until this browser opts in. */
(() => {
  'use strict';
  const base='/moviebox-projects/',service='https://moviebox-live-presence-emran.superannotat-0952.chatgpt.site';
  const preferenceKey='moviebox.usage-consent.v1',campaignKey='moviebox.campaign.v1';
  const route=location.pathname.replace(base,'').replace(/index\.html$/,'').replace(/\/$/,'')||'home';
  if(!['home','windows','android','samsung-tv','android-tv','help'].includes(route))return;
  const contentPattern=/^(?:|[rpc]\d{2}|release-moviebox-(?:desktop|android|tizen|android-tv)-\d{1,15})$/;
  const excluded=location.hostname!=='emransm877.github.io'||navigator.webdriver||new URLSearchParams(location.search).get('presence')==='off';
  const privacySignal=()=>navigator.globalPrivacyControl===true||navigator.doNotTrack==='1'||window.doNotTrack==='1';
  let consent=false,tokenPromise=null,viewsSent=false,eventsSent=0,attribution=null;
  try{consent=localStorage.getItem(preferenceKey)==='yes';}catch{}
  const active=()=>consent&&!excluded&&!privacySignal();
  function campaign(){
    const query=new URLSearchParams(location.search),source=query.get('utm_source');
    let saved=null;try{saved=JSON.parse(sessionStorage.getItem(campaignKey));}catch{}
    if(saved&&Date.now()-saved.at>30*60_000)saved=null;
    let value;
    if(source){const content=query.get('utm_content')||'';value={source:source.toLowerCase()==='facebook'?'facebook':'other',content:contentPattern.test(content)?content:'',at:Date.now()};}
    else if(saved&&['facebook','direct','other'].includes(saved.source)&&contentPattern.test(saved.content))value=saved;
    else{let referrer='';try{referrer=new URL(document.referrer).hostname;}catch{}value={source:/(^|\.)facebook\.com$/.test(referrer)?'facebook':referrer&&referrer!==location.hostname?'other':'direct',content:'',at:Date.now()};}
    try{sessionStorage.setItem(campaignKey,JSON.stringify(value));}catch{}
    return value;
  }
  async function token(){
    if(!tokenPromise)tokenPromise=(async()=>{
      const bytes=new Uint8Array(16);crypto.getRandomValues(bytes);const id=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
      const response=await fetch(service+'/api/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id}),credentials:'omit',referrerPolicy:'no-referrer',signal:AbortSignal.timeout(5000)});
      if(!response.ok)throw new Error('Unavailable');return (await response.json()).token;
    })();
    return tokenPromise;
  }
  async function send(event,platform='none'){
    if(!active()||eventsSent>=30)return;
    eventsSent++;attribution=attribution||campaign();
    try{
      const authorization=await token();if(!active())return;
      await fetch(service+'/api/usage',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:authorization,consent:true,route,source:attribution.source,content:attribution.content,event,platform}),credentials:'omit',referrerPolicy:'no-referrer',keepalive:true,signal:AbortSignal.timeout(5000)});
    }catch{/* Never delay a download or retry a possibly accepted event. */}
  }
  function view(){if(active()&&!viewsSent){viewsSent=true;send('page_view');}}
  const control=document.createElement('button');control.type='button';control.className='usage-control';control.textContent='Usage statistics';
  const dialog=document.createElement('dialog');dialog.className='usage-dialog';dialog.setAttribute('aria-labelledby','usage-title');
  dialog.innerHTML='<h2 id="usage-title">Optional usage statistics</h2><p>Help improve installation guides with anonymous page-view and download-click counts. This is off until you allow it.</p><p>Only the day, project page, broad source, public post code and platform are kept. No names, emails, IP addresses, full URLs or browser IDs are stored in these statistics. Counts are retained for up to 90 days and aggregate totals are publicly readable. Hosting providers process normal HTTP traffic.</p><p>These are event requests, not unique people, completed downloads or installs. Your choice is stored in this browser; campaign context is kept in this tab for up to 30 minutes. Global Privacy Control and Do Not Track override an allowance. The separate live presence counter is explained in Help.</p><p id="usage-choice" role="status"></p><div class="usage-actions"><button type="button" data-usage="allow">Allow anonymous counts</button><button type="button" data-usage="deny">Keep off</button><button type="button" data-usage="close">Close</button></div>';
  document.body.append(dialog);(document.querySelector('footer.footer')||document.body).append(control);
  function status(){dialog.querySelector('#usage-choice').textContent=privacySignal()?'Off — your browser sends a privacy signal.':consent?'Allowed in this browser.':'Off in this browser.';}
  control.addEventListener('click',()=>{status();dialog.showModal();});
  dialog.addEventListener('click',event=>{
    const action=event.target.closest('[data-usage]')?.dataset.usage;if(!action)return;
    if(action!=='close'){
      consent=action==='allow';try{localStorage.setItem(preferenceKey,consent?'yes':'no');}catch{}
      if(!consent){try{sessionStorage.removeItem(campaignKey);}catch{}attribution=null;tokenPromise=null;}
      status();view();
    }
    dialog.close();
  });
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[href]');if(!link||!event.isTrusted||event.button!==0)return;
    let url;try{url=new URL(link.href);}catch{return;}
    if(url.hostname!=='github.com'||url.protocol!=='https:')return;
    const match=url.pathname.match(/^\/emransm877\/moviebox-(desktop|android-tv|android|tizen)\/releases\/download\//);if(!match)return;
    const filename=url.pathname.split('/').at(-1);if(!/\.(?:exe|zip|apk|wgt)$/i.test(filename)||/sha256|checksum/i.test(filename))return;
    send('download_click',({desktop:'windows',android:'android',tizen:'samsung-tv','android-tv':'android-tv'})[match[1]]);
  },true);
  view();
})();
