'use strict';
(() => {
  const $ = id => document.getElementById(id), format = value => Number(value || 0).toLocaleString();
  function setupProjectFlips(){
    const grid=document.querySelector('.project-grid');if(!grid)return;
    const cards=Array.from(grid.children),fine=matchMedia('(hover:hover) and (pointer:fine)');
    cards.forEach((card,index)=>{
      const label=card.querySelector('.project-label'),heading=card.querySelector('h3'),description=card.querySelector(':scope > p'),features=card.querySelector('.feature-list'),downloads=card.querySelector('.project-download');
      const name=label.querySelector('span').textContent,inner=element('div',null,'project-flip-inner'),front=element('div',null,'flip-face flip-front'),back=element('div',null,'flip-face flip-back');
      back.id='project-back-'+index;back.inert=true;back.setAttribute('aria-hidden','true');
      const mark=element('img',null,'flip-mark');mark.src='assets/moviebox-logo.svg';mark.alt='';mark.width=100;mark.height=100;
      const open=element('button','Explore downloads','flip-open');open.type='button';open.setAttribute('aria-expanded','false');open.setAttribute('aria-controls',back.id);
      const backHeader=element('div',null,'flip-back-heading'),backLabel=element('p',name,'flip-platform'),close=element('button','Back','flip-close');close.type='button';close.setAttribute('aria-label','Show '+name+' overview');backHeader.append(backLabel,close);
      front.append(label,mark,heading,description,open);back.append(backHeader,features,downloads);inner.append(front,back);card.replaceChildren(inner);
      function flip(show,focus=false){
        if(card.classList.contains('is-flipped')===show)return;
        card.classList.toggle('is-flipped',show);front.inert=show;back.inert=!show;front.setAttribute('aria-hidden',String(show));back.setAttribute('aria-hidden',String(!show));open.setAttribute('aria-expanded',String(show));
        if(focus)(show?close:open).focus({preventScroll:true});
      }
      open.addEventListener('click',()=>flip(true,true));close.addEventListener('click',()=>flip(false,true));
      card.addEventListener('pointerenter',event=>{if(fine.matches&&event.pointerType!=='touch'&&!card.contains(document.activeElement))flip(true);});
      card.addEventListener('pointerleave',()=>{if(!card.contains(document.activeElement))flip(false);});
      card.addEventListener('focusout',()=>setTimeout(()=>{if(!card.contains(document.activeElement))flip(false);},0));
      card.addEventListener('keydown',event=>{if(event.key==='Escape'&&card.classList.contains('is-flipped')){event.preventDefault();flip(false,true);}});
      card.addEventListener('toggle',()=>size(),true);
    });
    grid.classList.add('flip-ready');
    function size(){cards.forEach(card=>card.firstElementChild.style.height='680px');const height=Math.max(680,...cards.flatMap(card=>Array.from(card.querySelectorAll('.flip-face')).map(face=>face.scrollHeight+2)));cards.forEach(card=>card.firstElementChild.style.height=height+'px');}
    size();window.addEventListener('resize',size);if(document.fonts)document.fonts.ready.then(size);
  }
  let snapshot, history, savedSnapshot, refreshing=false, lastRefresh=0, releasePage=1;
  let syncFeedbackUntil=0,syncMessageTimer=null,snapshotIsLive=false;
  function syncMessage(text,kind='neutral'){
    let message=$('sync-feedback');if(!message){message=element('span',null,'sync-feedback');message.id='sync-feedback';message.setAttribute('role','status');$('refresh-live').parentElement.append(message);}
    clearTimeout(syncMessageTimer);message.textContent=text;message.dataset.kind=kind;
    if(kind!=='busy')syncMessageTimer=setTimeout(()=>{message.textContent='';},6000);
  }
  function syncButton(){
    const button=$('refresh-live');button.disabled=refreshing;button.setAttribute('aria-busy',String(refreshing));
    button.classList.toggle('is-spinning',refreshing||Date.now()<syncFeedbackUntil);
    button.setAttribute('aria-label',refreshing?'Syncing live download counts':'Sync live download counts');
  }
  function showTime(live,message=''){
    snapshotIsLive=live;
    const stale=Date.now()-Date.parse(snapshot.observedAt)>48*3600*1000;
    const observed=new Date(snapshot.observedAt),status=$('snapshot-status');
    const detail=(live?'Refreshed from GitHub ':'Saved snapshot collected ')+observed.toLocaleString()+' · Auto-check: 10 seconds'+(message?' · '+message:stale?' · Older than 48 hours':'');
    status.textContent=(live?'Updated ':'Saved ')+observed.toLocaleTimeString([],{hour:'numeric',minute:'2-digit'});
    status.title=detail;status.setAttribute('aria-description',detail);
    $('snapshot-status').classList.toggle('error',!!message||stale);
  }
  async function refreshLive(manual=false){
    if(refreshing||(!manual&&(document.hidden||Date.now()-lastRefresh<9500)))return;
    if(manual)syncMessage('Checking…','busy');
    refreshing=true;syncButton();
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),18000);
    try{
      const previous=snapshot.repositories.map(repo=>repo.name+':'+repo.packages+':'+repo.allAssets).join('|'),live=await window.MovieBoxLiveCounts.load(controller.signal);
      snapshot=live;lastRefresh=Date.now();showTime(true);setDownloads(snapshot.repositories.find(r=>r.platform==='Android TV'),{apk:'androidtv-download'},'androidtv');renderStats();updateVersions();renderGrowth();
      setDownloads(snapshot.repositories.find(r=>r.platform==='Windows'),{installer:'windows-download',portable:'portable-download'},'windows');
      setDownloads(snapshot.repositories.find(r=>r.platform==='Android'),{apk:'android-download'},'android');
      setDownloads(snapshot.repositories.find(r=>r.platform==='Samsung TV'),{tv_bundle:'tv-download'},'tv');
      if(manual)syncMessage(previous===snapshot.repositories.map(repo=>repo.name+':'+repo.packages+':'+repo.allAssets).join('|')?'Up to date':'Counts updated','success');
    }catch(error){
      const limited=error.status===403||error.status===429,message=(limited?'GitHub rate limit reached'+(error.retryAt?'; next API request after '+new Date(error.retryAt).toLocaleTimeString():''):'Live refresh unavailable')+'; showing last available counts';
      lastRefresh=Date.now();let newerSaved=false;
      if(manual){
        const fallbackController=new AbortController(),fallbackTimeout=setTimeout(()=>fallbackController.abort(),5000);
        try{
          const response=await fetch('data/latest.json',{cache:'no-store',signal:fallbackController.signal});if(!response.ok)throw new Error('Saved data unavailable');const saved=await response.json();
          if(saved.schemaVersion===1&&saved.repositories?.length===4&&saved.repositories.every(repo=>Number.isSafeInteger(repo.packages)&&Number.isSafeInteger(repo.allAssets))&&Date.parse(saved.observedAt)>Date.parse(snapshot.observedAt)){
            snapshot=saved;newerSaved=true;showTime(false,message);renderStats();updateVersions();renderGrowth();
            for(const [platform,prefix,kinds] of [['Windows','windows',{installer:'windows-download',portable:'portable-download'}],['Android','android',{apk:'android-download'}],['Samsung TV','tv',{tv_bundle:'tv-download'}],['Android TV','androidtv',{apk:'androidtv-download'}]])setDownloads(snapshot.repositories.find(repo=>repo.platform===platform),kinds,prefix);
          }
        }catch{}finally{clearTimeout(fallbackTimeout);}
      }
      if(!newerSaved)showTime(snapshotIsLive,message);
      if(manual)syncMessage(newerSaved?'Saved counts refreshed':limited?'GitHub limit · try later':'Connection unavailable',newerSaved?'success':'warning');
    }finally{clearTimeout(timeout);refreshing=false;syncButton();}
  }
  function element(tag, text, className) {
    const node = document.createElement(tag); if (text != null) node.textContent = text; if (className) node.className = className; return node;
  }
  function safeDownload(url, repo) {
    try { const parsed = new URL(url); return parsed.protocol === 'https:' && parsed.hostname === 'github.com' && parsed.pathname.startsWith('/emransm877/' + repo + '/releases/download/') ? parsed.href : ''; } catch { return ''; }
  }
  function releaseLink(url, repo) {
    try { const parsed = new URL(url); return parsed.origin === 'https://github.com' && parsed.pathname.startsWith('/emransm877/' + repo + '/releases/tag/') ? parsed.href : ''; } catch { return ''; }
  }
  function setDownloads(repo, selector, prefix) {
    const release = repo.releases.find(item => item.tag === repo.latestTag && !item.prerelease);
    if (!release) return; $(prefix + '-version').textContent = release.tag;
    document.querySelectorAll('[data-version-source="'+prefix+'"]').forEach(node=>node.textContent=release.tag);
    for (const [kind, id] of Object.entries(selector)) {
      const asset = release.assets.find(item => item.kind === kind), url = asset && safeDownload(asset.url, repo.name);
      if (url) {$(id).href = url;document.querySelectorAll('[data-download-source="'+id+'"]').forEach(node=>node.href=url);}
    }
  }
  function renderStats() {
    const all = $('count-mode').value === 'all', android = snapshot.repositories.find(r => r.platform === 'Android'), windows = snapshot.repositories.find(r => r.platform === 'Windows'), tv = snapshot.repositories.find(r => r.platform === 'Samsung TV');
    $('android-count').textContent = format(all ? android.allAssets : android.packages);
    $('windows-count').textContent = format(all ? windows.allAssets : windows.packages);
    $('tv-count').textContent = format(all ? tv.allAssets : tv.packages);
    $('tv-count-label').textContent = all ? 'all file downloads' : 'package downloads';
    const androidtv=snapshot.repositories.find(repo=>repo.platform==='Android TV');$('androidtv-count').textContent=format(all?androidtv.allAssets:androidtv.packages);$('androidtv-count-label').textContent=all?'all file downloads':'APK downloads';$('androidtv-breakdown').textContent=format(androidtv.kinds.apk)+' APKs · '+format(androidtv.kinds.checksums)+' checksum files';
    $('tv-breakdown').textContent = format(tv.kinds.tv_bundle) + ' bundles · ' + format(tv.kinds.tv_widget) + ' widgets';
    $('combined-count').textContent = format(snapshot.repositories.reduce((total,repo)=>total+(all?repo.allAssets:repo.packages),0));
    $('android-count-label').textContent = all ? 'all file downloads' : 'APK downloads';
    $('windows-count-label').textContent = all ? 'all file downloads' : 'package downloads';
    $('combined-label').textContent = all ? 'Combined release-file downloads' : 'Combined package downloads';
    $('android-breakdown').textContent = format(android.kinds.apk) + ' APKs · ' + format(android.kinds.checksums) + ' checksum files';
    $('windows-breakdown').textContent = format(windows.kinds.installer) + ' installers · ' + format(windows.kinds.portable) + ' ZIPs';
    $('checksum-note').textContent = 'Currently observed: ' + format(snapshot.repositories.reduce((total,repo)=>total+repo.kinds.checksums,0)) + ' checksum-file downloads across the four published projects. These are excluded from application-package totals.';
    renderReleases();
  }
  function filteredReleases() {
    return snapshot.repositories.filter(r => $('platform-filter').value === 'all' || r.platform === $('platform-filter').value)
      .flatMap(repo => repo.releases.map(release => ({ repo, release })));
  }
  function updateVersions(preserve=true) {
    const select = $('version-filter'),previous=preserve?select.value:'all'; select.replaceChildren(element('option', 'All versions')); select.firstChild.value = 'all';
    for (const { repo, release } of filteredReleases()) { const option = element('option', repo.platform + ' ' + release.tag); option.value = repo.name + ':' + release.tag; select.append(option); }
    if(Array.from(select.options).some(option=>option.value===previous))select.value=previous;
    renderReleases();
  }
  function renderReleases() {
    const body = $('release-rows'); body.replaceChildren(); const all = $('count-mode').value === 'all';
    const releases = filteredReleases().filter(({ repo, release }) => $('version-filter').value === 'all' || $('version-filter').value === repo.name + ':' + release.tag)
      .sort((a, b) => b.release.publishedAt.localeCompare(a.release.publishedAt));
    const selectedSize=Number($('release-page-size').value),pageSize=[5,10,20].includes(selectedSize)?selectedSize:5;
    const pages=Math.max(1,Math.ceil(releases.length/pageSize));releasePage=Math.max(1,Math.min(releasePage,pages));
    const start=(releasePage-1)*pageSize,end=Math.min(start+pageSize,releases.length);
    $('release-previous').disabled=releasePage===1;$('release-next').disabled=releasePage===pages;
    $('release-page-label').textContent='Page '+releasePage+' of '+pages;
    const range=releases.length?'Showing '+(start+1)+'–'+end+' of '+format(releases.length)+' releases':'No matching releases';
    if($('release-range').textContent!==range)$('release-range').textContent=range;
    for (const { repo, release } of releases.slice(start,end)) {
      const assets = release.assets.filter(a => all || ['apk', 'installer', 'portable', 'tv_bundle', 'tv_widget'].includes(a.kind));
      const row = element('tr'); row.append(element('td', repo.platform));
      const version = element('td'), url = releaseLink(release.url, repo.name);
      const link = element(url ? 'a' : 'span', release.tag); if (url) link.href = url; version.append(link);
      if (release.tag === repo.latestTag) version.append(element('span', 'Latest', 'release-badge'));
      if (release.prerelease) version.append(element('span', 'Preview', 'release-badge'));
      row.append(version, element('td', new Date(release.publishedAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })), element('td', format(assets.reduce((n, a) => n + a.count, 0)), 'number'));
      const files = element('td', null, 'file-links'),chips=element('div',null,'release-assets');files.append(chips);
      for (const asset of assets) {
        const target = safeDownload(asset.url, repo.name); if (!target) continue;
        let label=({ apk: 'APK', installer: 'Setup EXE', portable: 'Portable ZIP', tv_bundle: 'TV bundle', tv_widget: 'TV widget', checksums: 'Checksum', other: asset.name })[asset.kind];
        if(asset.kind==='checksums')label=/setup/i.test(asset.name)?'EXE checksum':/desktop|portable/i.test(asset.name)?'ZIP checksum':/bundle/i.test(asset.name)?'Bundle checksum':/\.wgt/i.test(asset.name)?'Widget checksum':'Checksum';
        const file=element('a',null,'asset-chip');file.append(element('span',label),element('span',format(asset.count),'asset-downloads'));
        file.href = target; file.title = asset.name;file.setAttribute('aria-label',asset.name+': '+format(asset.count)+' downloads');chips.append(file);
      }
      if(!chips.children.length){const fallback=element(url?'a':'span',url?'View release files':'No package files');if(url)fallback.href=url;chips.append(fallback);}
      row.append(files); body.append(row);
    }
    if (!releases.length) { const row = element('tr'), cell = element('td', 'No published releases match this filter.'); cell.colSpan = 5; row.append(cell); body.append(row); }
  }
  function renderGrowth() {
    const chart=$('growth-chart'),oldRange=chart.querySelector('select'),restoreRangeFocus=oldRange===document.activeElement,range=oldRange?oldRange.value:'all',projects=snapshot.repositories,points=(history.points||[]).map(point=>({at:point.at,packages:{...point.packages}}));chart.replaceChildren();
    if(snapshot!==savedSnapshot&&points.length&&Date.parse(snapshot.observedAt)>Date.parse(points.at(-1).at)){
      const peaks={...(history.assetPeaks||{})},totals={...points.at(-1).packages};
      projects.forEach(repo=>{let gain=0;repo.releases.forEach(release=>release.assets.filter(asset=>['apk','installer','portable','tv_bundle','tv_widget'].includes(asset.kind)).forEach(asset=>{const old=peaks[repo.name+':'+asset.id];gain+=old?Math.max(0,asset.count-old.count):(history.assetPeaks?asset.count:0);}));totals[repo.name]=Object.hasOwn(totals,repo.name)?totals[repo.name]+gain:repo.packages;});
      points.push({at:snapshot.observedAt,packages:totals,live:true});
    }
    const latest=points.at(-1),start=history.trackingStartedAt||(points[0]||{}).at;
    const header=element('div',null,'growth-controls'),rangeLabel=element('label','Show '),select=element('select');select.id='growth-range';select.setAttribute('aria-label','Growth observation range');
    [['all','All observations'],['24','Past 24 hours'],['168','Past 7 days'],['720','Past 30 days']].forEach(([value,label])=>{const option=element('option',label);option.value=value;select.append(option);});select.value=range;select.addEventListener('change',renderGrowth);rangeLabel.append(select);header.append(rangeLabel);chart.append(header);
    const legend=element('div',null,'growth-legend');
    projects.forEach((repo,index)=>{const first=points.find(point=>Object.hasOwn(point.packages,repo.name)),count=latest&&Object.hasOwn(latest.packages,repo.name)?latest.packages[repo.name]:repo.packages,delta=first?Math.max(0,count-first.packages[repo.name]):0,item=element('div',null,'growth-platform growth-color-'+index);item.append(element('span',repo.platform),element('strong',format(repo.packages)),element('small',first?'+'+format(delta)+' since tracking began':'Awaiting baseline'));legend.append(item);});chart.append(legend);
    const changes=points.slice(1).map((point,index)=>{const deltas={};projects.forEach(repo=>{deltas[repo.name]=Object.hasOwn(points[index].packages,repo.name)?Math.max(0,(point.packages[repo.name]||0)-points[index].packages[repo.name]):0;});return {at:point.at,from:points[index].at,delta:Object.values(deltas).reduce((n,v)=>n+v,0),deltas,packages:point.packages};});
    const end=latest?Date.parse(latest.at):Date.now(),filtered=changes.filter(point=>range==='all'||Date.parse(point.at)>=end-Number(range)*3600000),bins=[],size=Math.max(1,Math.ceil(filtered.length/60));
    for(let i=0;i<filtered.length;i+=size){const group=filtered.slice(i,i+size),point={...group.at(-1),from:group[0].from,delta:0,deltas:{}};group.forEach(record=>{point.delta+=record.delta;projects.forEach(repo=>point.deltas[repo.name]=(point.deltas[repo.name]||0)+record.deltas[repo.name]);});bins.push(point);}
    const detail=element('p',null,'growth-selection');detail.setAttribute('role','status');detail.setAttribute('aria-live','polite');
    if(!bins.length){const baseline=element('p','Baseline established. Earlier daily downloads cannot be reconstructed. New observed growth will appear automatically after another successful collection.','growth-baseline');chart.append(baseline);}
    else {
      const svgNS='http://www.w3.org/2000/svg',svgNode=(tag,attributes={})=>{const node=document.createElementNS(svgNS,tag);Object.entries(attributes).forEach(([name,value])=>node.setAttribute(name,String(value)));return node;};
      const plot=element('div',null,'trend-plot'),svg=svgNode('svg',{viewBox:'0 0 1000 250',preserveAspectRatio:'none','aria-hidden':'true'}),times=[Date.parse(bins[0].from),...bins.map(point=>Date.parse(point.at))],duration=Math.max(1,times.at(-1)-times[0]),x=time=>40+(time-times[0])/duration*920;
      let running=0;const totals=[0],series=projects.map(()=>[0]);bins.forEach(point=>{running+=point.delta;totals.push(running);projects.forEach((repo,index)=>series[index].push(series[index].at(-1)+(point.deltas[repo.name]||0)));});
      const maximum=Math.max(1,...totals),y=value=>220-value/maximum*185;
      [0,.5,1].forEach(fraction=>{const height=y(maximum*fraction);svg.append(svgNode('line',{x1:40,x2:960,y1:height,y2:height,class:'trend-grid'}));const label=svgNode('text',{x:34,y:height-7,class:'trend-axis'});label.textContent='+'+format(Math.round(maximum*fraction));svg.append(label);});
      const combined=totals.map((value,index)=>[x(times[index]),y(value)]),area=svgNode('path',{d:'M '+combined.map(pair=>pair.join(',')).join(' L ')+' L 960,220 L 40,220 Z',class:'trend-area'});svg.append(area);
      series.forEach((values,index)=>svg.append(svgNode('polyline',{points:values.map((value,i)=>x(times[i])+','+y(value)).join(' '),class:'trend-line growth-color-'+index})));
      svg.append(svgNode('polyline',{points:combined.map(pair=>pair.join(',')).join(' '),class:'trend-combined'}));
      const cursor=svgNode('line',{x1:960,x2:960,y1:26,y2:225,class:'trend-cursor'});svg.append(cursor);plot.append(svg);
      const tooltip=element('div',null,'trend-tooltip');tooltip.setAttribute('aria-hidden','true');plot.append(tooltip);
      const show=(point,index)=>{const position=x(times[index+1]);cursor.setAttribute('x1',position);cursor.setAttribute('x2',position);tooltip.style.left=Math.max(22,Math.min(78,position/10))+'%';tooltip.replaceChildren(element('span',new Date(point.at).toLocaleString(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})),element('strong','+'+format(point.delta)+' downloads'),element('small',format(Object.values(point.packages).reduce((sum,count)=>sum+count,0))+' observed total'));detail.textContent=projects.map(repo=>repo.platform+' +'+format(point.deltas[repo.name]||0)).join(' · ');};
      bins.forEach((point,index)=>{const button=element('button',null,'trend-point');button.type='button';button.style.left=(x(times[index+1])/10)+'%';button.style.top=(y(totals[index+1])/250*100)+'%';button.setAttribute('aria-label',new Date(point.at).toLocaleString()+': +'+format(point.delta)+' downloads');button.append(element('span','+'+format(point.delta),'visually-hidden'));['pointerenter','focus','click'].forEach(event=>button.addEventListener(event,()=>show(point,index)));plot.append(button);});
      const dates=element('div',null,'trend-dates');[times[0],times.at(-1)].forEach(time=>dates.append(element('span',new Date(time).toLocaleString(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}))));chart.append(plot,dates);show(bins.at(-1),bins.length-1);
    }
    chart.append(detail);
    if(restoreRangeFocus)select.focus({preventScroll:true});
  }
  async function load() {
    try {
      const responses = await Promise.all(['data/latest.json', 'data/history.json'].map(url => fetch(url, { cache: 'no-cache' })));
      if (responses.some(r => !r.ok)) throw new Error('Snapshot unavailable');
      [snapshot, history] = await Promise.all(responses.map(r => r.json()));
      savedSnapshot=snapshot;
      if (snapshot.schemaVersion !== 1 || !snapshot.repositories || snapshot.repositories.length !== 4) throw new Error('Unsupported snapshot');
      showTime(false);
      setDownloads(snapshot.repositories.find(r => r.platform === 'Windows'), { installer: 'windows-download', portable: 'portable-download' }, 'windows');
      setDownloads(snapshot.repositories.find(r => r.platform === 'Android'), { apk: 'android-download' }, 'android');
      setDownloads(snapshot.repositories.find(r => r.platform === 'Samsung TV'), { tv_bundle: 'tv-download' }, 'tv');
      setDownloads(snapshot.repositories.find(r=>r.platform==='Android TV'),{apk:'androidtv-download'},'androidtv');renderStats(); updateVersions(); renderGrowth();
      $('count-mode').addEventListener('change', renderStats);
      $('platform-filter').addEventListener('change',()=>{releasePage=1;updateVersions(false);});
      $('version-filter').addEventListener('change',()=>{releasePage=1;renderReleases();});
      $('release-page-size').addEventListener('change',()=>{releasePage=1;renderReleases();});
      $('release-previous').addEventListener('click',()=>{releasePage--;renderReleases();});
      $('release-next').addEventListener('click',()=>{releasePage++;renderReleases();});
      $('refresh-live').addEventListener('click',()=>{syncFeedbackUntil=Date.now()+800;syncButton();setTimeout(syncButton,820);refreshLive(true);});
      refreshLive();setInterval(()=>refreshLive(),10000);
    } catch {
      $('snapshot-status').textContent = 'Download statistics are unavailable. Published download links above still work.'; $('snapshot-status').classList.add('error');
      $('release-rows').replaceChildren(); const row = element('tr'), cell = element('td', 'Could not load the last successful snapshot. Please try again later.'); cell.colSpan = 5; row.append(cell); $('release-rows').append(row);
    }
  }
  function setupScreenshotPreview(){
    const tabs=Array.from(document.querySelectorAll('.preview-tabs [role="tab"]'));
    const activate=tab=>{tabs.forEach(item=>{const active=item===tab;item.setAttribute('aria-selected',String(active));item.tabIndex=active?0:-1;$(item.getAttribute('aria-controls')).hidden=!active;});};
    tabs.forEach((tab,index)=>{tab.addEventListener('click',()=>activate(tab));tab.addEventListener('keydown',event=>{let next;if(event.key==='ArrowRight')next=(index+1)%tabs.length;else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;event.preventDefault();activate(tabs[next]);tabs[next].focus();});});
  }
  setupScreenshotPreview();setupProjectFlips();load();
})();
