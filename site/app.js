'use strict';
(() => {
  const $ = id => document.getElementById(id), format = value => Number(value || 0).toLocaleString();
  function setupProjectFlips(){
    const grid=document.querySelector('.project-grid');if(!grid||grid.classList.contains('cinema-scenes'))return;
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
  function fitTotal(){
    const total=$('combined-count');if(!total)return;
    total.style.fontSize='';
    if(total.clientWidth>0&&total.scrollWidth>total.clientWidth){
      total.style.fontSize=(parseFloat(getComputedStyle(total).fontSize)*total.clientWidth/total.scrollWidth*.98)+'px';
    }
  }
  function showTime(live, message='') {
    const analytics = $('analytics');
    analytics.dataset.state = live ? 'live' : 'saved';
    analytics.dataset.observedAt = snapshot.observedAt;
    analytics.dataset.refreshState = message ? 'unavailable' : 'available';
  }
  function applySnapshot(candidate,live=false){
    const checked=window.MovieBoxLiveCounts.validate(candidate);
    if(snapshot&&Date.parse(checked.observedAt)<Date.parse(snapshot.observedAt))return false;
    snapshot=checked;showTime(live);updateNativeAvailability();renderStats();updateVersions();renderGrowth();
    for(const [platform,prefix,kinds] of [
      ['Windows','windows',{installer:'windows-download',portable:'portable-download'}],
      ['Android','android',{apk:'android-download'}],['Samsung TV','tv',{tv_bundle:'tv-download'}],
      ['Android TV','androidtv',{apk:'androidtv-download'}],['Android app','native',{apk:'native-download'}]
    ])setDownloads(snapshot.repositories.find(repo=>repo.platform===platform),kinds,prefix);
    return true;
  }
  async function refreshSaved(signal){
    const response=await fetch('data/latest.json',{cache:'no-cache',signal});
    if(!response.ok)throw new Error('Snapshot unavailable');
    const candidate=window.MovieBoxLiveCounts.validate(await response.json());
    if(!savedSnapshot||Date.parse(candidate.observedAt)>Date.parse(savedSnapshot.observedAt)){
      savedSnapshot=candidate;window.MovieBoxLiveCounts.remember(candidate);
      try{const result=await fetch('data/history.json',{cache:'no-cache',signal});if(result.ok){const next=await result.json();if(next.schemaVersion===1&&Array.isArray(next.points))history=next;}}catch{/* Keep the last known history. */}
      if(!applySnapshot(candidate)&&snapshot)renderGrowth();
    }
  }
  async function refreshLive() {
    if (refreshing || document.hidden || Date.now() - lastRefresh < 9500) return;
    refreshing = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 18000);
    try {
      // Static collections can recover while GitHub's public API is rate-limited.
      try{await refreshSaved(controller.signal);}catch{/* Keep the newest verified observation. */}
      applySnapshot(window.MovieBoxLiveCounts.remember(await window.MovieBoxLiveCounts.load(controller.signal)),true);
    } catch {
      showTime($('analytics').dataset.state === 'live', 'unavailable');
    } finally {
      clearTimeout(timeout);
      lastRefresh = Date.now();
      refreshing = false;
    }
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
    if(!repo)return;
    const release = MovieBoxReleaseInfo.published(repo);
    if (!release) return; $(prefix + '-version').textContent = MovieBoxReleaseInfo.label(release.tag);
    document.querySelectorAll('[data-version-source="'+prefix+'"]').forEach(node=>node.textContent=MovieBoxReleaseInfo.label(release.tag));
    document.querySelectorAll('[data-theme-source="'+prefix+'"]').forEach(node=>node.textContent=MovieBoxReleaseInfo.themes(repo,release));
    if(prefix==='tv')document.querySelectorAll('[data-tizen-scope]').forEach(node=>node.textContent=MovieBoxReleaseInfo.tizenScope(release));
    for (const [kind, id] of Object.entries(selector)) {
      const asset = release.assets.find(item => item.kind === kind), url = asset && safeDownload(asset.url, repo.name);
      if (url) {$(id).href = url;document.querySelectorAll('[data-download-source="'+id+'"]').forEach(node=>node.href=url);}
    }
  }
  function platformLabel(repo){return repo.name==='moviebox-android'?'Android patch':repo.platform;}
  function updateNativeAvailability(){
    const repo=snapshot.repositories.find(item=>item.name==='moviebox-android-native'),available=!!(repo&&MovieBoxReleaseInfo.published(repo));
    const card=$('native-project'),changed=card.hidden===available;
    document.querySelectorAll('[data-published-project="moviebox-android-native"]').forEach(node=>node.hidden=!available);
    const count=available?5:4;
    document.querySelector('.project-grid').dataset.projectCount=count;
    document.querySelector('.stat-grid').dataset.projectCount=count;
    document.querySelectorAll('[data-project-total]').forEach(node=>node.textContent=available?'Five':'Four');
    document.querySelectorAll('[data-all-projects]').forEach(node=>node.textContent=available?'All five projects':'All four projects');
    if(available)setDownloads(repo,{apk:'native-download'},'native');
    if(changed)window.dispatchEvent(new Event('resize'));
  }
  function renderStats() {
    const all = $('count-mode').value === 'all', android = snapshot.repositories.find(r => r.platform === 'Android'), windows = snapshot.repositories.find(r => r.platform === 'Windows'), tv = snapshot.repositories.find(r => r.platform === 'Samsung TV');
    $('android-count').textContent = format(all ? android.allAssets : android.packages);
    $('windows-count').textContent = format(all ? windows.allAssets : windows.packages);
    $('tv-count').textContent = format(all ? tv.allAssets : tv.packages);
    $('tv-count-label').textContent = all ? 'all file downloads' : 'package downloads';
    const androidtv=snapshot.repositories.find(repo=>repo.platform==='Android TV');$('androidtv-count').textContent=format(all?androidtv.allAssets:androidtv.packages);$('androidtv-count-label').textContent=all?'all file downloads':'APK downloads';$('androidtv-breakdown').textContent=format(androidtv.kinds.apk)+' APKs · '+format(androidtv.kinds.checksums)+' checksum files';
    $('tv-breakdown').textContent = format(tv.kinds.tv_bundle) + ' bundles · ' + format(tv.kinds.tv_widget) + ' widgets';
    const native=snapshot.repositories.find(repo=>repo.name==='moviebox-android-native');if(native){$('native-count').textContent=format(all?native.allAssets:native.packages);$('native-count-label').textContent=all?'all file downloads':'APK downloads';$('native-breakdown').textContent=format(native.kinds.apk)+' APKs \u00b7 '+format(native.kinds.checksums)+' checksum files';}
    $('combined-count').textContent = format(snapshot.repositories.reduce((total,repo)=>total+(all?repo.allAssets:repo.packages),0));
    fitTotal();
    $('android-count-label').textContent = all ? 'all file downloads' : 'APK downloads';
    $('windows-count-label').textContent = all ? 'all file downloads' : 'package downloads';
    $('combined-label').textContent = all ? 'Release-file downloads across all releases' : 'Application package downloads across all releases';
    const peak=Math.max(0,...snapshot.repositories.map(repo=>all?repo.allAssets:repo.packages));
    document.querySelectorAll('[data-tally-repo]').forEach(bar=>{
      const repo=snapshot.repositories.find(item=>item.name===bar.dataset.tallyRepo);if(!repo)return;
      const value=all?repo.allAssets:repo.packages;
      bar.querySelector('i').style.width=(peak?value/peak*100:0)+'%';
      bar.title=format(value)+(all?' release-file':' package')+' downloads across all releases';
    });
    $('android-breakdown').textContent = format(android.kinds.apk) + ' APKs · ' + format(android.kinds.checksums) + ' checksum files';
    $('windows-breakdown').textContent = format(windows.kinds.installer) + ' installers · ' + format(windows.kinds.portable) + ' ZIPs';
    renderReleases();
  }
  function filteredReleases() {
    return snapshot.repositories.filter(r => $('platform-filter').value === 'all' || r.platform === $('platform-filter').value)
      .flatMap(repo => repo.releases.map(release => ({ repo, release })));
  }
  function updateVersions(preserve=true) {
    const select = $('version-filter'),previous=preserve?select.value:'all'; select.replaceChildren(element('option', 'All versions')); select.firstChild.value = 'all';
    for (const { repo, release } of filteredReleases()) { const option = element('option', platformLabel(repo) + ' ' + MovieBoxReleaseInfo.label(release.tag)); option.value = repo.name + ':' + release.tag; select.append(option); }
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
      const row = element('tr'); row.append(element('td', platformLabel(repo)));
      const version = element('td'), url = releaseLink(release.url, repo.name);
      const link = element(url ? 'a' : 'span', MovieBoxReleaseInfo.label(release.tag)); if (url) link.href = url; version.append(link);
      if (release.tag === repo.latestTag) version.append(element('span', 'Latest', 'release-badge'));
      if (release.prerelease && !MovieBoxReleaseInfo.label(release.tag).includes(' \u00b7 Preview ')) version.append(element('span', 'Preview', 'release-badge'));
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
    const chart = $('growth-chart'), projects = snapshot.repositories;
    const range = chart.dataset.range || 'all', platform = chart.dataset.platform || 'all';
    const signature = JSON.stringify([history.points, projects.map(repo => [repo.name, repo.packages]), range, platform]);
    if (chart.dataset.signature === signature) return;
    const focused = chart.contains(document.activeElement) ? document.activeElement.id : '';
    chart.dataset.signature = signature;
    chart._trendPointerController?.abort();
    chart._trendPointerController = new AbortController();
    chart.replaceChildren();
    const points = (history.points || []).filter(point => Number.isFinite(Date.parse(point.at))).map(point => ({at: point.at, packages: {...point.packages}}));
    // Add only observed increases. A newly appearing platform establishes a baseline.
    if (snapshot !== savedSnapshot && points.length && Date.parse(snapshot.observedAt) > Date.parse(points.at(-1).at)) {
      const totals = {...points.at(-1).packages}, peaks = history.assetPeaks || {};
      let increased = false;
      projects.forEach(repo => {
        let gain = 0;
        repo.releases.forEach(release => release.assets.filter(asset => ['apk', 'installer', 'portable', 'tv_bundle', 'tv_widget'].includes(asset.kind)).forEach(asset => {
          const old = peaks[repo.name + ':' + asset.id];
          gain += old ? Math.max(0, asset.count - old.count) : history.assetPeaks ? asset.count : 0;
        }));
        if (Object.hasOwn(totals, repo.name)) { totals[repo.name] += gain; increased ||= gain > 0; }
        else totals[repo.name] = repo.packages;
      });
      if (increased) points.push({at: snapshot.observedAt, packages: totals});
    }
    const controls = element('div', null, 'trend-toolbar'), tabs = element('div', null, 'trend-tabs');
    tabs.setAttribute('aria-label', 'Chart platform');
    [['all', 'All platforms'], ...projects.map(repo => [repo.name, platformLabel(repo)])].forEach(([name, label], index) => {
      const button = element('button', label, 'trend-tab' + (index ? ' growth-color-' + (index - 1) : ''));
      button.id = 'trend-platform-' + name; button.type = 'button'; button.setAttribute('aria-pressed', String(name === platform));
      button.addEventListener('click', () => { chart.dataset.platform = name; renderGrowth(); });
      tabs.append(button);
    });
    const select = element('select'); select.id = 'growth-range'; select.setAttribute('aria-label', 'Download trend period');
    [['all', 'All time'], ['24', '24 hours'], ['168', '7 days'], ['720', '30 days']].forEach(([value, label]) => {
      const option = element('option', label); option.value = value; select.append(option);
    });
    select.value = range; select.addEventListener('change', () => { chart.dataset.range = select.value; renderGrowth(); });
    controls.append(tabs, select); chart.append(controls);
    const end = points.length ? Date.parse(points.at(-1).at) : Date.now();
    const changes = points.slice(1).map((point, index) => {
      const deltas = {};
      projects.forEach(repo => { deltas[repo.name] = Object.hasOwn(points[index].packages, repo.name) && Object.hasOwn(point.packages, repo.name) ? Math.max(0, point.packages[repo.name] - points[index].packages[repo.name]) : 0; });
      return {at: point.at, from: points[index].at, deltas};
    }).filter(point => range === 'all' || Date.parse(point.from) >= end - Number(range) * 3600000);
    if (!changes.length) {
      chart.append(element('p', 'No recorded growth in this period yet.', 'trend-empty'));
      if (focused) $(focused)?.focus({preventScroll: true});
      return;
    }
    const active = platform === 'all' ? projects : projects.filter(repo => repo.name === platform);
    const totals = [0], series = projects.map(() => [0]);
    changes.forEach(point => {
      totals.push(totals.at(-1) + active.reduce((sum, repo) => sum + point.deltas[repo.name], 0));
      projects.forEach((repo, index) => series[index].push(series[index].at(-1) + point.deltas[repo.name]));
    });
    const caption = element('div', null, 'trend-caption');
    caption.append(element('span', 'Observed package growth'), element('strong', '+' + format(totals.at(-1)))); chart.append(caption);
    const svgNode = (tag, attrs = {}) => {
      const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
      Object.entries(attrs).forEach(([name, value]) => node.setAttribute(name, String(value))); return node;
    };
    const times = [Date.parse(changes[0].from), ...changes.map(point => Date.parse(point.at))], duration = Math.max(1, times.at(-1) - times[0]);
    const x = time => 48 + (time - times[0]) / duration * 904;
    const max = Math.max(1, totals.at(-1)), y = value => 236 - value / max * 204;
    const plot = element('div', null, 'trend-plot'); plot.id = 'trend-interactive'; plot.tabIndex = 0;
    plot.setAttribute('role', 'group'); plot.setAttribute('aria-label', 'Download growth chart. Use left and right arrows to inspect observations.');
    const svg = svgNode('svg', {viewBox: '0 0 1000 260', preserveAspectRatio: 'none', 'aria-hidden': 'true'});
    [...new Set([0, Math.round(max / 2), max])].forEach(value => {
      svg.append(svgNode('line', {x1: 48, x2: 952, y1: y(value), y2: y(value), class: 'trend-grid'}));
      const label = element('span', format(value), 'trend-y-label');
      label.style.top = (y(value) / 260 * 100) + '%'; plot.append(label);
    });
    const path = totals.map((value, index) => x(times[index]) + ',' + y(value)).join(' ');
    svg.append(svgNode('path', {d: 'M ' + path.replaceAll(' ', ' L ') + ' L 952,236 L 48,236 Z', class: 'trend-area'}));
    projects.forEach((repo, index) => {
      if (platform !== 'all' && platform !== repo.name) return;
      svg.append(svgNode('polyline', {points: series[index].map((value, i) => x(times[i]) + ',' + y(value)).join(' '), class: 'trend-line growth-color-' + index}));
    });
    svg.append(svgNode('polyline', {points: path, class: 'trend-combined'}));
    const cursor = svgNode('line', {y1: 28, y2: 236, class: 'trend-cursor'}), dot = svgNode('circle', {r: 4, class: 'trend-dot'});
    cursor.style.display = 'none'; dot.style.display = 'none'; svg.append(cursor, dot); plot.append(svg);
    const tooltip = element('div', null, 'trend-tooltip'); tooltip.hidden = true; plot.append(tooltip);
    const detail = element('p', null, 'growth-selection visually-hidden'); detail.setAttribute('role', 'status');
    let selected = changes.length - 1;
    function inspect(index) {
      selected = Math.max(0, Math.min(changes.length - 1, index));
      const point = changes[selected], position = x(times[selected + 1]), count = totals[selected + 1];
      cursor.style.display = ''; dot.style.display = ''; cursor.setAttribute('x1', position); cursor.setAttribute('x2', position); dot.setAttribute('cx', position); dot.setAttribute('cy', y(count));
      tooltip.hidden = false; tooltip.style.left = Math.max(24, Math.min(76, position / 10)) + '%';
      tooltip.replaceChildren(element('span', new Date(point.at).toLocaleString(undefined, {month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'})), element('strong', '+' + format(count) + ' in this period'));
      active.forEach(repo => tooltip.append(element('small', platformLabel(repo) + ' +' + format(series[projects.indexOf(repo)][selected + 1]))));
      detail.textContent = tooltip.textContent;
    }
    function hide() { tooltip.hidden = true; cursor.style.display = 'none'; dot.style.display = 'none'; }
    function nearest(event) {
      const bounds = plot.getBoundingClientRect(), value = (event.clientX - bounds.left) / bounds.width * 1000;
      let index = 0;
      changes.forEach((point, i) => { if (Math.abs(x(Date.parse(point.at)) - value) < Math.abs(x(Date.parse(changes[index].at)) - value)) index = i; });
      inspect(index);
    }
    plot.addEventListener('pointermove', event => { if (event.pointerType !== 'touch') nearest(event); });
    plot.addEventListener('pointerdown', event => {
      if (event.pointerType === 'touch') {
        plot.focus({preventScroll: true});
        nearest(event);
      } else nearest(event);
    });
    plot.addEventListener('pointerleave', event => { if (event.pointerType !== 'touch') hide(); });
    plot.addEventListener('focus', () => inspect(selected)); plot.addEventListener('blur', hide);
    document.addEventListener('pointerdown', event => {
      if (!plot.isConnected) return;
      if (!plot.contains(event.target)) hide();
    }, {signal: chart._trendPointerController?.signal});
    plot.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End', 'Escape'].includes(event.key)) return;
      event.preventDefault();
      if (event.key === 'Escape') hide();
      else inspect(event.key === 'Home' ? 0 : event.key === 'End' ? changes.length - 1 : selected + (event.key === 'ArrowRight' ? 1 : -1));
    });
    const dates = element('div', null, 'trend-dates');
    [times[0], times.at(-1)].forEach(time => dates.append(element('span', new Date(time).toLocaleString(undefined, {month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'}))));
    chart.append(plot, dates, detail);
    if (focused) $(focused)?.focus({preventScroll: true});
  }
  async function load() {
    try {
      $('count-mode').value=window.MovieBoxLiveCounts.mode();
      history={schemaVersion:1,points:[]};
      const cached=window.MovieBoxLiveCounts.cached();
      if(cached)applySnapshot(cached);
      try{await refreshSaved();}catch{if(!snapshot)throw new Error('Snapshot unavailable');}
      $('count-mode').addEventListener('change',()=>{window.MovieBoxLiveCounts.mode($('count-mode').value);renderStats();});
      $('platform-filter').addEventListener('change',()=>{releasePage=1;updateVersions(false);});
      $('version-filter').addEventListener('change',()=>{releasePage=1;renderReleases();});
      $('release-page-size').addEventListener('change',()=>{releasePage=1;renderReleases();});
      $('release-previous').addEventListener('click',()=>{releasePage--;renderReleases();});
      $('release-next').addEventListener('click',()=>{releasePage++;renderReleases();});
      refreshLive();setInterval(()=>refreshLive(),10000);
    } catch {
      $('analytics').dataset.state = 'unavailable';
      $('growth-chart').textContent = 'Download statistics are temporarily unavailable.';
      $('release-rows').replaceChildren(); const row = element('tr'), cell = element('td', 'Could not load the last successful snapshot. Please try again later.'); cell.colSpan = 5; row.append(cell); $('release-rows').append(row);
    }
  }
  function setupScreenshotPreview(){
    const tabs=Array.from(document.querySelectorAll('.preview-tabs [role="tab"]'));
    const activate=tab=>{tabs.forEach(item=>{const active=item===tab;item.setAttribute('aria-selected',String(active));item.tabIndex=active?0:-1;$(item.getAttribute('aria-controls')).hidden=!active;});};
    tabs.forEach((tab,index)=>{tab.addEventListener('click',()=>activate(tab));tab.addEventListener('keydown',event=>{let next;if(event.key==='ArrowRight')next=(index+1)%tabs.length;else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;event.preventDefault();activate(tabs[next]);tabs[next].focus();});});
  }
  window.addEventListener('resize',fitTotal);
  if(document.fonts)document.fonts.ready.then(fitTotal);
  setupScreenshotPreview();setupProjectFlips();load();
})();
