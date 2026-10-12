// Jason Stys: deliberately network-only service worker. Never cache private API responses or credentials.
// Installation gives standalone browser UI; offline login/sync are intentionally unavailable.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
