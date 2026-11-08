// Bump when SHELL changes so old caches are cleared.
const SHELL_CACHE = 'shell-v7';
const SPRITE_CACHE = 'sprites-v1';
const SPRITE_HOST = 'raw.githubusercontent.com';

const SHELL = [
  './',
  'index.html',
  'css/style.css',
  'js/db.js',
  'js/api.js',
  'js/ui.js',
  'js/names.js',
  'js/sync.js',
  'js/app.js',
  'data/exclusives.json',
  'data/best-catch.json',
  'data/best-sets.json',
  'manifest.webmanifest',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/maskable-512.png',
  'icons/apple-touch-icon.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL_CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  const keep = [SHELL_CACHE, SPRITE_CACHE];
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => !keep.includes(k)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  if (url.origin === location.origin) e.respondWith(networkFirst(req));
  else if (url.host === SPRITE_HOST) e.respondWith(cacheFirst(req));
  // everything else (PokéAPI, GitHub API) goes straight to the network
});

// App files: always fresh when online, cached copy when offline.
async function networkFirst(req) {
  const cache = await caches.open(SHELL_CACHE);
  try {
    // no-cache = ask the server if the file changed (navigations can't take options)
    const res = await (req.mode === 'navigate' ? fetch(req) : fetch(req, { cache: 'no-cache' }));
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch {
    return (await cache.match(req, { ignoreSearch: true })) || Response.error();
  }
}

// Sprites never change: cache once, then serve from cache.
async function cacheFirst(req) {
  const cache = await caches.open(SPRITE_CACHE);
  const hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok) cache.put(req, res.clone());
  return res;
}
