import re, shutil, sys

js = open("script.js", encoding="utf-8").read()
html = open("dashboard.html", encoding="utf-8").read()

if "pw-fab" in html:
    print("[lewati] sudah dipatch")
    sys.exit(0)

def run(src, name, edits):
    for label, old, new, need in edits:
        n = src.count(old)
        if n != need:
            sys.exit(f"[GAGAL] {name}: '{label}' ditemukan {n}x (harus {need}x). Tidak ada yang diubah.")
    for label, old, new, need in edits:
        src = src.replace(old, new)
    return src

def regex_once(src, name, label, pattern, fn):
    new, n = re.subn(pattern, fn, src, flags=re.S)
    if n != 1:
        sys.exit(f"[GAGAL] {name}: '{label}' ditemukan {n}x (harus 1x). Tidak ada yang diubah.")
    return new

# ======================= script.js =======================
state = """isGrantModalOpen: false,
    authorStatus: null, // null = memuat | 'none' | 'pending' | 'approved' | 'rejected'
    authorNote: '',
    authorApplyForm: { fullName: '', whatsapp: '', bio: '', sampleUrl: '', plan: '', agree: false },
    isSubmittingApplication: false,
    isReviewModalOpen: false,
    reviewLoading: false,
    reviewApplications: [],
    reviewNotes: {},"""

getters = """get isApprovedAuthor() {
      return this.isAdmin || this.authorStatus === 'approved';
    },

    get pendingApplicationsCount() {
      return this.reviewApplications.filter(a => a.status === 'pending').length;
    },

    get isAdmin() {"""

methods = """async fetchAuthorStatus() {
      if (!this.supabaseClient || !this.currentUser) { this.authorStatus = null; return; }
      try {
        const { data, error } = await this.supabaseClient
          .from('author_applications')
          .select('status, admin_note')
          .eq('user_id', this.currentUser.id)
          .maybeSingle();
        if (error) throw error;
        this.authorStatus = data ? data.status : 'none';
        this.authorNote = data?.admin_note || '';
      } catch (err) {
        console.warn('Gagal memuat status penulis:', err);
        this.authorStatus = 'none';
      }
      if (this.isAdmin) this.loadApplications(true);
    },

    async submitAuthorApplication() {
      const f = this.authorApplyForm;
      if (!f.fullName.trim() || f.bio.trim().length < 20) {
        this.showToast('Lengkapi nama dan latar belakang (minimal 20 karakter).', 'error');
        return;
      }
      if (!f.agree) {
        this.showToast('Setujui pernyataan hak cipta dulu.', 'error');
        return;
      }
      this.isSubmittingApplication = true;
      try {
        const { data, error } = await this.supabaseClient.rpc('submit_author_application', {
          p_full_name: f.fullName.trim(),
          p_whatsapp: f.whatsapp.trim(),
          p_bio: f.bio.trim(),
          p_sample_url: this.safeUrl(f.sampleUrl),
          p_plan: f.plan.trim()
        });
        if (error) throw error;
        await this.fetchAuthorStatus();
        this.showToast(data === 'ALREADY_APPROVED' ? 'Akun Anda sudah disetujui.' : 'Pengajuan terkirim. Admin akan meninjaunya.', 'success');
      } catch (err) {
        this.showToast('Gagal mengirim pengajuan: ' + (err.message || err), 'error');
      } finally {
        this.isSubmittingApplication = false;
      }
    },

    async openReviewModal() {
      this.isReviewModalOpen = true;
      await this.loadApplications();
    },

    closeReviewModal() {
      this.isReviewModalOpen = false;
    },

    async loadApplications(silent = false) {
      if (!this.isAdmin || !this.supabaseClient) return;
      if (!silent) this.reviewLoading = true;
      try {
        const { data, error } = await this.supabaseClient.rpc('admin_list_author_applications');
        if (error) throw error;
        this.reviewApplications = data || [];
      } catch (err) {
        if (!silent) this.showToast('Gagal memuat pengajuan: ' + (err.message || err), 'error');
      } finally {
        this.reviewLoading = false;
      }
    },

    async reviewApplication(app, status) {
      if (!this.isAdmin) return;
      try {
        const { error } = await this.supabaseClient.rpc('admin_review_author', {
          p_user: app.user_id,
          p_status: status,
          p_note: this.reviewNotes[app.user_id] || ''
        });
        if (error) throw error;
        this.showToast(status === 'approved' ? `${app.email} disetujui sebagai penulis.` : `${app.email} ditolak atau izinnya dicabut.`, 'success');
        await this.loadApplications();
      } catch (err) {
        this.showToast('Gagal menyimpan keputusan: ' + (err.message || err), 'error');
      }
    },

    async fetchUserPurchases() {"""

