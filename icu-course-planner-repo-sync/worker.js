// 暗号化データの保存だけを行うAPI。サーバーは中身を読めない(復号の鍵は端末側にしかない)。
const J = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
const sha = async s => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join('');

export default {
  async fetch(req, env) {
    const u = new URL(req.url), m = /^\/api\/sync\/([A-Za-z0-9_-]{22,64})$/.exec(u.pathname);
    if (!m) return u.pathname.startsWith('/api/') ? J({ error: 'not found' }, 404) : env.ASSETS.fetch(req);
    const tok = req.headers.get('X-Token') || '';
    if (!/^[0-9a-f]{64}$/.test(tok)) return J({ error: 'bad token' }, 401);
    const key = 's:' + m[1], h = await sha(tok), cur = await env.SYNC.get(key, 'json');
    if (req.method === 'GET') {
      if (!cur) return J({ error: 'not found' }, 404);
      if (cur.h !== h) return J({ error: 'forbidden' }, 403);
      return J({ data: cur.data, updated: cur.updated });
    }
    if (req.method === 'PUT') {
      const raw = await req.text();
      if (raw.length > 400000) return J({ error: 'too large' }, 413);
      let b; try { b = JSON.parse(raw); } catch { return J({ error: 'bad json' }, 400); }
      if (!b.data || typeof b.data.iv !== 'string' || typeof b.data.ct !== 'string') return J({ error: 'bad data' }, 400);
      if (cur && cur.h !== h) return J({ error: 'forbidden' }, 403);
      if (cur && b.prev !== '*' && b.prev !== cur.updated) return J({ error: 'conflict', data: cur.data, updated: cur.updated }, 409);
      const updated = Date.now();
      await env.SYNC.put(key, JSON.stringify({ h, data: b.data, updated }));
      return J({ updated });
    }
    if (req.method === 'DELETE') {
      if (!cur) return J({ ok: true });
      if (cur.h !== h) return J({ error: 'forbidden' }, 403);
      await env.SYNC.delete(key);
      return J({ ok: true });
    }
    return J({ error: 'method not allowed' }, 405);
  }
};
