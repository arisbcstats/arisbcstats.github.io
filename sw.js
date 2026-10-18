// Aris BC Stats: network-first για τη σελίδα (πάντα τα πιο φρέσκα δεδομένα), cache για εικονίδια· λειτουργεί και χωρίς ίντερνετ.
const C='aris-v1';
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(['./','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png'])));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{const r=e.request; if(r.method!=='GET') return; const u=new URL(r.url);
  if(u.origin===location.origin){ e.respondWith(fetch(r).then(res=>{const cp=res.clone(); caches.open(C).then(c=>c.put(r,cp)); return res;}).catch(()=>caches.match(r).then(m=>m||caches.match('./')))); }
  else if(u.hostname.endsWith('gstatic.com')||u.hostname.endsWith('googleapis.com')){ e.respondWith(caches.match(r).then(m=>m||fetch(r).then(res=>{const cp=res.clone(); caches.open(C).then(c=>c.put(r,cp)); return res;}))); }
});