js_edits = [
    ("state", "isGrantModalOpen: false,", state, 1),
    ("getter", "get isAdmin() {", getters, 1),
    ("metode", "async fetchUserPurchases() {", methods, 1),
    ("panggil status", "this.fetchUserPurchases();", "this.fetchUserPurchases();\n            this.fetchAuthorStatus();", 2),
    ("reset keluar", "this.clearAuthorProfileFromForm();",
     "this.clearAuthorProfileFromForm();\n      this.authorStatus = null;\n      this.authorNote = '';\n      this.reviewApplications = [];\n      this.isReviewModalOpen = false;", 1),
]

# ======================= dashboard.html =======================
css = """<style>
    .pw-card{background:#fff;color:#0f172a;border:1px solid #e2e8f0;border-radius:1rem;padding:1.5rem;box-shadow:0 1px 2px rgba(0,0,0,.05)}
    .dark .pw-card{background:#0f172a;color:#e2e8f0;border-color:#1e293b}
    .pw-title{font-size:1.125rem;font-weight:700;margin:0}
    .pw-sub{font-size:.75rem;color:#64748b;margin:.35rem 0 0;line-height:1.5}
    .dark .pw-sub{color:#94a3b8}
    .pw-text{font-size:.8rem;margin:.5rem 0 0;line-height:1.55;white-space:pre-line}
    .pw-label{display:block;font-size:.75rem;font-weight:600;margin:.9rem 0 .35rem}
    .pw-input{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:.75rem;padding:.55rem .8rem;font-size:.8rem;background:#fff;color:#0f172a}
    .dark .pw-input{background:#020617;border-color:#334155;color:#f1f5f9}
    .pw-check{display:flex;gap:.55rem;align-items:flex-start;font-size:.75rem;line-height:1.5;margin-top:1rem;cursor:pointer}
    .pw-link{border:0;background:none;padding:0;font-size:inherit;color:#4f46e5;text-decoration:underline;cursor:pointer}
    .dark .pw-link{color:#a5b4fc}
    .pw-btn{border:0;border-radius:.75rem;padding:.6rem 1.1rem;font-size:.8rem;font-weight:600;cursor:pointer;background:#4f46e5;color:#fff;margin-top:1rem}
    .pw-btn:disabled{opacity:.6;cursor:default}
    .pw-btn-ghost{background:#f1f5f9;color:#334155;margin-top:0}
    .dark .pw-btn-ghost{background:#1e293b;color:#e2e8f0}
    .pw-btn-ok{background:#059669;margin-top:.6rem}
    .pw-btn-no{background:#e11d48;margin-top:.6rem}
    .pw-note{font-size:.75rem;line-height:1.5;border-radius:.75rem;padding:.7rem .9rem;margin-top:.9rem;background:#fffbeb;border:1px solid #fde68a;color:#92400e}
    .dark .pw-note{background:rgba(120,53,15,.25);border-color:#78350f;color:#fde68a}
    .pw-item{border:1px solid #e2e8f0;border-radius:.75rem;padding:.9rem;margin-top:.9rem}
    .dark .pw-item{border-color:#334155}
    .pw-chip{font-size:.65rem;font-weight:700;border-radius:9999px;padding:.15rem .6rem;background:#e2e8f0;color:#334155}
    .pw-chip-pending{background:#fef3c7;color:#92400e}
    .pw-chip-approved{background:#d1fae5;color:#065f46}
    .pw-chip-rejected{background:#ffe4e6;color:#9f1239}
    .pw-modal-bg{position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;padding:1rem}
    .pw-modal{width:100%;max-width:640px;max-height:88vh;overflow:auto}
    .pw-fab{position:fixed;left:16px;bottom:64px;z-index:60;background:#4f46e5;color:#fff;border:0;border-radius:9999px;padding:10px 16px;font-size:13px;font-weight:600;box-shadow:0 4px 14px rgba(0,0,0,.3);cursor:pointer}
    .pw-count{margin-left:6px;background:#fff;color:#4f46e5;border-radius:9999px;padding:0 7px;font-size:11px;font-weight:700}
    .pw-badge-new{font-size:10px;font-weight:600;background:#4f46e5;color:#fff;border:1px solid #818cf8;padding:2px 8px;border-radius:4px;box-shadow:0 1px 2px rgba(0,0,0,.1)}
  </style>
</head>"""

