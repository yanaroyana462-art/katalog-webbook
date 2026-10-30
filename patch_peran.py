import re, sys

HTML_FILE = 'dashboard.html'
JS_FILE = 'script.js'

js = open(JS_FILE, encoding='utf-8').read()
h = open(HTML_FILE, encoding='utf-8').read()
required, notes = [], []

# =================== BAGIAN script.js ===================
STATE_JS = """grantResult: '',
    authorStatus: 'none', // 'none' | 'pending' | 'approved' | 'rejected'
    isApplyModalOpen: false,
    isApplying: false,
    applyReason: '',
    isAuthorAdminModalOpen: false,
    isLoadingApplications: false,
    authorApplications: [],"""

METHODS_JS = """get canUpload() {
      return Boolean(this.currentUser) && (this.isAdmin || this.authorStatus === 'approved');
    },

    get pendingApplicationsCount() {
      return this.authorApplications.filter(a => a.status === 'pending').length;
    },

    async loadAuthorStatus() {
      if (!this.supabaseClient || !this.currentUser) { this.authorStatus = 'none'; return; }
      try {
        const { data, error } = await this.supabaseClient
          .from('authors')
          .select('status')
          .eq('user_id', this.currentUser.id)
          .maybeSingle();
        this.authorStatus = (!error && data && data.status) ? data.status : 'none';
      } catch (e) {
        this.authorStatus = 'none';
      }
      if (this.isAdmin) this.loadAuthorApplications();
    },

    openApplyModal() {
      this.applyReason = '';
      this.isApplyModalOpen = true;
    },

    closeApplyModal() {
      if (this.isApplying) return;
      this.isApplyModalOpen = false;
    },

    async submitAuthorApplication() {
      if (!this.currentUser || !this.supabaseClient) return;
      this.isApplying = true;
      try {
        const { data, error } = await this.supabaseClient.rpc('apply_author', { p_reason: this.applyReason.trim() });
        if (error) throw error;
        this.authorStatus = data || 'pending';
        this.isApplyModalOpen = false;
        this.showToast('Pengajuan terkirim. Admin akan meninjau sebelum Anda bisa menerbitkan buku.', 'success');
      } catch (err) {
        this.showToast('Gagal mengajukan: ' + (err.message || err), 'error');
      } finally {
        this.isApplying = false;
      }
    },

    async openAuthorAdminModal() {
      if (!this.isAdmin) return;
      this.isAuthorAdminModalOpen = true;
      await this.loadAuthorApplications();
    },

    closeAuthorAdminModal() {
      this.isAuthorAdminModalOpen = false;
    },

    async loadAuthorApplications() {
      if (!this.isAdmin || !this.supabaseClient) return;
      this.isLoadingApplications = true;
      try {
        const { data, error } = await this.supabaseClient.rpc('list_author_applications');
        if (error) throw error;
        this.authorApplications = data || [];
      } catch (err) {
        console.warn('Gagal memuat pengajuan penulis:', err);
      } finally {
        this.isLoadingApplications = false;
      }
    },

    async decideAuthor(app, status) {
      if (!this.isAdmin || !this.supabaseClient) return;
      try {
        const { error } = await this.supabaseClient.rpc('set_author_status', { p_user: app.user_id, p_status: status });
        if (error) throw error;
        await this.loadAuthorApplications();
        this.showToast(status === 'approved' ? 'Penulis disetujui.' : 'Status penulis diubah menjadi ditolak.', 'success');
      } catch (err) {
        this.showToast('Gagal mengubah status: ' + (err.message || err), 'error');
      }
    },

    async fetchUserPurchases() {
      this.loadAuthorStatus();"""

GUARD_JS = """
     if (!this.canUpload) {
       this.showToast('Hanya penulis yang sudah disetujui yang bisa menerbitkan buku.', 'error');
       return;
     }"""

if 'get canUpload()' in js:
    notes.append('script.js: sudah ditambal sebelumnya, dilewati')
else:
    if js.count("grantResult: '',") == 1:
        js = js.replace("grantResult: '',", STATE_JS)
    else:
        required.append("script.js: baris `grantResult: '',` tidak ketemu atau ganda")

    if js.count("async fetchUserPurchases() {") == 1:
        js = js.replace("async fetchUserPurchases() {", METHODS_JS)
    else:
        required.append("script.js: `async fetchUserPurchases() {` tidak ketemu atau ganda")

    if js.count("this.clearAuthorProfileFromForm();") == 1:
        js = js.replace("this.clearAuthorProfileFromForm();",
                        "this.authorStatus = 'none';\n      this.clearAuthorProfileFromForm();")
    else:
        notes.append('script.js: reset status saat logout dilewati (tidak masalah)')

    ms = list(re.finditer(r'async saveNewBook\s*\([^)]*\)\s*\{', js))
    if len(ms) == 1:
        js = js[:ms[0].end()] + GUARD_JS + js[ms[0].end():]
    else:
        notes.append('script.js: penjaga di saveNewBook dilewati (database tetap menolak non-penulis)')

