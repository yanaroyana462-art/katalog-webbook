p = 'index.html'
s = open(p, encoding='utf-8').read()

start = s.index('<!-- Tombol & Modal Beri Akses (khusus admin) -->')
end = s.rindex('</body>')

new = '''<!-- Tombol & Modal Beri Akses (khusus admin) -->
<button x-show="isAdmin" style="display:none;position:fixed;left:16px;bottom:16px;z-index:60;background:#059669;color:#fff;border:0;border-radius:9999px;padding:10px 16px;font-size:13px;font-weight:600;box-shadow:0 4px 14px rgba(0,0,0,.3);cursor:pointer"
  @click="openGrantModal()">🔑 Beri Akses</button>

<div x-show="isGrantModalOpen && isAdmin" style="display:none;position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.55);align-items:center;justify-content:center;padding:16px"
  :style="isGrantModalOpen && isAdmin ? 'display:flex' : 'display:none'"
  @click.self="closeGrantModal()" @keydown.escape.window="closeGrantModal()">
  <div style="width:100%;max-width:420px;background:#fff;color:#0f172a;border-radius:16px;padding:24px;box-shadow:0 20px 50px rgba(0,0,0,.35)">
    <h3 style="margin:0;font-size:18px;font-weight:700">Beri Akses Buku Berbayar</h3>
    <p style="margin:4px 0 0;font-size:13px;color:#64748b">Isi setelah pembayaran pembeli Anda verifikasi.</p>

    <label style="display:block;margin-top:16px;font-size:13px;font-weight:600">Email pembeli</label>
    <input type="email" x-model="grantEmail" placeholder="email.pembeli@gmail.com"
      style="margin-top:4px;width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:14px;background:#fff;color:#0f172a">

    <label style="display:block;margin-top:16px;font-size:13px;font-weight:600">Buku yang dibeli</label>
    <select x-model="grantBookId"
      style="margin-top:4px;width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:14px;background:#fff;color:#0f172a">
      <option value="">-- Pilih buku berbayar --</option>
      <template x-for="b in paidBooks" :key="b.id">
        <option :value="b.id" x-text="b.title"></option>
      </template>
    </select>

    <p x-show="grantResult" x-text="grantResult" style="display:none;margin:16px 0 0;background:#f1f5f9;border-radius:8px;padding:12px;font-size:13px"></p>

    <div style="margin-top:20px;display:flex;justify-content:flex-end;gap:8px">
      <button @click="closeGrantModal()" style="border:0;background:#f1f5f9;color:#475569;border-radius:8px;padding:8px 16px;font-size:13px;cursor:pointer">Tutup</button>
      <button @click="grantAccess()" :disabled="isGranting"
        style="border:0;background:#059669;color:#fff;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer"
        x-text="isGranting ? 'Memproses...' : 'Beri Akses'"></button>
    </div>
  </div>
</div>
'''

s = s[:start] + new + s[end:]

# naikkan versi script supaya browser memuat yang baru
assert s.count('script.js?v=2.3') == 1, 'baris script.js tidak ketemu'
s = s.replace('script.js?v=2.3', 'script.js?v=2.4')

# rapikan komentar HTML yang tidak tertutup di modal donasi (tidak berbahaya)
s = s.replace('<!-- Header --\n', '<!-- Header -->\n')

open(p, 'w', encoding='utf-8').write(s)
print('Selesai: index.html berhasil ditambal')