apply_card = """<!-- Pengajuan menjadi penulis (untuk akun yang belum disetujui) -->
    <div x-show="currentUser && authorStatus !== null && !isApprovedAuthor" x-cloak class="pw-card">
      <h3 class="pw-title">Ajukan Diri Menjadi Penulis</h3>
      <p class="pw-sub">Akun Anda sudah terdaftar sebagai pembaca. Untuk menerbitkan buku, ajukan diri sebagai penulis. Admin akan meninjau pengajuan Anda.</p>

      <div x-show="authorStatus === 'pending'" class="pw-note">Pengajuan Anda sedang ditinjau admin. Setelah disetujui, muat ulang halaman ini dan formulir unggah akan terbuka.</div>

      <div x-show="authorStatus === 'rejected'" class="pw-note">
        Pengajuan sebelumnya belum disetujui.
        <span x-show="authorNote" x-text="'Catatan admin: ' + authorNote"></span>
        Anda dapat memperbarui data lalu mengajukan kembali.
      </div>

      <form x-show="authorStatus === 'none' || authorStatus === 'rejected'" @submit.prevent="submitAuthorApplication()">
        <label class="pw-label">Nama lengkap / nama pena *</label>
        <input class="pw-input" type="text" x-model="authorApplyForm.fullName" required maxlength="120" />

        <label class="pw-label">Nomor WhatsApp</label>
        <input class="pw-input" type="text" x-model="authorApplyForm.whatsapp" maxlength="30" placeholder="08..." />

        <label class="pw-label">Latar belakang dan keahlian * (minimal 20 karakter)</label>
        <textarea class="pw-input" rows="4" x-model="authorApplyForm.bio" required minlength="20" maxlength="1000" placeholder="Ceritakan singkat siapa Anda dan bidang yang Anda tulis."></textarea>

        <label class="pw-label">Tautan contoh karya (opsional)</label>
        <input class="pw-input" type="url" x-model="authorApplyForm.sampleUrl" placeholder="https://..." />

        <label class="pw-label">Buku apa yang ingin Anda terbitkan? (opsional)</label>
        <textarea class="pw-input" rows="2" x-model="authorApplyForm.plan" maxlength="500"></textarea>

        <label class="pw-check">
          <input type="checkbox" x-model="authorApplyForm.agree" required />
          <span>Saya hanya akan mengunggah karya sendiri atau karya yang saya miliki izinnya, dan menyetujui
            <button type="button" class="pw-link" @click="openLegal('terms')">Syarat &amp; Ketentuan</button> serta
            <button type="button" class="pw-link" @click="openLegal('copyright')">Kebijakan Hak Cipta</button>.</span>
        </label>

        <p class="pw-sub">Penulis baru menerbitkan buku gratis terlebih dahulu. Buku berbayar ditetapkan oleh admin.</p>

        <button type="submit" class="pw-btn" :disabled="isSubmittingApplication" x-text="isSubmittingApplication ? 'Mengirim...' : 'Kirim Pengajuan'"></button>
      </form>
    </div>

    <div x-show="currentUser && isApprovedAuthor" class="space-y-4">"""

