#!/usr/bin/env node
// Tambalan: login langsung di tempat saat membeli buku (tanpa kembali ke rak).
// Pakai:  node patch-beli.js [dashboard.html] [script.js]
// Aman: tiap titik tambalan harus ditemukan TEPAT 1 kali. Jika tidak, tidak ada file yang diubah.
// File asli disimpan sebagai *.bak

const fs = require('fs');

const htmlPath = process.argv[2] || 'dashboard.html';
const jsPath = process.argv[3] || 'script.js';

const jsPatches = [
  {
    name: 'script.js #1 state pendingPurchaseBook',
    find: 'checkoutBook: null,',
    replace: 'checkoutBook: null,\n    pendingPurchaseBook: null,'
  },
  {
    name: 'script.js #2 pemantau login di init()',
    find: ".forEach(key => this.$watch(key, () => { this.currentPage = 1; }));",
    replace: `.forEach(key => this.$watch(key, () => { this.currentPage = 1; }));
      // Setelah login, lanjutkan pembelian yang tertunda
      this.$watch('currentUser', (user) => {
        if (user && this.pendingPurchaseBook) this.resumePendingPurchase();
      });`
  },
  {
    name: 'script.js #3 closeReader membersihkan antrean',
    find: 'closeReader() {',
    replace: 'closeReader() {\n     this.pendingPurchaseBook = null;'
  },
  {
    name: 'script.js #4 openPaymentModal + resumePendingPurchase',
    find: 'openPaymentModal(book) {',
    replace: `async resumePendingPurchase() {
     const book = this.pendingPurchaseBook;
     if (!book || !this.currentUser) return;
     this.pendingPurchaseBook = null;
     await this.fetchUserPurchases();
     if (this.purchasedBookIds.map(String).includes(String(book.id))) {
       this.showToast('Anda sudah punya akses ke buku ini. Selamat membaca!', 'success');
       if (this.activeBook && String(this.activeBook.id) === String(book.id)) this.loadSignedUrlForActiveBook();
       return;
     }
     this.openPaymentModal(book);
   },

   openPaymentModal(book) {
     if (!book) return;
     // Belum login: buka jendela login di tempat, ingat buku yang mau dibeli
     if (!this.currentUser) {
       this.pendingPurchaseBook = book;
       window.dispatchEvent(new CustomEvent('open-login'));
       this.showToast('Masuk atau daftar dulu. Setelah itu Anda langsung lanjut ke pembayaran.', 'info');
       return;
     }`
  },
  {
    name: 'script.js #5 pengaman processPayment',
    find: "this.showToast('Silakan masuk sebelum mengajukan pembelian buku.', 'error');",
    replace: `const pendingBook = this.checkoutBook;
       if (pendingBook) {
         this.isProcessingPayment = false;
         this.isPaymentModalOpen = false;
         this.openPaymentModal(pendingBook);
         return;
       }
       this.showToast('Silakan masuk sebelum mengajukan pembelian buku.', 'error');`
  }
];

const htmlPatches = [
  {
    name: 'dashboard.html #1 tombol Masuk/Daftar di halaman baca',
    find: '<template x-if="activeBook">',
    replace: `<button type="button" x-show="activeBook && !currentUser" style="display:none" @click="$dispatch('open-login')"
                class="px-3 sm:px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition-all shadow-sm shadow-indigo-600/20 flex-shrink-0">
          Masuk / Daftar
        </button>

        <template x-if="activeBook">`
  },
  {
    name: 'dashboard.html #2 subjudul jendela login',
    find: "x-text=\"authMode === 'forgot' ? 'Masukkan email akun Anda. Kami kirim tautan untuk mengatur ulang kata sandi.' : 'Akun diperlukan untuk membeli dan membaca buku berbayar.'\"",
    replace: `x-text="authMode === 'forgot'
               ? 'Masukkan email akun Anda. Kami kirim tautan untuk mengatur ulang kata sandi.'
               : (pendingPurchaseBook
                   ? 'Masuk atau daftar untuk membeli “' + pendingPurchaseBook.title + '”. Setelah itu Anda langsung lanjut ke pembayaran.'
                   : 'Akun diperlukan untuk membeli dan membaca buku berbayar.')"`
  },
  {
    name: 'dashboard.html #3 batalkan antrean jika login ditutup',
    find: '@open-login.window="switchAuthMode(\'login\'); open = true"',
    replace: `@open-login.window="switchAuthMode('login'); open = true"
     x-init="$watch('open', v => { if (!v && !currentUser) pendingPurchaseBook = null })"`
  }
];

function count(haystack, needle) {
  let n = 0, i = 0;
  while ((i = haystack.indexOf(needle, i)) !== -1) { n++; i += needle.length; }
  return n;
}

function plan(path, patches) {
  let src = fs.readFileSync(path, 'utf8');
  if (src.includes('pendingPurchaseBook')) {
    console.log(`- ${path}: sudah ditambal sebelumnya, dilewati.`);
    return null;
  }
  const errors = [];
  for (const p of patches) {
    const c = count(src, p.find);
    if (c !== 1) errors.push(`  ${p.name}: ditemukan ${c}x (harus 1x)`);
  }
  if (errors.length) {
    console.error(`GAGAL pada ${path}:\n${errors.join('\n')}`);
    process.exit(1);
  }
  for (const p of patches) src = src.replace(p.find, () => p.replace);
  return src;
}

// Tahap 1: cek semua dulu, belum menulis apa pun
const newJs = plan(jsPath, jsPatches);
const newHtml = plan(htmlPath, htmlPatches);

// Tahap 2: tulis
if (newJs !== null) {
  fs.copyFileSync(jsPath, jsPath + '.bak');
  fs.writeFileSync(jsPath, newJs);
  console.log(`✔ ${jsPath} ditambal (cadangan: ${jsPath}.bak)`);
}
if (newHtml !== null) {
  fs.copyFileSync(htmlPath, htmlPath + '.bak');
  fs.writeFileSync(htmlPath, newHtml);
  console.log(`✔ ${htmlPath} ditambal (cadangan: ${htmlPath}.bak)`);
}
console.log('Selesai. Naikkan versi di dashboard.html agar cache browser diperbarui: script.js?v=2.19 → v=2.20');