# =================== BAGIAN HTML ===================
PANEL = """<!-- Panel untuk akun pembaca (belum jadi penulis) -->
    <div x-show="currentUser && !canUpload" style="display:none;max-width:480px;margin:0 auto;background:#fff;color:#0f172a;border:1px solid #e2e8f0;border-radius:16px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,.08)">
      <h3 style="margin:0;font-size:18px;font-weight:700">Akun Anda adalah akun pembaca</h3>
      <p style="margin:8px 0 0;font-size:13px;line-height:1.6;color:#475569">Akun pembaca bisa membaca, membeli, dan membagikan buku. Untuk menerbitkan buku sendiri, ajukan diri sebagai penulis. Admin akan meninjau pengajuan Anda terlebih dahulu.</p>
      <p x-show="authorStatus === 'pending'" style="display:none;margin:16px 0 0;background:#fef3c7;color:#92400e;border-radius:8px;padding:12px;font-size:13px">⏳ Pengajuan Anda sedang ditinjau admin. Silakan cek lagi nanti.</p>
      <p x-show="authorStatus === 'rejected'" style="display:none;margin:16px 0 0;background:#fee2e2;color:#991b1b;border-radius:8px;padding:12px;font-size:13px">Pengajuan Anda belum disetujui. Hubungi admin lewat WhatsApp untuk informasi lebih lanjut.</p>
      <div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap">
        <button x-show="authorStatus === 'none'" style="display:none;border:0;background:#4f46e5;color:#fff;border-radius:8px;padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer" @click="openApplyModal()">Ajukan Jadi Penulis</button>
        <button style="border:0;background:#f1f5f9;color:#475569;border-radius:8px;padding:10px 16px;font-size:13px;cursor:pointer" @click="goToCatalog()">Kembali ke Rak</button>
        <button style="border:0;background:#fff1f2;color:#be123c;border-radius:8px;padding:10px 16px;font-size:13px;cursor:pointer" @click="handleLogout()">Keluar</button>
      </div>
      <p style="margin:12px 0 0;font-size:12px;color:#94a3b8" x-text="'Masuk sebagai: ' + (currentUser ? currentUser.email : '')"></p>
    </div>

    <!-- Form Unggah (Hanya Tampil Untuk Penulis Disetujui / Admin) -->
    """

GRANT_BLOCK = """<!-- Tombol & Modal Beri Akses (khusus admin) -->
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
"""

