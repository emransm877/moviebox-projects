const ORIGIN='https://emransm877.github.io';
export const WINDOW_MS=90_000;
const TOKEN_MS=30*60_000;
const encoder=new TextEncoder();
const encode=bytes=>btoa(String.fromCharCode(...new Uint8Array(bytes))).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');
const decode=value=>Uint8Array.from(atob(value.replaceAll('-','+').replaceAll('_','/')),c=>c.charCodeAt(0));
async function key(env){if(!env.PRESENCE_SECRET||env.PRESENCE_SECRET.length<32)throw new Error('Presence signing key missing');return crypto.subtle.importKey('raw',encoder.encode(env.PRESENCE_SECRET),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);}
async function sign(id,expiry,env){const payload=id+'.'+expiry;return payload+'.'+encode(await crypto.subtle.sign('HMAC',await key(env),encoder.encode(payload)));}
async function verify(token,env,now){
  if(typeof token!=='string'||token.length>200)return null;
  const [id,expiry,signature,...extra]=token.split('.');
  if(extra.length||!/^[a-f0-9]{32}$/.test(id)||!/^\d{13}$/.test(expiry)||!/^[A-Za-z0-9_-]{43}$/.test(signature||''))return null;
  const until=Number(expiry);if(until<=now||until>now+TOKEN_MS+5000)return null;
  return await crypto.subtle.verify('HMAC',await key(env),decode(signature),encoder.encode(id+'.'+expiry))?id:null;
}
function reply(body,status=200){return new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store','access-control-allow-origin':ORIGIN,'vary':'Origin','x-content-type-options':'nosniff'}});}
async function input(request){
  if(!request.headers.get('content-type')?.startsWith('application/json'))throw new Error('bad-input');
  const reader=request.body?.getReader();if(!reader)throw new Error('bad-input');let size=0,chunks=[];
  while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>512){await reader.cancel();throw new Error('bad-input');}chunks.push(value);}
  const data=new Uint8Array(size);let offset=0;for(const chunk of chunks){data.set(chunk,offset);offset+=chunk.length;}
  return JSON.parse(new TextDecoder().decode(data));
}
export default {
  async fetch(request,env){
    const path=new URL(request.url).pathname,origin=request.headers.get('origin');
    if(path==='/'&&request.method==='GET')return new Response('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta name="robots" content="noindex"><title>MovieBox Live Presence</title><style>body{background:#0b1716;color:#d8f8e6;font:16px system-ui;margin:15vh auto;padding:24px;max-width:600px}h1{font-size:30px}p{color:#abc4b5;line-height:1.7}a{color:#adf1cd}</style><h1>MovieBox Live Presence</h1><p>Anonymous, short-lived activity counts for MovieBox Projects. Visiting this service page does not count as a MovieBox visitor.</p><a href="https://emransm877.github.io/moviebox-projects/">Open MovieBox Projects</a></html>',{headers:{'content-type':'text/html; charset=utf-8','cache-control':'no-store'}});
    if(!['/api/session','/api/presence','/api/count'].includes(path))return reply({error:'not-found'},404);
    if(origin!==ORIGIN)return reply({error:'origin-not-allowed'},403);
    if(request.method==='OPTIONS')return new Response(null,{status:204,headers:{'access-control-allow-origin':ORIGIN,'access-control-allow-methods':'GET, POST, OPTIONS','access-control-allow-headers':'Content-Type','access-control-max-age':'600','cache-control':'no-store','vary':'Origin'}});
    if((path==='/api/count'&&request.method!=='GET')||(path!=='/api/count'&&request.method!=='POST'))return reply({error:'method-not-allowed'},405);
    try{
      const now=Date.now();
      if(path==='/api/session'){
        let data;try{data=await input(request);}catch{return reply({error:'invalid-input'},400);}
        if(!data||!/^[a-f0-9]{32}$/.test(data.id||''))return reply({error:'invalid-id'},400);
        const expires=now+TOKEN_MS;return reply({token:await sign(data.id,expires,env),expiresAt:expires});
      }
      if(!env.DB)return reply({error:'service-unavailable'},503);
      const statements=[env.DB.prepare('DELETE FROM active_browsers WHERE expires_at <= ?').bind(now)];
      if(path==='/api/presence'){
        let data;try{data=await input(request);}catch{return reply({error:'invalid-input'},400);}
        const id=await verify(data?.token,env,now);if(!id)return reply({error:'invalid-session'},401);
        statements.push(env.DB.prepare('INSERT INTO active_browsers (browser_id, expires_at) VALUES (?, ?) ON CONFLICT(browser_id) DO UPDATE SET expires_at = excluded.expires_at').bind(id,now+WINDOW_MS));
      }
      statements.push(env.DB.prepare('SELECT COUNT(*) AS count FROM active_browsers WHERE expires_at > ?').bind(now));
      const results=await env.DB.batch(statements),count=results.at(-1).results[0].count;
      if(!Number.isSafeInteger(count)||count<0)throw new Error('invalid-count');
      return reply({count,windowSeconds:WINDOW_MS/1000,observedAt:now});
    }catch{return reply({error:'service-unavailable'},503);}
  }
};