admin_ui = """<!-- Tombol & Modal Tinjau Pengajuan Penulis (khusus admin) -->
<button x-show="isAdmin" x-cloak type="button" class="pw-fab" @click="openReviewModal()">
  ✍️ Pengajuan Penulis<span x-show="pendingApplicationsCount > 0" class="pw-count" x-text="pendingApplicationsCount"></span>
</button>

<div x-show="isReviewModalOpen && isAdmin" x-cloak class="pw-modal-bg" @click.self="closeReviewModal()" @keydown.escape.window="closeReviewModal()">
  <div class="pw-card pw-modal">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">
      <div>
        <h3 class="pw-title">Pengajuan Penulis</h3>
        <p class="pw-sub">Setujui untuk memberi izin menerbitkan buku. Tolak atau cabut untuk menutup izin itu.</p>
      </div>
      <button type="button" class="pw-btn pw-btn-ghost" @click="closeReviewModal()">Tutup</button>
    </div>

    <p x-show="reviewLoading" class="pw-sub">Memuat...</p>
    <p x-show="!reviewLoading && reviewApplications.length === 0" class="pw-sub">Belum ada pengajuan.</p>

    <template x-for="app in reviewApplications" :key="app.user_id">
      <div class="pw-item">
        <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;align-items:center">
          <strong x-text="app.full_name"></strong>
          <span class="pw-chip" :class="'pw-chip-' + app.status" x-text="app.status === 'pending' ? 'Menunggu' : (app.status === 'approved' ? 'Disetujui' : 'Ditolak')"></span>
        </div>
        <p class="pw-sub" x-text="app.email + ' · ' + new Date(app.created_at).toLocaleDateString('id-ID')"></p>
        <p class="pw-text" x-text="app.bio"></p>
        <p class="pw-text" x-show="app.plan" x-text="'Rencana: ' + app.plan"></p>
        <p class="pw-sub">
          <a x-show="safeUrl(app.sample_url)" :href="safeUrl(app.sample_url)" target="_blank" rel="noopener noreferrer" class="pw-link">Contoh karya</a>
          <a x-show="app.whatsapp" :href="formatWhatsappUrl(app.whatsapp)" target="_blank" rel="noopener noreferrer" class="pw-link" style="margin-left:10px">WhatsApp</a>
        </p>
        <input class="pw-input" style="margin-top:.6rem" type="text" placeholder="Catatan untuk pengaju (opsional)" x-model="reviewNotes[app.user_id]" />
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button type="button" x-show="app.status !== 'approved'" class="pw-btn pw-btn-ok" @click="reviewApplication(app, 'approved')">Setujui</button>
          <button type="button" x-show="app.status !== 'rejected'" class="pw-btn pw-btn-no" @click="reviewApplication(app, 'rejected')" x-text="app.status === 'approved' ? 'Cabut izin' : 'Tolak'"></button>
        </div>
      </div>
    </template>
  </div>
</div>

<!-- Tombol & Modal Beri Akses (khusus admin) -->"""

html_edits = [
    ("gaya", "</head>", css, 1),
    ("kartu pengajuan", '<div x-show="currentUser" class="space-y-4">', apply_card, 1),
    ("panel admin", "<!-- Tombol & Modal Beri Akses (khusus admin) -->", admin_ui, 1),
]

js = run(js, "script.js", js_edits)
html = run(html, "dashboard.html", html_edits)

# Dasbor dan Profil Saya hanya untuk penulis disetujui
for label, fn_name in [("tombol Dasbor", "openDashboard"), ("tombol Profil Saya", "openProfileModal")]:
    html = regex_once(
        html, "dashboard.html", label,
        r'<template x-if="currentUser">(\s*<button @click="' + fn_name + r'\(\)")',
        lambda m: '<template x-if="currentUser && isApprovedAuthor">' + m.group(1))

# Pilihan "Berbayar" hanya untuk admin
html = regex_once(
    html, "dashboard.html", "pilihan Berbayar",
    r'<label (class="inline-flex items-center cursor-pointer text-xs text-slate-700 dark:text-slate-300">\s*<input type="radio" value="Berbayar")',
    lambda m: '<label x-show="isAdmin" ' + m.group(1))

# Perbaikan warna label "Baru" (jika patch draft sudah dipasang)
old_baru = 'class="text-[10px] bg-indigo-600/95 text-white border border-indigo-400 px-2 py-0.5 rounded font-semibold shadow-sm">Baru</span>'
if html.count(old_baru) == 1:
    html = html.replace(old_baru, 'class="pw-badge-new">Baru</span>')

m = re.search(r'script\.js\?v=(\d+)\.(\d+)', html)
if m:
    new_ver = f"{m.group(1)}.{int(m.group(2)) + 1}"
    html = html.replace(m.group(0), f"script.js?v={new_ver}")
    print(f"[info] versi cache script.js: {m.group(1)}.{m.group(2)} -> {new_ver}")
else:
    print("[peringatan] versi cache script.js tidak ditemukan, naikkan manual")

shutil.copy("script.js", "script.js.bak_penulis")
shutil.copy("dashboard.html", "dashboard.html.bak_penulis")
open("script.js", "w", encoding="utf-8").write(js)
open("dashboard.html", "w", encoding="utf-8").write(html)
print("[ok] sistem pengajuan penulis terpasang (cadangan: *.bak_penulis)")
