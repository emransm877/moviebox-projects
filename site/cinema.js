
(function(){
  "use strict";
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fine = window.matchMedia && matchMedia('(pointer: fine)').matches;
  var small = Math.min(innerWidth, innerHeight) < 700;

  /* Recommend a device without replacing or hiding the other downloads. */
  var ua=navigator.userAgent||'', device=/Tizen|SMART-TV/i.test(ua)?'tv':/Android/i.test(ua)?(/\bTV\b|AFT|BRAVIA|GoogleTV|SmartTV/i.test(ua)?'androidtv':'native'):/Windows/i.test(ua)?'windows':'';
  var tickets=document.getElementById('tickets'),recommended=device&&tickets.querySelector('[data-dev="'+device+'"]');
  if(recommended&&!recommended.hidden){tickets.prepend(recommended);recommended.classList.add('me','mag');recommended.querySelector('.k').textContent='For this device';}
  /* ---------- timecode ---------- */
  var tc = document.getElementById('tc'), t0 = performance.now();
  function pad(n){return (n<10?'0':'')+n}
  function tick(){
    var f = Math.floor((performance.now()-t0)/1000*24), s=Math.floor(f/24);
    tc.textContent = 'TC '+pad(Math.floor(s/3600))+':'+pad(Math.floor(s/60)%60)+':'+pad(s%60)+':'+pad(f%24);
  }
  if (!reduce) setInterval(function(){if(!document.hidden)tick();},250);

  /* ---------- split-flap opening titles ---------- */
  var GL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#/<>*+';
  function flapify(el){
    var out=[], kids=Array.prototype.slice.call(el.childNodes);
    kids.forEach(function(node){
      if (node.nodeType===3) {
        var frag=document.createDocumentFragment();
        Array.from(node.textContent).forEach(function(ch){
          if (/\s/.test(ch)) { frag.appendChild(document.createTextNode(ch)); return; }
          var s=document.createElement('span'); s.className='ch'; s.textContent=ch; s.setAttribute('aria-hidden','true');
          frag.appendChild(s); out.push({s:s,ch:ch});
        });
        node.parentNode.replaceChild(frag,node);
      } else if (node.nodeType===1) out = out.concat(flapify(node));
    });
    return out;
  }
  function scramble(el, delay){
    if (!el || reduce || el.dataset.done) return; el.dataset.done='1';
    var label = el.textContent.replace(/\s+/g,' ').trim();
    var chars = flapify(el);
    var sr=document.createElement('span'); sr.className='sr'; sr.textContent=label; el.insertBefore(sr, el.firstChild);
    chars.forEach(function(o){ o.w=o.s.getBoundingClientRect().width; o.s.style.width=o.w+'px'; });
    var start = performance.now()+ (delay||0);
    chars.forEach(function(o,i){ o.at = start + 220 + i*38 + Math.random()*180; });
    var last=0;
    function step(now){
      var live=false;
      if (now-last>55) {
        last=now;
        chars.forEach(function(o){
          if (now<start) return;
          if (now<o.at){ live=true; o.s.textContent=GL[(Math.random()*GL.length)|0]; o.s.classList.remove('f'); void o.s.offsetWidth; o.s.classList.add('f'); }
          else if (!o.fin){ o.fin=1; o.s.textContent=o.ch; o.s.classList.remove('f'); void o.s.offsetWidth; o.s.classList.add('f'); }
        });
      } else live=true;
      if (now<start) live=true;
      if (live) requestAnimationFrame(step);
      else chars.forEach(function(o){ o.s.style.width=''; });
    }
    requestAnimationFrame(step);
  }
  var fontsReady = (document.fonts && document.fonts.ready) ? Promise.race([document.fonts.ready, new Promise(function(r){setTimeout(r,1200)})]) : Promise.resolve();
  fontsReady.then(function(){
    var lns = document.querySelectorAll('h1.title .ln');
    scramble(lns[0], 0); scramble(lns[1], 260); scramble(lns[2], 520);
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting){ scramble(e.target,0); io.unobserve(e.target);} }); },{threshold:.6});
      document.querySelectorAll('.scr-t').forEach(function(el){ io.observe(el); });
    }
  });

  /* ---------- magnetic ticket ---------- */
  if (fine && !reduce) {
    document.addEventListener('pointermove', function(e){
      var m = e.target.closest && e.target.closest('.mag');
      if (m) { var r=m.getBoundingClientRect(); m.style.transform='translate('+((e.clientX-r.left-r.width/2)*.06)+'px,'+((e.clientY-r.top-r.height/2)*.18 - 3)+'px)'; }
    }, {passive:true});
    document.addEventListener('pointerout', function(e){ var m=e.target.closest && e.target.closest('.mag'); if(m && !m.contains(e.relatedTarget)) m.style.transform=''; });
  }

  /* ---------- WebGL smoke-of-light: the projected film ---------- */
  var scr = document.getElementById('screen');
  var cv = document.getElementById('smoke');
  var gl = null;
  var constrained=reduce || matchMedia('(pointer: coarse)').matches || Math.min(screen.width,screen.height)<560 || (navigator.deviceMemory && navigator.deviceMemory<=4) || (navigator.hardwareConcurrency && navigator.hardwareConcurrency<=4) || (navigator.connection && navigator.connection.saveData);
  if(constrained){ document.documentElement.classList.add('no-gl');window.__mbTier='static';return; }
  window.__mbTier = 'static';
  try { gl = cv.getContext('webgl', {antialias:false, alpha:false, depth:false, stencil:false, premultipliedAlpha:false, preserveDrawingBuffer:false, powerPreference:'high-performance'}); } catch(e) { gl = null; }
  if (!gl) { document.documentElement.classList.add('no-gl'); return; }

  /* ---------- GPU quality tiers: initial guess ---------- */
  function mq(q){ try { return !!(window.matchMedia && matchMedia(q).matches); } catch(e){ return false; } }
  var coarse = mq('(pointer: coarse)');
  var scrW = (window.screen && screen.width) || innerWidth, scrH = (window.screen && screen.height) || innerHeight;
  var phoneSize = Math.min(scrW, scrH) < 560;
  var desktop = fine && !coarse && !phoneSize;
  var cores = navigator.hardwareConcurrency || 4;
  var mem = navigator.deviceMemory || 0;
  var gpuRaw = '';
  try {
    gpuRaw = String(gl.getParameter(gl.RENDERER) || '');
    if (!gpuRaw || /^webkit/i.test(gpuRaw)) {
      var dbg = gl.getExtension('WEBGL_debug_renderer_info');
      if (dbg) gpuRaw = String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) || gpuRaw);
    }
  } catch(e) {}
  var SOFT = /swiftshader|llvmpipe|softpipe|lavapipe|basic render|software/i;
  var LOWG = /mali|adreno|powervr|videocore|tegra|intel(\(r\))?\s*(u?hd|gma)/i;
  var HIG = /RTX|GTX 16|GTX 10[7-8]|Radeon RX ?[5-9][0-9]{3}|Radeon Pro|Arc A7|Apple M[1-9] (Pro|Max|Ultra)/i;
  var veryWeak = SOFT.test(gpuRaw);
  if(veryWeak){document.documentElement.classList.add('no-gl');var release=gl.getExtension('WEBGL_lose_context');if(release)release.loseContext();return;}
  function guessTier(){
    if (coarse || phoneSize || (mem && mem <= 4) || cores <= 4 || veryWeak || LOWG.test(gpuRaw)) return 'lite';
    if (desktop && HIG.test(gpuRaw) && cores >= 8) return 'ultra';
    return 'high';
  }
  function gpuShort(s){
    var m;
    if (!s) return '';
    if ((m = s.match(/\b(RTX|GTX|RX)\s?([A-Z]?\d{3,4}[A-Z]?)(\s(Ti|SUPER|XTX|XT|GRE)\b)?/i))) return m[1].toUpperCase()+' '+m[2]+(m[4]?' '+m[4]:'');
    if ((m = s.match(/\bArc(\(TM\))?\s?(A\d{3}M?|B\d{3})/i))) return 'Arc '+m[2];
    if ((m = s.match(/Apple (M\d+( Pro| Max| Ultra)?|GPU)/i))) return 'Apple '+m[1];
    if ((m = s.match(/(Adreno|Mali)[\s(TM)-]*[\w-]*/i))) return m[0].replace(/\(TM\)/i,'').trim().slice(0,16);
    if ((m = s.match(/Iris\s?\w*|UHD\s?\d*|HD\s?\d+/i))) return 'Intel '+m[0].trim();
    if (SOFT.test(s)) return 'Software';
    if ((m = s.match(/Radeon[^,(]*/i))) return m[0].trim().slice(0,18);
    return '';
  }
  var gpuName = gpuShort(gpuRaw);

  var STORE = 'mbq-tier';
  function readPref(){ try { var v = localStorage.getItem(STORE) || ''; return /^(auto|ultra|high|lite)$/.test(v) ? v : 'auto'; } catch(e){ return 'auto'; } }
  function savePref(v){ try { localStorage.setItem(STORE, v); } catch(e){} }
  var mode = readPref();
  var autoTier = guessTier();
  var tier = mode === 'auto' ? autoTier : mode;
  if (reduce && tier === 'ultra') tier = 'high';
  /* high = the original look; lite = cheapest; ultra = full DPR, big sim, extra passes */
  function params(t){
    /* br = brush falloff (lower = wider stroke), ip = idle brush power, em = light emitters (cheap: sim pass only) */
    if (t === 'lite') return {cap:1, scale: veryWeak ? 0.42 : 0.5, sim: small ? 200 : 240, q:0, oct:3, dim: small ? 0.92 : 0.86, em: small ? 2 : 1, br: small ? 520 : 800, ip: small ? 0.24 : 0.16, bl: small ? 2.4 : 1.5};
    if (t === 'ultra') return {cap: (coarse || phoneSize) ? 2 : 3, scale:1, sim: (coarse || phoneSize) ? 512 : 768, q:2, oct:8, dim:0.9, em:3, br:1300, ip:0.10, bl:1};
    return {cap: small ? 1.5 : 2, scale: small ? 0.55 : 0.7, sim: small ? 300 : 460, q:1, oct: small ? 3 : 5, dim: small ? 0.86 : 0.85, em: small ? 2 : 0, br: small ? 700 : 1300, ip: small ? 0.18 : 0.10, bl: small ? 1.8 : 1};
  }
  var Q = params(tier);

  var HEAD = 'precision mediump float;\n#ifdef GL_FRAGMENT_PRECISION_HIGH\nprecision highp float;\n#endif\nvarying vec2 vUv;\n'+
    'vec2 hsh(vec2 p){p=vec2(dot(p,vec2(127.1,311.7)),dot(p,vec2(269.5,183.3)));return -1.0+2.0*fract(sin(p)*43758.5453);}\n'+
    'float nz(vec2 p){vec2 i=floor(p),f=fract(p);vec2 u=f*f*(3.0-2.0*f);'+
    'return mix(mix(dot(hsh(i),f),dot(hsh(i+vec2(1,0)),f-vec2(1,0)),u.x),mix(dot(hsh(i+vec2(0,1)),f-vec2(0,1)),dot(hsh(i+vec2(1,1)),f-vec2(1,1)),u.x),u.y);}\n';
  var VS = 'attribute vec2 p;varying vec2 vUv;void main(){vUv=p*0.5+0.5;gl_Position=vec4(p,0.0,1.0);}';
  var SIM = HEAD +
    'uniform sampler2D uPrev;uniform float uT;uniform vec2 uAsp;uniform vec2 uA;uniform vec2 uB;uniform vec2 uVel;uniform float uPow;uniform vec3 uCol;uniform float uQ;uniform float uNE;uniform float uBr;uniform vec4 uE[3];uniform vec4 uEC[3];\n'+
    'vec2 curl(vec2 p){float e=0.06;float a=nz(p+vec2(0.0,e)),b=nz(p-vec2(0.0,e)),c=nz(p+vec2(e,0.0)),d=nz(p-vec2(e,0.0));return vec2(a-b,-(c-d))/(2.0*e);}\n'+
    'void main(){vec2 p=vUv*uAsp;\n'+
    'vec2 v=curl(p*1.7+vec2(0.0,uT*0.05))*0.0017+curl(p*4.6-vec2(uT*0.08,0.0))*0.0007+vec2(0.0,0.0007);\n'+
    'if(uQ>1.5){v+=curl(p*9.5+vec2(uT*0.11,-uT*0.07))*0.0003;for(int k=0;k<3;k++){vec2 dq=(vUv-uE[k].xy)*uAsp;v+=uE[k].zw*exp(-dot(dq,dq)*420.0)*0.5;}}\n'+
    'vec2 pa=(vUv-uA)*uAsp,ba=(uB-uA)*uAsp;float h=clamp(dot(pa,ba)/max(dot(ba,ba),1e-6),0.0,1.0);vec2 dd=pa-ba*h;float d2=dot(dd,dd);\n'+
    'v+=uVel*exp(-d2*220.0)*0.55;\n'+
    'vec3 c=texture2D(uPrev,vUv-v/uAsp).rgb;\n'+
    'c=max(c*0.984-0.0022,0.0);\n'+
    'c+=uCol*uPow*exp(-d2*uBr);\n'+
    'if(uNE>0.5){float ew=uQ>1.5?2600.0:520.0;float eg=uQ>1.5?1.0:2.6;for(int k=0;k<3;k++){if(float(k)>=uNE)break;vec2 dq=(vUv-uE[k].xy)*uAsp;c+=uEC[k].rgb*uEC[k].a*eg*exp(-dot(dq,dq)*ew);}}\n'+
    'gl_FragColor=vec4(min(c,vec3(1.0)),1.0);}';
  var DISP = HEAD +
    'uniform sampler2D uDye;uniform float uT;uniform vec2 uAsp;uniform vec2 uRes;uniform float uQ;uniform int uOct;uniform float uDim;uniform float uBL;uniform vec2 uL;\n'+
    'float fbm(vec2 p){float s=0.0,a=0.5;for(int i=0;i<8;i++){if(i>=uOct)break;s+=a*nz(p);p=p*2.03+vec2(1.7,9.2);a*=0.5;}return s;}\n'+
    'void main(){vec2 p=vUv*uAsp;\n'+
    'vec2 q=vec2(fbm(p*1.2+uT*0.018),fbm(p*1.2+vec2(5.2,1.3)-uT*0.014));\n'+
    'float n;\n'+
    'if(uQ>1.5){vec2 r=vec2(fbm(p*1.3+3.0*q+vec2(1.7,9.2)+uT*0.012),fbm(p*1.3+3.0*q+vec2(8.3,2.8)-uT*0.010));n=fbm(p*1.5+2.2*r);}else{n=fbm(p*1.5+2.2*q);}\n'+
    'vec3 base=mix(vec3(0.008,0.010,0.028),vec3(0.055,0.03,0.12),smoothstep(-0.25,0.55,n));\n'+
    'base+=vec3(0.0,0.10,0.14)*smoothstep(0.3,0.85,n)*0.7+vec3(0.16,0.03,0.09)*smoothstep(0.2,0.8,q.x)*0.35;\n'+
    'if(uQ>1.5){float fil=smoothstep(0.42,0.95,n);base+=vec3(0.12,0.06,0.20)*fil*fil*0.9+vec3(0.0,0.09,0.12)*smoothstep(0.55,1.0,q.y)*0.5;}\n'+
    'vec3 dye;\n'+
    'if(uQ>1.5){vec2 ca=(vUv-0.5)*0.007;dye=vec3(texture2D(uDye,vUv+ca).r,texture2D(uDye,vUv).g,texture2D(uDye,vUv-ca).b);}else{dye=texture2D(uDye,vUv).rgb;}\n'+
    'vec3 glow=vec3(0.0);\n'+
    'if(uQ<0.5){for(int i=0;i<4;i++){float a=float(i)*1.570796+0.785398;glow+=texture2D(uDye,vUv+vec2(cos(a),sin(a))*0.03/uAsp).rgb;}glow/=4.0;}\n'+
    'else{for(int i=0;i<8;i++){float a=float(i)*0.785398;glow+=texture2D(uDye,vUv+vec2(cos(a),sin(a))*0.03/uAsp).rgb;}glow/=8.0;}\n'+
    'vec3 col=base*uBL+dye*1.15+glow*0.6;\n'+
    'if(uQ>0.5){vec3 st=vec3(0.0);for(int i=-6;i<=6;i++){float w=1.0-abs(float(i))/7.0;st+=texture2D(uDye,vUv+vec2(float(i)*0.03,0.0)).rgb*w;}\n'+
    'col+=vec3(dot(st,vec3(0.33)))*vec3(0.35,0.65,1.0)*0.07;}\n'+
    'if(uQ>1.5){\n'+
    ' vec3 g2=vec3(0.0);for(int i=0;i<12;i++){float a=float(i)*0.523599+0.2618;g2+=texture2D(uDye,vUv+vec2(cos(a),sin(a))*0.075/uAsp).rgb;}col+=g2*(0.5/12.0);\n'+
    ' vec3 s2=vec3(0.0);for(int i=-10;i<=10;i++){float w=1.0-abs(float(i))/11.0;s2+=texture2D(uDye,vUv+vec2(float(i)*0.06,0.0)).rgb*w*w;}col+=vec3(dot(s2,vec3(0.33)))*vec3(0.3,0.6,1.0)*0.045;\n'+
    ' vec2 dl=(vUv-uL)*(0.9/32.0);vec2 tc=vUv;float il=1.0;vec3 gr=vec3(0.0);\n'+
    ' for(int i=0;i<32;i++){tc-=dl;gr+=texture2D(uDye,tc).rgb*il;il*=0.94;}\n'+
    ' col+=gr*vec3(1.0,0.92,0.8)*0.05;\n'+
    '}\n'+
    'col=1.0-exp(-col*1.55);\n'+
    'float vg=smoothstep(1.25,0.25,length((vUv-0.5)*vec2(uAsp.x*0.9,1.1)));col*=mix(0.4,1.0,vg);\n'+
    'float g=fract(sin(dot(floor(vUv*uRes)+fract(uT*7.0)*91.0,vec2(12.9898,78.233)))*43758.5453);col+=(g-0.5)*0.05;\n'+
    'col=col*uDim;\n'+
    'gl_FragColor=vec4(col,1.0);}';

  function sh(type, src){ var s=gl.createShader(type); gl.shaderSource(s,src); gl.compileShader(s); if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
  function prog(fs){ var p=gl.createProgram(); gl.attachShader(p,sh(gl.VERTEX_SHADER,VS)); gl.attachShader(p,sh(gl.FRAGMENT_SHADER,fs)); gl.bindAttribLocation(p,0,'p'); gl.linkProgram(p); if(!gl.getProgramParameter(p,gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p)); var u={}; var n=gl.getProgramParameter(p,gl.ACTIVE_UNIFORMS); for(var i=0;i<n;i++){var a=gl.getActiveUniform(p,i); var loc=gl.getUniformLocation(p,a.name); u[a.name]=loc; u[a.name.replace(/\[0\]$/,'')]=loc;} return {p:p,u:u}; }
  var simP, dispP;
  try { simP = prog(SIM); dispP = prog(DISP); }
  catch(err){ document.documentElement.classList.add('no-gl'); return; }
  function U(pr, name){ return pr.u[name] || null; }

  var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);

  var fbs=[], simW=0, simH=0, W=0, H=0, asp=1;
  function mkFB(w,h){
    var t=gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D,t);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,w,h,0,gl.RGBA,gl.UNSIGNED_BYTE,null);
    var f=gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER,f); gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,t,0);
    gl.clearColor(0,0,0,1); gl.clear(gl.COLOR_BUFFER_BIT);
    return {t:t,f:f};
  }
  var lastVW=0, lastVH=0;
  function resize(force){
    var vw=scr.clientWidth||innerWidth, vh=scr.clientHeight||innerHeight;
    if (!force && vw===lastVW && vh===lastVH) return;
    lastVW=vw; lastVH=vh;
    var dpr = Math.min(window.devicePixelRatio||1, Q.cap) * Q.scale;
    W = Math.max(2, Math.round(vw*dpr)); H = Math.max(2, Math.round(vh*dpr));
    cv.width=W; cv.height=H; asp = vw/vh;
    var long = Q.sim;
    var nw = asp>=1 ? long : Math.round(long*asp), nh = asp>=1 ? Math.round(long/asp) : long;
    if (nw!==simW || nh!==simH) {
      fbs.forEach(function(b){ gl.deleteTexture(b.t); gl.deleteFramebuffer(b.f); });
      simW=nw; simH=nh; fbs=[mkFB(simW,simH), mkFB(simW,simH)];
    }
  }
  resize(true);
  addEventListener('resize', function(){
    var pw=lastVW, ph=lastVH; resize(false);
    /* resizing clears the canvas; with reduced motion no RAF loop repaints it, so re-render the still */
    if (reduce && (pw!==lastVW || ph!==lastVH)) { clearTimeout(stillT); renderStill(); stillT=setTimeout(renderStill,150); }
  }, {passive:true});

  var ptr={x:.5,y:.5,lx:.5,ly:.5,last:-1e9,boost:0};
  function onMove(x,y){ var r=scr.getBoundingClientRect(); if (x<r.left||x>r.right||y<r.top||y>r.bottom) return false; ptr.x=(x-r.left)/r.width; ptr.y=1-(y-r.top)/r.height; ptr.last=performance.now(); return true; }
  addEventListener('pointermove', function(e){ onMove(e.clientX,e.clientY); }, {passive:true});
  addEventListener('pointerdown', function(e){ if (onMove(e.clientX,e.clientY)) { ptr.lx=ptr.x; ptr.ly=ptr.y; ptr.boost=1; } }, {passive:true});
  addEventListener('touchmove', function(e){ var t=e.touches[0]; if(t) onMove(t.clientX,t.clientY); }, {passive:true});

  var pal=[[.37,.95,1.0],[1.0,.31,.66],[1.0,.75,.35],[.72,.64,1.0]];
  function colAt(t){ var k=t*0.18, i=Math.floor(k)%pal.length, j=(i+1)%pal.length, f=k-Math.floor(k); f=f*f*(3-2*f); return [pal[i][0]+(pal[j][0]-pal[i][0])*f, pal[i][1]+(pal[j][1]-pal[i][1])*f, pal[i][2]+(pal[j][2]-pal[i][2])*f]; }

  /* ultra-only: three satellite "spotlights" that lay extra light trails */
  var emP=[null,null,null], emA=new Float32Array(12), emC=new Float32Array(12);
  function emitters(t){
    for (var k=0;k<3;k++){
      var ph=k*2.0944, sp=.19+.06*k;
      var x=.5+.40*Math.sin(t*sp+ph)+.07*Math.sin(t*1.13+k*1.7);
      var y=.52+.33*Math.cos(t*(sp*1.37)+ph*1.3)+.06*Math.sin(t*.91+k);
      var o=emP[k]||{x:x,y:y};
      emA[k*4]=x; emA[k*4+1]=y;
      emA[k*4+2]=Math.max(-.03,Math.min(.03,x-o.x))*.9; emA[k*4+3]=Math.max(-.03,Math.min(.03,y-o.y))*.9;
      emP[k]={x:x,y:y};
      var c=colAt(t+(k+1)*5.6);
      emC[k*4]=c[0]*.5; emC[k*4+1]=c[1]*.5; emC[k*4+2]=c[2]*.5; emC[k*4+3]=.30+.12*Math.sin(t*1.7+k*2.1);
    }
  }

  var cur=0, startT=performance.now(), running=false, raf=0, ghostP={x:.5,y:.5};
  function frame(now, fixedT){
    var t = fixedT!=null ? fixedT : Math.max(0,(now-startT)/1000);
    var idle = (now - ptr.last) > 1600;
    var tx, ty;
    if (idle) {
      tx = .5 + .30*Math.sin(t*.41) + .10*Math.sin(t*1.27+1.3);
      ty = .56 + .22*Math.sin(t*.57+.7) + .07*Math.cos(t*1.61);
      if (small) { tx = .5 + .34*Math.sin(t*.47) + .08*Math.sin(t*1.3); ty = .62 + .2*Math.sin(t*.6+.4); }
      ghostP.x += (tx-ghostP.x)*.5; ghostP.y += (ty-ghostP.y)*.5;
      tx=ghostP.x; ty=ghostP.y;
    } else { tx=ptr.x; ty=ptr.y; ghostP.x=tx; ghostP.y=ty; }
    var vx = tx-ptr.lx, vy = ty-ptr.ly;
    var sp = Math.sqrt(vx*vx*asp*asp+vy*vy);
    var pow = Math.min(1, (idle?Q.ip:0.06) + sp*(idle?14:22) + ptr.boost);
    ptr.boost *= .9;
    var c = colAt(t);
    if (Q.em) emitters(t);

    var a = fbs[cur], b = fbs[1-cur];
    gl.bindFramebuffer(gl.FRAMEBUFFER, b.f); gl.viewport(0,0,simW,simH);
    gl.useProgram(simP.p);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, a.t);
    gl.uniform1i(U(simP,'uPrev'),0); gl.uniform1f(U(simP,'uT'),t);
    gl.uniform2f(U(simP,'uAsp'),asp,1); gl.uniform2f(U(simP,'uA'),ptr.lx,ptr.ly); gl.uniform2f(U(simP,'uB'),tx,ty);
    gl.uniform2f(U(simP,'uVel'), Math.max(-.05,Math.min(.05,vx))*.9, Math.max(-.05,Math.min(.05,vy))*.9);
    gl.uniform1f(U(simP,'uPow'),pow); gl.uniform3f(U(simP,'uCol'),c[0]*.55,c[1]*.55,c[2]*.55);
    gl.uniform1f(U(simP,'uQ'),Q.q); gl.uniform1f(U(simP,'uNE'),Q.em); gl.uniform1f(U(simP,'uBr'),Q.br);
    if (Q.em) { gl.uniform4fv(U(simP,'uE'),emA); gl.uniform4fv(U(simP,'uEC'),emC); }
    gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
    cur = 1-cur;
    ptr.lx=tx; ptr.ly=ty;

    gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0,0,W,H);
    gl.useProgram(dispP.p);
    gl.bindTexture(gl.TEXTURE_2D, b.t);
    gl.uniform1i(U(dispP,'uDye'),0); gl.uniform1f(U(dispP,'uT'),t);
    gl.uniform2f(U(dispP,'uAsp'),asp,1); gl.uniform2f(U(dispP,'uRes'),W,H);
    gl.uniform1f(U(dispP,'uQ'),Q.q); gl.uniform1i(U(dispP,'uOct'),Q.oct); gl.uniform1f(U(dispP,'uDim'),Q.dim); gl.uniform1f(U(dispP,'uBL'),Q.bl);
    gl.uniform2f(U(dispP,'uL'), .78+.06*Math.sin(t*.13), 1.02+.04*Math.sin(t*.29));
    gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
  }

  /* ---------- runtime FPS sampler + tier switching ---------- */
  var S={last:0,warm:0,ws:0,ts:[],ups:0,downed:false,lastChange:0,fps:0};
  function applyTier(t){
    tier=t; Q=params(t); window.__mbTier=t;
    emP=[null,null,null];
    resize(true);
    S.lastChange=performance.now(); S.last=0; S.ts=[]; S.ws=0; S.ups=0;
    updateChip();
  }
  function sample(now){
    if (!S.last) { S.last=now; S.warm=now+1500; S.ws=0; S.ts=[]; return; }
    var dt=now-S.last; S.last=now;
    if (dt>250) { S.warm=now+500; S.ws=0; S.ts=[]; return; }
    if (now<S.warm) return;
    if (!S.ws) { S.ws=now; return; }
    S.ts.push(dt);
    if (now-S.ws<2000) return;
    var n=S.ts.length, sum=0, i;
    for (i=0;i<n;i++) sum+=S.ts[i];
    var srt=S.ts.slice().sort(function(x,y){return x-y;});
    var p90=srt[Math.min(n-1, Math.floor(n*.9))];
    S.ts=[]; S.ws=now;
    S.fps=Math.round(1000*n/sum); window.__mbFps=S.fps;
    if (mode==='auto' && now-S.lastChange>=3000) {
      if (S.fps<45 && tier!=='lite') { S.downed=true; applyTier(tier==='ultra'?'high':'lite'); return; }
      if (tier==='high' && desktop && !S.downed && S.fps>=58 && p90<12) {
        if (++S.ups>=2) { applyTier('ultra'); return; }
      } else S.ups=0;
    }
    updateChip();
  }

  // Adaptive rendering stays internal; visitors only need the downloads.
  var chip=null;function updateChip(){}
  var painted=0;
  function loop(now){ if(!running) return; if(now-painted>=1000/60){painted=now;frame(now);sample(now);} raf=requestAnimationFrame(loop); }
  var sync = null, stillT = 0;
  function renderStill(){ if (gl.isContextLost()) return; var n0=performance.now(); ghostP={x:.5,y:.5}; ptr.lx=.5; ptr.ly=.5; emP=[null,null,null]; for (var i=0;i<140;i++) frame(n0, i/30); }
  function start(){ if(running||reduce) return; running=true; S.last=0; raf=requestAnimationFrame(loop); }
  function stop(){ running=false; cancelAnimationFrame(raf); }

  if (reduce) {
    /* still render: run the sim quickly offscreen, then hold one frame */
    renderStill();
  } else {
    /* only project while the screen is in view */
    var onScr = true;
    sync = function(){ if (onScr && !document.hidden && !gl.isContextLost()) start(); else stop(); };
    if ('IntersectionObserver' in window) new IntersectionObserver(function(es){ onScr = es[es.length-1].isIntersecting; sync(); }).observe(scr);
    start();
    document.addEventListener('visibilitychange', sync);
  }
  cv.addEventListener('webglcontextlost', function(e){ e.preventDefault(); stop(); document.documentElement.classList.add('no-gl'); window.__mbTier='static'; });
  cv.addEventListener('webglcontextrestored', function(){
    try {
      simP = prog(SIM); dispP = prog(DISP);
      buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
      gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
      fbs=[]; simW=0; simH=0; resize(true);
      document.documentElement.classList.remove('no-gl'); window.__mbTier=tier;
      if (reduce) renderStill(); else if (sync) sync(); else start();
    } catch(err) {}
  });
})();
