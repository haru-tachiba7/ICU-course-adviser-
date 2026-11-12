// 端末間の同期(アカウントなし・端末側で暗号化)。同期コード+パスフレーズから鍵と合言葉を作る。
(function () {
  'use strict';
  const META = 'icu_sync_meta', te = new TextEncoder(), td = new TextDecoder();
  const _set = Storage.prototype.setItem;
  const b64 = a => { let s = ''; new Uint8Array(a).forEach(x => s += String.fromCharCode(x)); return btoa(s); };
  const ub64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
  const hex = a => [...new Uint8Array(a)].map(x => x.toString(16).padStart(2, '0')).join('');
  const isData = k => k.startsWith('icu_planner_') || k.startsWith('icu_tt_');
  let meta = null, applying = false, timer = null, state = '';
  try { meta = JSON.parse(localStorage.getItem(META)); } catch (e) {}
  const saveMeta = () => _set.call(localStorage, META, JSON.stringify(meta));
  function setState(m) { state = m; const e = document.getElementById('sync-st'); if (e) e.textContent = m; }

  async function derive(id, pass) {
    const k = await crypto.subtle.importKey('raw', te.encode(pass), 'PBKDF2', false, ['deriveBits']);
    const b = new Uint8Array(await crypto.subtle.deriveBits({ name: 'PBKDF2', salt: te.encode('icu-sync-v1:' + id), iterations: 300000, hash: 'SHA-256' }, k, 512));
    return { key: b64(b.slice(0, 32)), token: hex(b.slice(32)) };  // 前半=暗号鍵(端末内のみ)、後半=サーバー用の合言葉
  }
  const ck = () => crypto.subtle.importKey('raw', ub64(meta.key), 'AES-GCM', false, ['encrypt', 'decrypt']);
  async function enc(obj) {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, await ck(), te.encode(JSON.stringify(obj)));
    return { iv: b64(iv), ct: b64(ct) };
  }
  async function dec(d) { return JSON.parse(td.decode(await crypto.subtle.decrypt({ name: 'AES-GCM', iv: ub64(d.iv) }, await ck(), ub64(d.ct)))); }
  const api = (m, body) => fetch('/api/sync/' + meta.id, { method: m, headers: { 'X-Token': meta.token, 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  function snap() { const o = {}; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (isData(k)) o[k] = localStorage.getItem(k); } return o; }

  async function applyRemote(j) {
    const o = await dec(j.data); applying = true;
    try {
      const del = []; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (isData(k)) del.push(k); }
      del.forEach(k => localStorage.removeItem(k));
      Object.entries(o.d).forEach(([k, v]) => { if (isData(k)) _set.call(localStorage, k, v); });
    } finally { applying = false; }
    meta.updated = j.updated; meta.dirty = false; saveMeta(); location.reload();
  }
  async function push(force) {
    const r = await api('PUT', { data: await enc({ d: snap() }), prev: force ? '*' : meta.updated });
    if (r.status === 409) {
      const j = await r.json();
      if (confirm('別の端末でデータが更新されています。\nOK: クラウドの内容を読み込む\nキャンセル: この端末の内容で上書き保存')) return applyRemote(j);
      return push(true);
    }
    if (!r.ok) { setState('保存に失敗しました (' + r.status + ')'); return; }
    meta.updated = (await r.json()).updated; meta.dirty = false; saveMeta(); setState('同期済み');
  }
  async function pull() {
    if (!meta) return;
    try {
      const r = await api('GET');
      if (r.status === 404) return push(true);
      if (!r.ok) { setState('同期できません (' + r.status + ')'); return; }
      const j = await r.json();
      if (j.updated === meta.updated) return meta.dirty ? push() : setState('同期済み');
      if (!meta.dirty || confirm('この端末とクラウドの両方で変更があります。\nOK: クラウドの内容を読み込む\nキャンセル: この端末の内容で上書き')) return applyRemote(j);
      return push(true);
    } catch (e) { setState('同期できません(通信を確認してください)'); }
  }
  async function start(pass) {
    if (pass.length < 12) throw new Error('パスフレーズは12文字以上にしてください');
    const id = b64(crypto.getRandomValues(new Uint8Array(16))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    const d = await derive(id, pass); meta = { id, key: d.key, token: d.token, updated: null, dirty: false }; saveMeta();
    await push(true); return id;
  }
  async function join(id, pass) {
    id = id.trim(); const d = await derive(id, pass), prev = meta;
    meta = { id, key: d.key, token: d.token, updated: null, dirty: false };
    try {
      const r = await api('GET');
      if (r.status === 404) throw new Error('その同期コードのデータが見つかりません');
      if (!r.ok) throw new Error('パスフレーズが違うか、アクセスできません');
      const j = await r.json();
      try { await dec(j.data); } catch (e) { throw new Error('パスフレーズが違います'); }
      saveMeta(); await applyRemote(j);
    } catch (e) { meta = prev; throw e; }
  }
  async function wipe() { await api('DELETE'); disconnect(); }
  function disconnect() { localStorage.removeItem(META); meta = null; }

  const _s = Storage.prototype.setItem;
  Storage.prototype.setItem = function (k, v) {
    _s.call(this, k, v);
    if (this === localStorage && meta && !applying && isData(k)) {
      meta.dirty = true; saveMeta(); clearTimeout(timer);
      timer = setTimeout(() => push().catch(() => setState('保存に失敗しました')), 4000);
    }
  };
  window.icuSync = { start, join, push, pull, wipe, disconnect, get meta() { return meta; } };

  // ---- 画面(右下の「同期」ボタン) ----
  function ui() {
    const css = document.createElement('style');
    css.textContent = '#sync-p input{width:100%;margin:4px 0;padding:6px;font:inherit;background:var(--panel,#eee);color:inherit;border:1px solid var(--border,#ccc);border-radius:3px}#sync-p button,#sync-btn{margin:4px 4px 0 0;padding:6px 12px;font:inherit;cursor:pointer;background:var(--panel,#eee);color:inherit;border:1px solid var(--border,#ccc);border-radius:3px}#sync-p small{color:var(--ink-muted,#666)}#sync-p hr{border:0;border-top:1px solid var(--border,#ccc);margin:10px 0}';
    document.head.appendChild(css);
    const b = document.createElement('button'); b.id = 'sync-btn'; b.textContent = '☁ 同期';
    b.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:60;font-size:13px;color:var(--ink,#111)';
    const p = document.createElement('div'); p.id = 'sync-p';
    p.style.cssText = 'display:none;position:fixed;right:16px;bottom:60px;z-index:60;width:min(340px,92vw);padding:14px;background:var(--bg,#fff);color:var(--ink,#111);border:1px solid var(--border,#ccc);box-shadow:0 8px 24px rgba(0,0,0,.3);font:13px/1.55 var(--sans,sans-serif)';
    const $ = i => p.querySelector('#' + i), msg = t => { $('smsg').textContent = t; };
    function draw() {
      if (!meta) {
        p.innerHTML = '<b>端末間でデータを同期</b><p><small>データはこの端末で暗号化されてから保存されます。パスフレーズは運営側にも分からず、忘れると復元できません。</small></p><div>新しく始める<input id="sp1" type="password" placeholder="パスフレーズ(12文字以上・長い文章がおすすめ)"><button id="sgo">始める</button></div><hr><div>別の端末と接続<input id="sid" placeholder="同期コード"><input id="sp2" type="password" placeholder="パスフレーズ"><button id="sjoin">接続</button></div><div id="smsg" class="warn" style="color:#9C4530;margin-top:6px"></div>';
        $('sgo').onclick = async () => { msg('処理中…'); try { await start($('sp1').value); draw(); } catch (e) { msg(e.message); } };
        $('sjoin').onclick = async () => { msg('処理中…'); try { await join($('sid').value, $('sp2').value); } catch (e) { msg(e.message); } };
      } else {
        p.innerHTML = '<b>同期中</b><p>同期コード(他の端末で入力。必ず控えてください)<input id="scode" readonly value="' + meta.id + '"></p><div>状態: <span id="sync-st">' + (state || '') + '</span></div><button id="snow">今すぐ同期</button><button id="soff">この端末の同期を解除</button><button id="sdel">クラウドのデータを削除</button><div id="smsg" style="color:#9C4530;margin-top:6px"></div>';
        $('scode').onclick = e => e.target.select();
        $('snow').onclick = () => { setState('同期中…'); pull(); };
        $('soff').onclick = () => { if (confirm('この端末の同期を解除します(クラウドのデータは残ります)。')) { disconnect(); draw(); } };
        $('sdel').onclick = async () => { if (confirm('クラウドのデータを削除します。他の端末の同期も止まります。')) { try { await wipe(); draw(); } catch (e) { msg('削除に失敗しました'); } } };
      }
    }
    b.onclick = () => { p.style.display = p.style.display === 'none' ? 'block' : 'none'; draw(); };
    document.body.appendChild(p); document.body.appendChild(b);
  }
  document.addEventListener('DOMContentLoaded', () => { ui(); pull(); });
  document.addEventListener('visibilitychange', () => { if (!document.hidden && meta && !meta.dirty) pull(); });
})();
