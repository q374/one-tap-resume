const API = {
    async get(url) {
        const r = await fetch(url);
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
    },
    async upload(url, file) {
        const fd = new FormData();
        fd.append('file', file);
        const r = await fetch(url, {method: 'POST', body: fd});
        if (!r.ok) {
            let msg = r.statusText;
            try { const j = await r.json(); msg = j.detail || j.error || msg; } catch(e) {}
            throw new Error(msg);
        }
        return r.json();
    },
    async post(url, data) {
        const r = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
    },
    async put(url, data) {
        const r = await fetch(url, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
    },
    async del(url) {
        const r = await fetch(url, {method: 'DELETE'});
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
    }
};
