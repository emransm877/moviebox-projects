import {test} from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import worker,{WINDOW_MS} from '../worker/index.js';
function setup(){const db=new DatabaseSync(':memory:');for(const file of readdirSync(new URL('../drizzle/',import.meta.url)).filter(name=>name.endsWith('.sql')).sort())db.exec(readFileSync(new URL('../drizzle/'+file,import.meta.url),'utf8'));return {db,env:{PRESENCE_SECRET:'LOCAL-UNIT-TEST-ONLY-KEY-DO-NOT-DEPLOY-1234',DB:{prepare(sql){return {sql,args:[],bind(...args){return {...this,args};}};},async batch(statements){db.exec('BEGIN');try{const result=statements.map(s=>({results:s.sql.startsWith('SELECT')?db.prepare(s.sql).all(...s.args):(db.prepare(s.sql).run(...s.args),[])}));db.exec('COMMIT');return result;}catch(error){db.exec('ROLLBACK');throw error;}}}}};}
const origin='https://emransm877.github.io';
const req=(path,data,otherOrigin=origin)=>new Request('https://presence.invalid'+path,{method:data===undefined?'GET':'POST',headers:{origin:otherOrigin,'content-type':'application/json'},body:data===undefined?undefined:JSON.stringify(data)});
async function session(env,id){const r=await worker.fetch(req('/api/session',{id}),env);assert.equal(r.status,200);return (await r.json()).token;}
test('distinct browsers count once each, repeat tabs deduplicate, stale sessions expire',async()=>{const {db,env}=setup(),realNow=Date.now;let now=1795228800000;Date.now=()=>now;try{const a=await session(env,'a'.repeat(32)),b=await session(env,'b'.repeat(32));for(const [token,count] of [[a,1],[a,1],[b,2]])assert.equal((await (await worker.fetch(req('/api/presence',{token}),env)).json()).count,count);now+=WINDOW_MS+1;assert.equal((await (await worker.fetch(req('/api/count'),env)).json()).count,0);assert.equal(db.prepare('SELECT COUNT(*) AS count FROM active_browsers').get().count,0);}finally{Date.now=realNow;db.close();}});
test('invalid origins, tampered tokens, invalid IDs, oversized bodies and expired tokens rejected',async()=>{const {db,env}=setup();try{assert.equal((await worker.fetch(req('/api/session',{id:'a'.repeat(32)},'https://evil.invalid'),env)).status,403);assert.equal((await worker.fetch(req('/api/session',{id:"' OR 1=1"}),env)).status,400);assert.equal((await worker.fetch(req('/api/session',{id:'a'.repeat(600)}),env)).status,400);const token=await session(env,'c'.repeat(32));assert.equal((await worker.fetch(req('/api/presence',{token:'d'+token.slice(1)}),env)).status,401);const realNow=Date.now;Date.now=()=>realNow()+31*60_000;try{assert.equal((await worker.fetch(req('/api/presence',{token}),env)).status,401);}finally{Date.now=realNow;}assert.equal(db.prepare('SELECT COUNT(*) AS count FROM active_browsers').get().count,0);}finally{db.close();}});
test('preflight permits exact GitHub origin and unavailable service never fabricates zero',async()=>{const {db,env}=setup();try{const options=await worker.fetch(new Request('https://presence.invalid/api/presence',{method:'OPTIONS',headers:{origin}}),env);assert.equal(options.status,204);assert.equal(options.headers.get('access-control-allow-origin'),origin);const failed=await worker.fetch(req('/api/count'),{});assert.equal(failed.status,503);assert.equal((await failed.json()).count,undefined);const healthy=await worker.fetch(req('/api/count'),env);assert.equal(healthy.headers.get('cache-control'),'no-store');assert.equal((await healthy.json()).count,0);}finally{db.close();}});

