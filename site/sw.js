const CACHE = 'ea-equipment-v119';
const SHELL = ['./', './index.html', './data.js', './manifest.json', './icon-192.png', './icon-512.png', './install-guide.pdf', './images/app-qr.png', './images/install-guide.jpg'];
// Hosted rulebook PDFs (site/docs/) are fetched by the page's top-up loop
// after activation rather than during install, so install stays fast and
// activation (offline capability) is never delayed behind large downloads.

// Derive the full image list from the data file so everything is available
// offline after install (importScripts is synchronous in the SW scope).
let IMAGES = [];
try {
  importScripts('./data.js');
  const s = new Set();
  (EA_DATA.items || []).forEach(i => (i.images || []).forEach(f => s.add('./images/' + f)));
  (EA_DATA.rules || []).forEach(r => (r.images || []).forEach(o => s.add('./images/' + (o.src || o))));
  (EA_DATA.galleries || []).forEach(g => (g.images || []).forEach(o => s.add('./images/' + (o.src || o))));
  if (EA_DATA.policy && EA_DATA.policy.images) EA_DATA.policy.images.forEach(o => s.add('./images/' + (o.src || o)));
  IMAGES = [...s];
} catch (e) { /* shell precache still works; images fall back to on-demand caching */ }

// Cloudflare 307-redirects /index.html to /, and a cached redirect-tainted
// response is rejected for app-launch navigations — store shell entries as
// clean 200s so offline launches always work.
async function cleanPut(c, u){
  const res = await fetch(u);
  if(!res.ok) throw new Error('precache failed: ' + u);
  if(res.redirected){
    const b = await res.blob();
    return c.put(u, new Response(b, {status: 200, headers: res.headers}));
  }
  return c.put(u, res);
}
function unpoison(res, req){
  if(res && res.redirected && req.mode === 'navigate'){
    return res.blob().then(b => new Response(b, {status: 200, headers: res.headers}));
  }
  return res;
}
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c =>
    // Shell must succeed; images are best-effort so one bad file can't block install
    Promise.all(SHELL.map(u => cleanPut(c, u))).then(() => Promise.allSettled(IMAGES.map(u => c.add(u))))
  ).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});
// Cache-first for images; network-first for the shell so content edits propagate
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return; // analytics beacon POSTs etc. go straight to network
  const url = new URL(e.request.url);
  if (url.pathname.includes('/images/')) {
    e.respondWith(
      caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
        return res;
      }))
    );
  } else {
    e.respondWith(
      fetch(e.request).then(res => {
        // only cache good responses — never redirects or error pages
        if (res.ok && !res.redirected) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
        return res;
      }).catch(() => caches.match(e.request).then(hit =>
        // offline app launch must never dead-end: any navigation falls back
        // to the cached shell, with redirect taint stripped
        hit ? unpoison(hit, e.request)
            : (e.request.mode === 'navigate'
              ? caches.match('./index.html', {ignoreSearch: true}).then(h => h && unpoison(h, e.request))
              : undefined)
      ))
    );
  }
});
