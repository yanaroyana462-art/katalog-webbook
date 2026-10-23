#!/usr/bin/env python3
"""
Tambal Pustaka WebBook: footer + modal halaman legal
(Privasi, Syarat & Ketentuan, Hak Cipta, Tentang & Cara Kerja).

Cara pakai (di folder yang berisi index.html dan script.js):
    python3 patch_legal.py

Aman dijalankan ulang: kalau sudah pernah ditambal, skrip berhenti tanpa mengubah apa pun.
File asli dicadangkan sebagai index.html.bak dan script.js.bak.
"""
import shutil
import sys

HTML_FILE = "index.html"
JS_FILE = "script.js"

HTML_ANCHOR = "<!-- Tombol & Modal Beri Akses (khusus admin) -->"
JS_STATE_ANCHOR = "    // State Modal Donasi\n"
JS_METHOD_ANCHOR = "   openDonateModal() {"

HTML_BLOCK = r'''
  <!-- ========================================== -->
  <!-- FOOTER                                     -->
  <!-- ========================================== -->
  <footer x-show="!activeBook" x-cloak class="mt-16 border-t border-stone-200/80 dark:border-slate-800 bg-[#fdfcfb]/80 dark:bg-slate-900/70 backdrop-blur-sm">
    <div class="max-w-6xl mx-auto px-4 py-10">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 text-xs">
        <div>
          <div class="flex items-center gap-2.5 mb-3">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-700 via-indigo-600 to-amber-600 flex items-center justify-center font-bold text-white text-[11px] tracking-wider">WB</div>
            <span class="font-bold text-sm text-stone-900 dark:text-white">Pustaka WebBook</span>
          </div>
          <p class="text-stone-600 dark:text-slate-400 leading-relaxed">Portal buku interaktif dan digital. Baca, kumpulkan, dan terbitkan buku Anda dalam satu rak.</p>
        </div>

        <div>
          <h4 class="font-bold text-stone-900 dark:text-white mb-3">Informasi</h4>
          <ul class="space-y-2 text-stone-600 dark:text-slate-400">
            <li><button type="button" @click="openLegal('about')" class="hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline">Tentang & Cara Kerja</button></li>
            <li><button type="button" @click="openLegal('privacy')" class="hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline">Kebijakan Privasi</button></li>
            <li><button type="button" @click="openLegal('terms')" class="hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline">Syarat & Ketentuan</button></li>
            <li><button type="button" @click="openLegal('copyright')" class="hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline">Kebijakan Hak Cipta</button></li>
          </ul>
        </div>

        <div>
          <h4 class="font-bold text-stone-900 dark:text-white mb-3">Kontak</h4>
          <ul class="space-y-2 text-stone-600 dark:text-slate-400">
            <li>
              <a :href="`https://wa.me/${adminWaNumber}?text=${encodeURIComponent('Halo Admin Pustaka WebBook, saya ingin bertanya.')}`" target="_blank" rel="noopener noreferrer" class="hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline">WhatsApp Admin</a>
            </li>
            <li>
              <a :href="`mailto:${adminEmail}`" class="hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline break-all" x-text="adminEmail"></a>
            </li>
            <li><button type="button" @click="openDonateModal()" class="hover:text-rose-600 dark:hover:text-rose-400 hover:underline">Dukung dengan Donasi</button></li>
          </ul>
        </div>
      </div>

      <div class="mt-8 pt-5 border-t border-stone-200/70 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-stone-500 dark:text-slate-500">
        <span x-text="`© ${new Date().getFullYear()} Pustaka WebBook. Seluruh hak cipta buku tetap milik penulis atau pemegang hak masing-masing.`"></span>
        <span>Laporan pelanggaran hak cipta: gunakan tombol "Laporkan buku" pada halaman buku.</span>
      </div>
    </div>
  </footer>

  <!-- ========================================== -->
  <!-- MODAL HALAMAN INFORMASI & KEBIJAKAN        -->
  <!-- ========================================== -->
  <div x-show="isLegalModalOpen" x-cloak
       @keydown.escape.window="closeLegal()"
       class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm"
       x-transition:enter="transition ease-out duration-200"
       x-transition:enter-start="opacity-0"
       x-transition:enter-end="opacity-100"
       x-transition:leave="transition ease-in duration-150"
       x-transition:leave-start="opacity-100"
       x-transition:leave-end="opacity-0">

    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl relative"
         @click.outside="closeLegal()"
         role="dialog" aria-modal="true" aria-labelledby="legalModalTitle">

      <!-- Header + Tab -->
      <div class="p-4 sm:p-5 border-b border-slate-100 dark:border-slate-800">
        <div class="flex items-center justify-between">
          <h3 id="legalModalTitle" class="text-base font-bold text-slate-900 dark:text-white" x-text="legalTitles[legalPage]"></h3>
          <button type="button" @click="closeLegal()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg" aria-label="Tutup">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>
        <div class="mt-3 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          <template x-for="key in ['about','privacy','terms','copyright']" :key="key">
            <button type="button" @click="legalPage = key; $refs.legalBody.scrollTop = 0"
                    class="px-3 py-1.5 rounded-lg text-[11px] font-semibold whitespace-nowrap transition border"
                    :class="legalPage === key
                      ? 'bg-indigo-600 border-indigo-600 text-white'
                      : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700'"
                    x-text="legalTabs[key]"></button>
          </template>
        </div>
      </div>

      <!-- Isi -->
      <div x-ref="legalBody" class="flex-1 overflow-y-auto p-4 sm:p-6 text-xs sm:text-sm leading-relaxed text-slate-700 dark:text-slate-300 space-y-4">

        <!-- TENTANG & CARA KERJA -->
        <div x-show="legalPage === 'about'" class="space-y-4">
          <p>Pustaka WebBook adalah portal buku digital interaktif. Pembaca dapat membaca buku langsung di browser (teks bab, dokumen PDF, atau WebBook interaktif), sedangkan penulis dapat menerbitkan karyanya dan mengelola profil penulisnya sendiri.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">Cara membaca</h4>
          <ol class="list-decimal pl-5 space-y-1.5">
            <li>Cari buku lewat kolom pencarian atau filter kategori, akses, dan penulis.</li>
            <li>Buka kartu buku untuk melihat sinopsis, profil penulis, dan daftar bab.</li>
            <li>Buku berstatus Gratis dapat dibaca penuh. Buku Berbayar menampilkan pratinjau Bab 1, sedangkan bab lainnya terbuka setelah akses diberikan.</li>
          </ol>

          <h4 class="font-bold text-slate-900 dark:text-white">Cara membeli buku berbayar</h4>
          <ol class="list-decimal pl-5 space-y-1.5">
            <li>Masuk atau daftar akun member, lalu tekan tombol beli pada halaman buku.</li>
            <li>Konfirmasi pesanan. Anda akan diarahkan ke WhatsApp admin untuk menerima petunjuk pembayaran.</li>
            <li>Setelah pembayaran diverifikasi admin, akses buku dibuka pada akun yang sama. Verifikasi dilakukan secara manual, sehingga membutuhkan waktu.</li>
          </ol>

          <h4 class="font-bold text-slate-900 dark:text-white">Cara menerbitkan buku</h4>
          <ol class="list-decimal pl-5 space-y-1.5">
            <li>Masuk dengan akun member, lalu pilih Unggah Buku.</li>
            <li>Isi judul, penulis, sinopsis, kategori, jenis akses, serta bab atau berkas buku.</li>
            <li>Pilih dasar hak untuk membagikan dan setujui pernyataan hak cipta. Hanya karya sendiri, domain publik, lisensi terbuka, atau karya yang sudah mendapat izin pemegang hak yang boleh diunggah.</li>
          </ol>

          <p>Butuh bantuan? Hubungi admin lewat WhatsApp atau email pada bagian Kontak di footer.</p>
        </div>

        <!-- KEBIJAKAN PRIVASI -->
        <div x-show="legalPage === 'privacy'" class="space-y-4">
          <p class="text-[11px] text-slate-500 dark:text-slate-400">Berlaku sejak: Oktober 2026</p>
          <p>Kebijakan ini menjelaskan data apa yang kami simpan saat Anda memakai Pustaka WebBook, untuk apa data itu dipakai, dan bagaimana Anda dapat mengendalikannya.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">Data yang kami simpan</h4>
          <ul class="list-disc pl-5 space-y-1.5">
            <li><strong>Akun:</strong> alamat email dan kata sandi. Kata sandi dikelola oleh layanan autentikasi Supabase dan tidak dapat dibaca oleh admin.</li>
            <li><strong>Profil penulis (opsional):</strong> nama pena, foto, biografi, dan tautan media sosial atau kontak yang Anda isi sendiri. Informasi ini tampil publik pada buku yang Anda terbitkan.</li>
            <li><strong>Buku dan berkas:</strong> judul, sinopsis, isi bab, sampul, dan dokumen yang Anda unggah.</li>
            <li><strong>Akses buku:</strong> catatan buku berbayar apa saja yang sudah dibuka untuk akun Anda.</li>
            <li><strong>Statistik kunjungan:</strong> data kunjungan yang bersifat agregat melalui layanan analitik Umami, untuk mengetahui halaman mana yang sering dibuka.</li>
          </ul>

          <h4 class="font-bold text-slate-900 dark:text-white">Data di perangkat Anda</h4>
          <p>Browser Anda menyimpan pilihan tema terang atau gelap, ukuran huruf pembaca, dan salinan profil penulis agar formulir terisi otomatis. Data ini hanya ada di perangkat Anda dan dapat dihapus lewat pengaturan browser.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">Pembayaran dan donasi</h4>
          <p>Pembayaran dan donasi dikonfirmasi lewat WhatsApp. Portal ini tidak menyimpan nomor kartu atau data rekening Anda. Pesan yang Anda kirim lewat WhatsApp tunduk pada kebijakan WhatsApp.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">Dengan siapa data dibagikan</h4>
          <p>Kami tidak menjual data Anda. Data disimpan dan diproses oleh penyedia layanan yang menjalankan portal ini, yaitu Supabase (basis data, autentikasi, dan penyimpanan berkas) dan Umami (statistik kunjungan). Data juga dapat kami buka bila diwajibkan oleh hukum.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">Hak Anda</h4>
          <p>Anda dapat meminta perbaikan data, penghapusan akun, atau penghapusan buku yang Anda unggah dengan menghubungi admin. Profil penulis dapat Anda ubah sendiri kapan saja lewat tombol Profil Saya.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">Kontak</h4>
          <p>Pertanyaan tentang privasi: <a :href="`mailto:${adminEmail}`" class="text-indigo-600 dark:text-indigo-400 underline break-all" x-text="adminEmail"></a>.</p>
        </div>

        <!-- SYARAT & KETENTUAN -->
        <div x-show="legalPage === 'terms'" class="space-y-4">
          <p class="text-[11px] text-slate-500 dark:text-slate-400">Berlaku sejak: Oktober 2026</p>
          <p>Dengan memakai Pustaka WebBook, Anda menyetujui syarat berikut.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">1. Akun</h4>
          <p>Anda bertanggung jawab menjaga kerahasiaan kata sandi dan seluruh aktivitas pada akun Anda. Gunakan email yang aktif dan benar.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">2. Konten yang diunggah</h4>
          <ul class="list-disc pl-5 space-y-1.5">
            <li>Anda hanya boleh mengunggah karya sendiri, karya domain publik, karya berlisensi terbuka, atau karya yang sudah mendapat izin pemegang hak.</li>
            <li>Anda bertanggung jawab penuh atas keaslian dan legalitas konten yang diunggah.</li>
            <li>Dilarang mengunggah konten yang melanggar hukum, mengandung kebencian, pornografi, penipuan, atau malware.</li>
            <li>Admin berhak menurunkan, menyembunyikan, atau menghapus konten yang melanggar ketentuan ini tanpa pemberitahuan lebih dulu.</li>
          </ul>

          <h4 class="font-bold text-slate-900 dark:text-white">3. Pembelian buku berbayar</h4>
          <ul class="list-disc pl-5 space-y-1.5">
            <li>Akses dibuka setelah pembayaran diverifikasi admin dan melekat pada akun pembeli.</li>
            <li>Akses bersifat pribadi. Dilarang membagikan akun, menyalin, atau menyebarkan ulang isi buku. Dokumen PDF yang diunduh dapat diberi watermark berisi identitas akun pembeli.</li>
            <li>Permintaan pengembalian dana atau kendala akses dapat disampaikan ke admin dan ditinjau satu per satu.</li>
          </ul>

          <h4 class="font-bold text-slate-900 dark:text-white">4. Donasi</h4>
          <p>Donasi bersifat sukarela untuk mendukung pengembangan portal dan tidak memberikan hak atau akses tertentu.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">5. Ketersediaan layanan</h4>
          <p>Kami berusaha menjaga portal tetap berjalan, namun tidak menjamin layanan bebas gangguan. Fitur dapat berubah sewaktu-waktu.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">6. Perubahan ketentuan</h4>
          <p>Syarat ini dapat diperbarui. Pemakaian portal setelah pembaruan berarti Anda menyetujui versi terbaru.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">Kontak</h4>
          <p>Pertanyaan tentang syarat ini: <a :href="`mailto:${adminEmail}`" class="text-indigo-600 dark:text-indigo-400 underline break-all" x-text="adminEmail"></a>.</p>
        </div>

        <!-- KEBIJAKAN HAK CIPTA -->
        <div x-show="legalPage === 'copyright'" class="space-y-4">
          <p class="text-[11px] text-slate-500 dark:text-slate-400">Berlaku sejak: Oktober 2026</p>
          <p>Kami menghormati hak cipta. Seluruh hak atas sebuah buku tetap dimiliki penulis atau pemegang haknya masing-masing.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">Tanggung jawab pengunggah</h4>
          <p>Setiap buku diunggah bersama pernyataan dasar hak (karya sendiri, izin pemegang hak, domain publik, atau lisensi terbuka) dan persetujuan pengunggah. Pengunggah bertanggung jawab atas pernyataan tersebut.</p>

          <h4 class="font-bold text-slate-900 dark:text-white">Cara melaporkan pelanggaran</h4>
          <ol class="list-decimal pl-5 space-y-1.5">
            <li>Buka halaman buku yang dipermasalahkan, lalu tekan tombol <strong>Laporkan buku</strong>. Pesan WhatsApp ke admin akan terisi otomatis dengan judul, penulis, dan tautan buku.</li>
            <li>Sebutkan alasan laporan, karya asli yang dilanggar, dan bukti kepemilikan hak bila ada.</li>
            <li>Anda juga dapat melapor lewat email ke <a :href="`mailto:${adminEmail}`" class="text-indigo-600 dark:text-indigo-400 underline break-all" x-text="adminEmail"></a>.</li>
          </ol>

          <h4 class="font-bold text-slate-900 dark:text-white">Tindak lanjut</h4>
          <ul class="list-disc pl-5 space-y-1.5">
            <li>Admin meninjau laporan dan dapat meminta bukti izin dari pengunggah.</li>
            <li>Buku dapat disembunyikan sementara selama peninjauan, dan dihapus bila pelanggaran terbukti atau pengunggah tidak dapat menunjukkan haknya.</li>
            <li>Akun yang berulang kali melanggar dapat ditutup.</li>
          </ul>
        </div>
      </div>

      <!-- Footer modal -->
      <div class="p-3 sm:p-4 border-t border-slate-100 dark:border-slate-800 flex justify-end">
        <button type="button" @click="closeLegal()" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold transition">Tutup</button>
      </div>
    </div>
  </div>

  '''

