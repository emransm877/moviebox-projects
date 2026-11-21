/* Public GitHub metadata only. No tokens, app telemetry or visitor identifiers. */
(function(global){
  'use strict';
  const owner='emransm877',projects=[['moviebox-android','Android'],['moviebox-desktop','Windows'],['moviebox-tizen','Samsung TV'],['moviebox-android-tv','Android TV']];
  function kind(name,repo){
    name=name.toLowerCase();
    if(/\.(sha256|sha512)$/.test(name)||['sha256sums.txt','checksums.txt'].includes(name))return 'checksums';
    if(repo==='moviebox-android'&&/^moviebox-android-[0-9.]+\.apk$/.test(name))return 'apk';
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
      if(url.origin!=='https://github.com'||!url.pathname.startsWith('/'+owner+'/'+repo+'/releases/download/'))throw new Error('Unexpected asset origin');
      if(!Number.isSafeInteger(a.download_count)||a.download_count<0)throw new Error('Invalid count');
      kinds[type]+=a.download_count;
      return {id:a.id,name:a.name,count:a.download_count,kind:type,url:url.href,size:a.size,createdAt:a.created_at,digest:a.digest||null};
    })}));
    return {name:repo,platform,url:'https://github.com/'+owner+'/'+repo,releases:output,kinds,latestTag:latest.tag_name,
      packages:kinds.apk+kinds.installer+kinds.portable+kinds.tv_bundle+kinds.tv_widget,allAssets:Object.values(kinds).reduce((a,b)=>a+b,0)};
  }
  let pausedUntil=0;
  async function load(signal){
    if(Date.now()<pausedUntil){const error=new Error('GitHub rate limit pause');error.status=429;error.retryAt=pausedUntil;throw error;}
    async function request(path){
      const response=await fetch('https://api.github.com/repos/'+owner+'/'+path,{headers:{Accept:'application/vnd.github+json'},cache:'no-cache',signal});
      const remaining=Number(response.headers.get('x-ratelimit-remaining')),reset=Number(response.headers.get('x-ratelimit-reset'))*1000;
      if(response.headers.has('x-ratelimit-remaining')&&remaining<9&&reset>Date.now())pausedUntil=reset;
      if(!response.ok){const error=new Error(response.status===403||response.status===429?'GitHub rate limit reached':'GitHub could not be reached');error.status=response.status;error.retryAt=reset||Date.now()+60000;pausedUntil=Math.max(pausedUntil,error.retryAt);throw error;}
      return response.json();
    }
    const repositories=await Promise.all(projects.map(async([repo,platform])=>{
      const [latest,first]=await Promise.all([request(repo+'/releases/latest'),request(repo+'/releases?per_page=100&page=1')]);
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
      return normalise(repo,platform,releases,latest);
    }));
    return {schemaVersion:1,observedAt:new Date().toISOString(),repositories};
  }
  global.MovieBoxLiveCounts={load,normalise,kind};
})(window);
