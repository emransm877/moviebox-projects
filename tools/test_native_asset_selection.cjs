const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const window={localStorage:{getItem:()=>null,setItem:()=>{}}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../site/live-counts.js'),'utf8'),{window,URL});
const normalise=window.MovieBoxLiveCounts.normalise;
function asset(repo,id,name,count){return {id,name,download_count:count,size:100+id,created_at:'2026-11-24T00:00:00Z',digest:'sha256:'+id,browser_download_url:`https://github.com/emransm877/${repo}/releases/download/v0.1.1/${name}`};}
function release(repo,assets){return {tag_name:'v0.1.1',html_url:`https://github.com/emransm877/${repo}/releases/tag/v0.1.1`,published_at:'2026-11-24T00:00:00Z',prerelease:false,assets};}
test('same-release refresh offers canonical APK and retains every counter/digest',()=>{
 const repo='moviebox-android-native',old=asset(repo,1,'MovieBox-Android-Native-0.1.1.apk',17),sum=asset(repo,3,'MovieBox-Android-App-0.1.1.apk.sha256',5),current=asset(repo,2,'MovieBox-Android-App-0.1.1.apk',2),input=release(repo,[old,sum,current]);
 const result=normalise(repo,'Android app',[input],{tag_name:'v0.1.1'});
 assert.equal(result.releases[0].assets[0].url,current.browser_download_url);
 assert.equal(result.packages,19);assert.equal(result.allAssets,24);
 assert.deepEqual(Array.from(result.releases[0].assets,a=>a.id),[2,1,3]);
 assert.equal(result.releases[0].assets[1].digest,old.digest);
 assert.deepEqual(input.assets,[old,sum,current]);
});
test('older native-only release remains installable',()=>{
 const repo='moviebox-android-native',old=asset(repo,1,'MovieBox-Android-Native-0.1.1.apk',17),result=normalise(repo,'Android app',[release(repo,[old])],{tag_name:'v0.1.1'});
 assert.equal(result.releases[0].assets[0].id,1);assert.equal(result.packages,17);
});
test('other platforms retain original asset order',()=>{
 const repo='moviebox-desktop',first=asset(repo,1,'MovieBox-Desktop-0.10.4-windows-x64.zip',9),second=asset(repo,2,'MovieBox-Setup-0.10.4-windows-x64.exe',12),result=normalise(repo,'Windows',[release(repo,[first,second])],{tag_name:'v0.1.1'});
 assert.deepEqual(Array.from(result.releases[0].assets,a=>a.id),[1,2]);assert.equal(result.packages,21);
});