test('usage requires explicit consent, validates dimensions and keeps only aggregate counters',async()=>{
  const {db,env}=setup();try{
    const token=await session(env,'f'.repeat(32)),base={token,consent:true,route:'windows',source:'facebook',content:'r01',event:'page_view',platform:'none'};
    assert.equal((await worker.fetch(req('/api/usage',{...base,consent:false}),env)).status,400);
    assert.equal((await worker.fetch(req('/api/usage',{...base,route:'https://private.invalid/account'}),env)).status,400);
    assert.equal((await worker.fetch(req('/api/usage',{...base,content:'private@example.com'}),env)).status,400);
    assert.equal((await worker.fetch(req('/api/usage',{...base,token:'bad'}),env)).status,401);
    for(let i=0;i<2;i++)assert.equal((await worker.fetch(req('/api/usage',base),env)).status,202);
    assert.equal((await worker.fetch(req('/api/usage',{...base,event:'download_click',platform:'windows'}),env)).status,202);
    const summary=await (await worker.fetch(req('/api/usage-summary?days=7'),env)).json();
    assert.equal(summary.rows.length,2);assert.equal(summary.rows.find(r=>r.event==='page_view').count,2);
    assert.equal(summary.rows.find(r=>r.event==='download_click').count,1);
    assert.equal(JSON.stringify(summary).includes(token),false);
    assert.equal(db.prepare('SELECT COUNT(*) AS count FROM active_browsers').get().count,0);
    assert.deepEqual(db.prepare('PRAGMA table_info(usage_counts)').all().map(c=>c.name),['day','route','source','content','event','platform','count']);
    assert.equal((await worker.fetch(req('/api/usage-summary?days=999'),env)).status,400);
  }finally{db.close();}
});

test('usage retention removes aggregates older than ninety days without changing presence',async()=>{
 const {db,env}=setup(),clock=Date.now;let time=clock();Date.now=()=>time;try{
   const event={consent:true,route:'home',source:'direct',content:'',event:'page_view',platform:'none'};
   await worker.fetch(req('/api/usage',{...event,token:await session(env,'a'.repeat(32))}),env);
   time+=91*86400000;
   await worker.fetch(req('/api/usage',{...event,token:await session(env,'b'.repeat(32))}),env);
   assert.equal(db.prepare('SELECT COUNT(*) AS count FROM usage_counts').get().count,1);
 }finally{Date.now=clock;db.close();}
});

test('usage summary purges the ninetieth prior day but retains ninety calendar days inclusive',async()=>{
 const {db,env}=setup(),clock=Date.now;const now=Date.UTC(2026,10,22,18,5);Date.now=()=>now;
 const day=value=>new Date(value+6*60*60*1000).toISOString().slice(0,10);
 try{
   const insert=db.prepare("INSERT INTO usage_counts(day,route,source,content,event,platform,count) VALUES (?,'home','direct','','page_view','none',1)");
   for(const age of [90,89,0])insert.run(day(now-age*86400000));
   const token=await session(env,'c'.repeat(32));await worker.fetch(req('/api/presence',{token}),env);
   const result=await worker.fetch(req('/api/usage-summary?days=30'),env);assert.equal(result.status,200);
   assert.equal(db.prepare('SELECT COUNT(*) AS count FROM usage_counts').get().count,2);
   assert.equal(db.prepare('SELECT COUNT(*) AS count FROM usage_counts WHERE day=?').get(day(now-90*86400000)).count,0);
   assert.equal(db.prepare('SELECT COUNT(*) AS count FROM usage_counts WHERE day=?').get(day(now-89*86400000)).count,1);
   assert.equal((await result.json()).rows.length,1);
   assert.equal(db.prepare('SELECT COUNT(*) AS count FROM active_browsers').get().count,1);
 }finally{Date.now=clock;db.close();}
});


test('native Android guide and download are separate from the Android patch',async()=>{
 const {db,env}=setup();try{
  const token=await session(env,'9'.repeat(32));
  for(const [route,platform] of [['android-app','android-app'],['android','android']]){
   const response=await worker.fetch(req('/api/usage',{token,consent:true,route,source:'direct',content:'',event:'download_click',platform}),env);
   assert.equal(response.status,202);
  }
  const rows=db.prepare('SELECT route,platform,count FROM usage_counts ORDER BY route').all();
  assert.deepEqual(rows.map(r=>[r.route,r.platform,r.count]),[['android','android',1],['android-app','android-app',1]]);
 }finally{db.close();}
});