JS_STATE_BLOCK = r'''    // State Halaman Informasi & Kebijakan (footer)
    isLegalModalOpen: false,
    legalPage: 'about', // 'about' | 'privacy' | 'terms' | 'copyright'
    adminEmail: ADMIN_EMAIL,
    legalTabs: { about: 'Tentang', privacy: 'Privasi', terms: 'Syarat', copyright: 'Hak Cipta' },
    legalTitles: {
      about: 'Tentang & Cara Kerja',
      privacy: 'Kebijakan Privasi',
      terms: 'Syarat & Ketentuan',
      copyright: 'Kebijakan Hak Cipta'
    },
'''

JS_METHOD_BLOCK = r'''   openLegal(page = 'about') {
     this.legalPage = page;
     this.isLegalModalOpen = true;
     this.$nextTick(() => { if (this.$refs.legalBody) this.$refs.legalBody.scrollTop = 0; });
   },

   closeLegal() {
     this.isLegalModalOpen = false;
   },

'''


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    html = read(HTML_FILE)
    js = read(JS_FILE)

    if "isLegalModalOpen" in html or "isLegalModalOpen" in js:
        print("Sudah pernah ditambal. Tidak ada yang diubah.")
        return

    problems = []
    if html.count(HTML_ANCHOR) != 1:
        problems.append(f"index.html: penanda '{HTML_ANCHOR}' ditemukan {html.count(HTML_ANCHOR)}x (harus 1x)")
    if js.count(JS_STATE_ANCHOR) != 1:
        problems.append(f"script.js: penanda state ditemukan {js.count(JS_STATE_ANCHOR)}x (harus 1x)")
    if js.count(JS_METHOD_ANCHOR) != 1:
        problems.append(f"script.js: penanda fungsi ditemukan {js.count(JS_METHOD_ANCHOR)}x (harus 1x)")
    if problems:
        print("Dibatalkan, tidak ada file yang diubah:")
        for p in problems:
            print(" -", p)
        sys.exit(1)

    shutil.copyfile(HTML_FILE, HTML_FILE + ".bak")
    shutil.copyfile(JS_FILE, JS_FILE + ".bak")

    html = html.replace(HTML_ANCHOR, HTML_BLOCK + HTML_ANCHOR)
    js = js.replace(JS_STATE_ANCHOR, JS_STATE_BLOCK + JS_STATE_ANCHOR)
    js = js.replace(JS_METHOD_ANCHOR, JS_METHOD_BLOCK + JS_METHOD_ANCHOR)

    write(HTML_FILE, html)
    write(JS_FILE, js)

    print("Selesai. Footer dan 4 halaman (Tentang, Privasi, Syarat, Hak Cipta) sudah ditambahkan.")
    print("Cadangan: index.html.bak dan script.js.bak")
    print("Naikkan versi script, misalnya script.js?v=2.4 menjadi script.js?v=2.5, agar browser memuat yang baru.")


if __name__ == "__main__":
    main()