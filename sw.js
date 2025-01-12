self.addEventListener('fetch', event => {
    event.respondWith(
        caches.open('cache').then(cache => {
            return fetch(event.request).then(response => {
                cache.put(event.request, response.clone());
                return response;
            }).catch(() => {
                return caches.match(event.request).then(response => {
                    return response || new Response('No internet connection', { status: 503, statusText: 'Service Unavailable' });
                });
            });
        })
    );
});
