const CACHE = 'ea-equipment-v92';
const SHELL = ['./', './index.html', './data.js', './manifest.json', './icon-192.png', './icon-512.png', './install-guide.pdf', './images/app-qr.png', './images/install-guide.jpg'];

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

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c =>
    // Shell must succeed; images are best-effort so one bad file can't block install
    c.addAll(SHELL).then(() => Promise.allSettled(IMAGES.map(u => c.add(u))))
  ).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});
// Cache-first for images; network-first for the shell so content edits propagate
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.pathname.includes('/images/')) {
    e.respondWith(
      caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return res;
      }))
    );
  } else {
    e.respondWith(
      fetch(e.request).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return res;
      }).catch(() => caches.match(e.request))
    );
  }
});