AUTHOR_BLOCKS = """<!-- Tombol admin: kelola pengajuan penulis -->
<button x-show="isAdmin" style="display:none;position:fixed;left:16px;bottom:62px;z-index:60;background:#4f46e5;color:#fff;border:0;border-radius:9999px;padding:10px 16px;font-size:13px;font-weight:600;box-shadow:0 4px 14px rgba(0,0,0,.3);cursor:pointer"
  @click="openAuthorAdminModal()">👥 Penulis <span x-show="pendingApplicationsCount > 0" style="display:none;background:#f43f5e;border-radius:9999px;padding:1px 7px;margin-left:4px" x-text="pendingApplicationsCount"></span></button>

<!-- Modal: pembaca mengajukan jadi penulis -->
<div x-show="isApplyModalOpen" style="display:none;position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.55);align-items:center;justify-content:center;padding:16px"
  :style="isApplyModalOpen ? 'display:flex' : 'display:none'" @click.self="closeApplyModal()">
  <div style="width:100%;max-width:420px;background:#fff;color:#0f172a;border-radius:16px;padding:24px;box-shadow:0 20px 50px rgba(0,0,0,.35)">
    <h3 style="margin:0;font-size:18px;font-weight:700">Ajukan Jadi Penulis</h3>
    <p style="margin:4px 0 0;font-size:13px;color:#64748b">Ceritakan singkat buku apa yang ingin Anda terbitkan.</p>
    <textarea x-model="applyReason" rows="4" maxlength="500" placeholder="Contoh: Saya ingin menerbitkan buku panduan usaha kecil..."
      style="margin-top:12px;width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:14px;background:#fff;color:#0f172a"></textarea>
    <div style="margin-top:16px;display:flex;justify-content:flex-end;gap:8px">
      <button @click="closeApplyModal()" style="border:0;background:#f1f5f9;color:#475569;border-radius:8px;padding:8px 16px;font-size:13px;cursor:pointer">Batal</button>
      <button @click="submitAuthorApplication()" :disabled="isApplying" style="border:0;background:#4f46e5;color:#fff;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer" x-text="isApplying ? 'Mengirim...' : 'Kirim Pengajuan'"></button>
    </div>
  </div>
</div>

<!-- Modal admin: daftar pengajuan penulis -->
<div x-show="isAuthorAdminModalOpen && isAdmin" style="display:none;position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.55);align-items:center;justify-content:center;padding:16px"
  :style="isAuthorAdminModalOpen && isAdmin ? 'display:flex' : 'display:none'" @click.self="closeAuthorAdminModal()">
  <div style="width:100%;max-width:560px;max-height:85vh;overflow-y:auto;background:#fff;color:#0f172a;border-radius:16px;padding:24px;box-shadow:0 20px 50px rgba(0,0,0,.35)">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <h3 style="margin:0;font-size:18px;font-weight:700">Pengajuan Penulis</h3>
      <button @click="closeAuthorAdminModal()" style="border:0;background:transparent;font-size:22px;cursor:pointer;color:#64748b">&times;</button>
    </div>
    <p x-show="isLoadingApplications" style="display:none;margin:12px 0 0;font-size:13px;color:#64748b">Memuat...</p>
    <p x-show="!isLoadingApplications && authorApplications.length === 0" style="display:none;margin:12px 0 0;font-size:13px;color:#64748b">Belum ada pengajuan.</p>
    <template x-for="app in authorApplications" :key="app.user_id">
      <div style="margin-top:12px;border:1px solid #e2e8f0;border-radius:12px;padding:12px">
        <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
          <strong style="font-size:13px;word-break:break-all" x-text="app.email"></strong>
          <span style="font-size:11px;font-weight:600;border-radius:9999px;padding:2px 10px;white-space:nowrap"
            :style="app.status === 'approved' ? 'background:#d1fae5;color:#065f46' : (app.status === 'rejected' ? 'background:#fee2e2;color:#991b1b' : 'background:#fef3c7;color:#92400e')"
            x-text="app.status === 'approved' ? 'Disetujui' : (app.status === 'rejected' ? 'Ditolak' : 'Menunggu')"></span>
        </div>
        <p x-show="app.reason" style="display:none;margin:8px 0 0;font-size:13px;color:#475569;white-space:pre-line" x-text="app.reason"></p>
        <div style="margin-top:10px;display:flex;gap:8px">
          <button x-show="app.status !== 'approved'" style="display:none;border:0;background:#059669;color:#fff;border-radius:8px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer" @click="decideAuthor(app, 'approved')">Setujui</button>
          <button x-show="app.status !== 'rejected'" style="display:none;border:0;background:#fff1f2;color:#be123c;border-radius:8px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer" @click="decideAuthor(app, 'rejected')" x-text="app.status === 'approved' ? 'Cabut Izin' : 'Tolak'"></button>
        </div>
      </div>
    </template>
  </div>
</div>
"""

# 1) panel pembaca + formulir hanya untuk penulis
if 'x-show="canUpload"' in h:
    notes.append('HTML: pembatas formulir unggah sudah ada, dilewati')
else:
    pat = re.compile(r'<div\s+x-show="currentUser"\s+class="space-y-4"\s*>')
    if len(pat.findall(h)) == 1:
        h = pat.sub(lambda m: PANEL + '<div x-show="canUpload" class="space-y-4">', h)
    else:
        required.append(HTML_FILE + ': pembungkus formulir unggah `<div x-show="currentUser" class="space-y-4">` tidak ketemu atau ganda')

# 2) tombol & modal di akhir halaman
if '</body>' not in h:
    required.append(HTML_FILE + ': tag </body> tidak ketemu')
else:
    extra = ''
    if 'openGrantModal()' not in h:
        extra += GRANT_BLOCK
        notes.append('HTML: tombol Beri Akses belum ada di ' + HTML_FILE + ', ditambahkan')
    if 'openAuthorAdminModal()' not in h:
        extra += AUTHOR_BLOCKS
    if extra:
        i = h.rindex('</body>')
        h = h[:i] + extra + h[i:]

# 3) naikkan versi script.js
h, n = re.subn(r'script\.js\?v=\d+(?:\.\d+)*', 'script.js?v=2.5', h)
if n == 0:
    notes.append('HTML: nomor versi script.js tidak ketemu (lakukan refresh keras di browser)')

# =================== HASIL ===================
if required:
    print('GAGAL, tidak ada file yang diubah. Bagian yang tidak ketemu:')
    for r in required:
        print(' -', r)
    for nline in notes:
        print(' (catatan)', nline)
    sys.exit(1)

open(JS_FILE, 'w', encoding='utf-8').write(js)
open(HTML_FILE, 'w', encoding='utf-8').write(h)
print('SELESAI: script.js dan', HTML_FILE, 'berhasil ditambal')
for nline in notes:
    print(' (catatan)', nline)