/* Public GitHub metadata only. No tokens, app telemetry or visitor identifiers. */
(function(global){
  'use strict';
  const owner='emransm877',projects=[['moviebox-android','Android'],['moviebox-desktop','Windows'],['moviebox-tizen','Samsung TV'],['moviebox-android-tv','Android TV'],['moviebox-android-native','Android app']];
  function kind(name,repo){
    name=name.toLowerCase();
    if(/\.(sha256|sha512)$/.test(name)||['sha256sums.txt','checksums.txt'].includes(name))return 'checksums';
    if(repo==='moviebox-android'&&/^moviebox-android-[0-9.]+\.apk$/.test(name))return 'apk';
    if(repo==='moviebox-android-native'&&/^moviebox-android-(app|native)-[0-9.]+\.apk$/.test(name))return 'apk';
    if(repo==='moviebox-android-tv'&&/^moviebox-android-tv-[0-9.]+\.apk$/.test(name))return 'apk';
    if(repo==='moviebox-desktop'&&/^moviebox-setup-[0-9.]+-windows-x64(-self-signed-test)?\.exe$/.test(name))return 'installer';
    if(repo==='moviebox-desktop'&&/^moviebox-(desktop-)?[0-9.]+-windows-x64(-portable|-self-signed-test)?\.zip$/.test(name))return 'portable';
    if(repo==='moviebox-tizen'&&/^moviebox-tv-[0-9.]+-install-bundle\.zip$/.test(name))return 'tv_bundle';
    if(repo==='moviebox-tizen'&&/^moviebox-tv-[0-9.]+-unsigned\.wgt$/.test(name))return 'tv_widget';
    return 'other';
  }
  function normalise(repo,platform,releases,latest){
    const kinds={apk:0,installer:0,portable:0,tv_bundle:0,tv_widget:0,checksums:0,other:0};
    const output=releases.filter(r=>!r.draft).map(r=>({tag:r.tag_name,url:r.html_url,publishedAt:r.published_at,prerelease:!!r.prerelease,assets:r.assets.map(a=>{
      const type=kind(a.name,repo),url=new URL(a.browser_download_url);
      if(url.origin!=='https://github.com'||url.username||url.password||!url.pathname.startsWith('/'+owner+'/'+repo+'/releases/download/'))throw new Error('Unexpected asset origin');
      if(!Number.isSafeInteger(a.download_count)||a.download_count<0)throw new Error('Invalid count');
      kinds[type]+=a.download_count;
      return {id:a.id,name:a.name,count:a.download_count,kind:type,url:url.href,size:a.size,createdAt:a.created_at,digest:a.digest||null};
    })}));
    // Retain archived APKs/counts while making the canonical same-release App APK the download.
    if(repo==='moviebox-android-native')for(const release of output)release.assets.sort((a,b)=>Number(/^moviebox-android-app-[0-9.]+\.apk$/i.test(b.name))-Number(/^moviebox-android-app-[0-9.]+\.apk$/i.test(a.name)));
    return {name:repo,platform,url:'https://github.com/'+owner+'/'+repo,releases:output,kinds,latestTag:latest.tag_name,
      packages:kinds.apk+kinds.installer+kinds.portable+kinds.tv_bundle+kinds.tv_widget,allAssets:Object.values(kinds).reduce((a,b)=>a+b,0)};
  }
  const snapshotKey='moviebox.downloads.snapshot.v1',modeKey='moviebox.downloads.mode.v1',retryKey='moviebox.downloads.retry.v1';
  function read(key){try{return global.localStorage.getItem(key);}catch{return null;}}
  function write(key,value){try{global.localStorage.setItem(key,value);}catch{/* Storage is optional. */}}
  function validate(value){
    if(!value||value.schemaVersion!==1||!Number.isFinite(Date.parse(value.observedAt))||!Array.isArray(value.repositories)||![4,5].includes(value.repositories.length))throw new Error('Invalid download snapshot');
    const names=new Set();
    const repositories=value.repositories.map(record=>{
      const expected=projects.find(([name])=>name===record.name);
      if(!expected||names.has(record.name)||record.platform!==expected[1]||!Array.isArray(record.releases)||record.releases.length>10000||typeof record.latestTag!=='string')throw new Error('Invalid project snapshot');
      names.add(record.name);
      const assetIds=new Set();
      const releases=record.releases.map(release=>{
        if(typeof release.tag!=='string'||typeof release.prerelease!=='boolean'||!Array.isArray(release.assets)||release.assets.length>10000||!Number.isFinite(Date.parse(release.publishedAt)))throw new Error('Invalid release snapshot');
        const url=new URL(release.url);
        if(url.origin!=='https://github.com'||url.username||url.password||!url.pathname.startsWith('/'+owner+'/'+record.name+'/releases/tag/'))throw new Error('Invalid release origin');
        return {tag_name:release.tag,html_url:release.url,published_at:release.publishedAt,prerelease:release.prerelease,assets:release.assets.map(asset=>{
          if(!Number.isSafeInteger(asset.id)||asset.id<1||assetIds.has(asset.id)||typeof asset.name!=='string'||!Number.isSafeInteger(asset.size)||asset.size<0)throw new Error('Invalid asset snapshot');
          assetIds.add(asset.id);
          return {id:asset.id,name:asset.name,download_count:asset.count,browser_download_url:asset.url,size:asset.size,created_at:asset.createdAt,digest:asset.digest};
        })};
      });
      const checked=normalise(record.name,record.platform,releases,{tag_name:record.latestTag});
      if(![checked.packages,checked.allAssets,...Object.values(checked.kinds)].every(Number.isSafeInteger))throw new Error('Download total exceeds safe integer range');
      if(!checked.releases.some(release=>release.tag===record.latestTag)||record.packages!==checked.packages||record.allAssets!==checked.allAssets||Object.keys(checked.kinds).some(k=>record.kinds?.[k]!==checked.kinds[k]))throw new Error('Inconsistent download totals');
      return checked;
    });
    if(projects.slice(0,4).some(([name])=>!names.has(name)))throw new Error('Incomplete download snapshot');
    return {schemaVersion:1,observedAt:value.observedAt,repositories};
  }
  function cached(){try{const raw=read(snapshotKey),value=raw&&raw.length<=3000000?validate(JSON.parse(raw)):null;return value&&Date.parse(value.observedAt)<=Date.now()+300000?value:null;}catch{return null;}}
  function remember(value){const checked=validate(value),previous=cached();if(!previous||Date.parse(checked.observedAt)>=Date.parse(previous.observedAt))write(snapshotKey,JSON.stringify(checked));return checked;}
  function mode(value){if(value==='all'||value==='packages')write(modeKey,value);return read(modeKey)==='all'?'all':'packages';}
  // Respect an actual server retry deadline across reloads, without extending it.
  let pausedUntil=Number(read(retryKey))||0;
  if(pausedUntil>Date.now()+3600000||pausedUntil<0)pausedUntil=0;
  async function load(signal){
    if(Date.now()<pausedUntil){const error=new Error('GitHub rate limit pause');error.status=429;error.retryAt=pausedUntil;throw error;}
    async function request(path,optional=false){
      const response=await fetch('https://api.github.com/repos/'+owner+'/'+path,{headers:{Accept:'application/vnd.github+json'},cache:'no-cache',signal});
      if(optional&&response.status===404)return null;
      const remaining=Number(response.headers.get('x-ratelimit-remaining')),reset=Number(response.headers.get('x-ratelimit-reset'))*1000;
      if(response.headers.has('x-ratelimit-remaining')&&remaining<9&&reset>Date.now()){pausedUntil=reset;write(retryKey,String(pausedUntil));}
      if(!response.ok){const error=new Error(response.status===403||response.status===429?'GitHub rate limit reached':'GitHub could not be reached');error.status=response.status;error.retryAt=(response.status===403||response.status===429)&&reset>Date.now()?reset:Date.now()+60000;pausedUntil=Math.max(pausedUntil,error.retryAt);write(retryKey,String(pausedUntil));throw error;}
      return response.json();
    }
    const repositories=await Promise.all(projects.map(async([repo,platform])=>{
      const optional=repo==='moviebox-android-native';
      const [latest,first]=await Promise.all([request(repo+'/releases/latest',optional),request(repo+'/releases?per_page=100&page=1',optional)]);
      if(optional&&(!latest||!first))return null;
      let releases=first;
      for(let page=2;releases.length===(page-1)*100;page++){
        if(page>100)throw new Error('Pagination limit exceeded');
        releases=releases.concat(await request(repo+'/releases?per_page=100&page='+page));
      }
      for(const release of releases){
        if(release.assets.length<100)continue;
        let assets=[];
        for(let page=1;page<=100;page++){
          const batch=await request(repo+'/releases/'+release.id+'/assets?per_page=100&page='+page);assets=assets.concat(batch);
          if(batch.length<100)break;if(page===100)throw new Error('Asset pagination limit exceeded');
        }
        release.assets=assets;
      }
      const record=normalise(repo,platform,releases,latest);
      return optional&&!global.MovieBoxReleaseInfo.published(record)?null:record;
    }));
    return validate({schemaVersion:1,observedAt:new Date().toISOString(),repositories:repositories.filter(Boolean)});
  }
  global.MovieBoxLiveCounts={load,normalise,kind,validate,cached,remember,mode,retryAt:()=>pausedUntil};
})(window);
