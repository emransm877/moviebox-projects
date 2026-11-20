'use strict';
(() => {
  const $ = id => document.getElementById(id), format = value => Number(value || 0).toLocaleString();
  let snapshot, history, savedSnapshot, refreshing=false, lastRefresh=0;
  function showTime(live,message=''){
    const stale=Date.now()-Date.parse(snapshot.observedAt)>48*3600*1000;
    const observed=new Date(snapshot.observedAt),status=$('snapshot-status');
    const detail=(live?'Refreshed from GitHub ':'Saved snapshot collected ')+observed.toLocaleString()+' · Auto-check: 10 seconds'+(message?' · '+message:stale?' · Older than 48 hours':'');
    status.textContent=(live?'Updated ':'Saved ')+observed.toLocaleTimeString([],{hour:'numeric',minute:'2-digit'});
    status.title=detail;status.setAttribute('aria-description',detail);
    $('snapshot-status').classList.toggle('error',!!message||stale);
  }
  async function refreshLive(manual=false){
    if(refreshing||(!manual&&document.hidden)||Date.now()-lastRefresh<9500)return;
    refreshing=true;$('refresh-live').disabled=true;$('refresh-live').textContent='Refreshing…';
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),18000);
    try{
      const live=await window.MovieBoxLiveCounts.load(controller.signal);
      snapshot=live;lastRefresh=Date.now();showTime(true);renderStats();updateVersions();
      setDownloads(snapshot.repositories.find(r=>r.platform==='Windows'),{installer:'windows-download',portable:'portable-download'},'windows');
      setDownloads(snapshot.repositories.find(r=>r.platform==='Android'),{apk:'android-download'},'android');
      setDownloads(snapshot.repositories.find(r=>r.platform==='Samsung TV'),{tv_bundle:'tv-download'},'tv');
    }catch(error){
      lastRefresh=Date.now();showTime(snapshot!==savedSnapshot,(error.status===403||error.status===429?'GitHub rate limit reached'+(error.retryAt?'; next API request after '+new Date(error.retryAt).toLocaleTimeString():''):'Live refresh unavailable')+'; showing last available counts');
    }finally{clearTimeout(timeout);refreshing=false;$('refresh-live').disabled=false;$('refresh-live').textContent='Refresh live counts';}
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
    for (const [kind, id] of Object.entries(selector)) {
      const asset = release.assets.find(item => item.kind === kind), url = asset && safeDownload(asset.url, repo.name);
      if (url) $(id).href = url;
    }
  }
  function renderStats() {
    const all = $('count-mode').value === 'all', android = snapshot.repositories.find(r => r.platform === 'Android'), windows = snapshot.repositories.find(r => r.platform === 'Windows'), tv = snapshot.repositories.find(r => r.platform === 'Samsung TV');
    $('android-count').textContent = format(all ? android.allAssets : android.packages);
    $('windows-count').textContent = format(all ? windows.allAssets : windows.packages);
    $('tv-count').textContent = format(all ? tv.allAssets : tv.packages);
    $('tv-count-label').textContent = all ? 'all file downloads' : 'package downloads';
    $('tv-breakdown').textContent = format(tv.kinds.tv_bundle) + ' bundles · ' + format(tv.kinds.tv_widget) + ' widgets';
    $('combined-count').textContent = format(all ? android.allAssets + windows.allAssets + tv.allAssets : android.packages + windows.packages + tv.packages);
    $('android-count-label').textContent = all ? 'all file downloads' : 'APK downloads';
    $('windows-count-label').textContent = all ? 'all file downloads' : 'package downloads';
    $('combined-label').textContent = all ? 'Combined release-file downloads' : 'Combined package downloads';
    $('android-breakdown').textContent = format(android.kinds.apk) + ' APKs · ' + format(android.kinds.checksums) + ' checksum files';
    $('windows-breakdown').textContent = format(windows.kinds.installer) + ' installers · ' + format(windows.kinds.portable) + ' ZIPs';
    $('checksum-note').textContent = 'Currently observed: ' + format(android.kinds.checksums + windows.kinds.checksums + tv.kinds.checksums) + ' checksum-file downloads across both projects. These are excluded from application-package totals.';
    renderReleases();
  }
  function filteredReleases() {
    return snapshot.repositories.filter(r => $('platform-filter').value === 'all' || r.platform === $('platform-filter').value)
      .flatMap(repo => repo.releases.map(release => ({ repo, release })));
  }
  function updateVersions() {
    const select = $('version-filter'); select.replaceChildren(element('option', 'All versions')); select.firstChild.value = 'all';
    for (const { repo, release } of filteredReleases()) { const option = element('option', repo.platform + ' ' + release.tag); option.value = repo.name + ':' + release.tag; select.append(option); }
    renderReleases();
  }
  function renderReleases() {
    const body = $('release-rows'); body.replaceChildren(); const all = $('count-mode').value === 'all';
    const releases = filteredReleases().filter(({ repo, release }) => $('version-filter').value === 'all' || $('version-filter').value === repo.name + ':' + release.tag)
      .sort((a, b) => b.release.publishedAt.localeCompare(a.release.publishedAt));
    for (const { repo, release } of releases) {
      const assets = release.assets.filter(a => all || ['apk', 'installer', 'portable', 'tv_bundle', 'tv_widget'].includes(a.kind));
      const row = element('tr'); row.append(element('td', repo.platform));
      const version = element('td'), url = releaseLink(release.url, repo.name);
      const link = element(url ? 'a' : 'span', release.tag); if (url) link.href = url; version.append(link);
      if (release.tag === repo.latestTag) version.append(element('span', 'Latest', 'release-badge'));
      if (release.prerelease) version.append(element('span', 'Preview', 'release-badge'));
      row.append(version, element('td', new Date(release.publishedAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })), element('td', format(assets.reduce((n, a) => n + a.count, 0)), 'number'));
      const files = element('td', null, 'file-links');
      for (const asset of assets) {
        const target = safeDownload(asset.url, repo.name); if (!target) continue;
        const file = element('a', ({ apk: 'APK', installer: 'Setup EXE', portable: 'Portable ZIP', tv_bundle: 'TV bundle', tv_widget: 'TV widget', checksums: 'Checksum', other: asset.name })[asset.kind] + ' · ' + format(asset.count));
        file.href = target; file.title = asset.name; files.append(file);
      }
      row.append(files); body.append(row);
    }
    if (!releases.length) { const row = element('tr'), cell = element('td', 'No published releases match this filter.'); cell.colSpan = 5; row.append(cell); body.append(row); }
  }
  function renderGrowth() {
    const chart = $('growth-chart'), points = history.points || []; chart.replaceChildren();
    const days = new Set(points.map(p => p.at.slice(0, 10)));
    if (days.size < 2) {
      chart.append(element('p', 'Tracking has started. Daily growth will appear after the next day’s collection. Earlier daily downloads cannot be reconstructed.')); return;
    }
    const changes = points.slice(1).map((p, i) => ({ at: p.at, delta: Object.entries(p.packages).reduce((total, [name, count]) => total + (Object.hasOwn(points[i].packages, name) ? Math.max(0,count-points[i].packages[name]) : 0), 0) })).slice(-14);
    const max = Math.max(1, ...changes.map(p => p.delta)), bars = element('div', null, 'growth-bars');
    for (const point of changes) {
      const bar = element('div', null, 'growth-bar'), fill = element('div'); fill.style.height = (point.delta ? Math.max(4, point.delta / max * 90) : 2) + 'px';
      const date = new Date(point.at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      bar.append(element('b', '+' + format(point.delta)), fill, element('span', date)); bar.setAttribute('aria-label', date + ': ' + format(point.delta) + ' additional observed package downloads'); bars.append(bar);
    }
    chart.append(bars);
  }
  async function load() {
    try {
      const responses = await Promise.all(['data/latest.json', 'data/history.json'].map(url => fetch(url, { cache: 'no-cache' })));
      if (responses.some(r => !r.ok)) throw new Error('Snapshot unavailable');
      [snapshot, history] = await Promise.all(responses.map(r => r.json()));
      savedSnapshot=snapshot;
      if (snapshot.schemaVersion !== 1 || !snapshot.repositories || snapshot.repositories.length !== 3) throw new Error('Unsupported snapshot');
      showTime(false);
      setDownloads(snapshot.repositories.find(r => r.platform === 'Windows'), { installer: 'windows-download', portable: 'portable-download' }, 'windows');
      setDownloads(snapshot.repositories.find(r => r.platform === 'Android'), { apk: 'android-download' }, 'android');
      setDownloads(snapshot.repositories.find(r => r.platform === 'Samsung TV'), { tv_bundle: 'tv-download' }, 'tv');
      renderStats(); updateVersions(); renderGrowth();
      $('count-mode').addEventListener('change', renderStats); $('platform-filter').addEventListener('change', updateVersions); $('version-filter').addEventListener('change', renderReleases);
      $('refresh-live').addEventListener('click',()=>refreshLive(true));
      refreshLive();setInterval(()=>refreshLive(),10000);
    } catch {
      $('snapshot-status').textContent = 'Download statistics are unavailable. Published download links above still work.'; $('snapshot-status').classList.add('error');
      $('release-rows').replaceChildren(); const row = element('tr'), cell = element('td', 'Could not load the last successful snapshot. Please try again later.'); cell.colSpan = 5; row.append(cell); $('release-rows').append(row);
    }
  }
  load();
})();
