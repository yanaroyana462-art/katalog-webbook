p = 'script.js'
s = open(p, encoding='utf-8').read()

def swap(old, new):
    global s
    assert s.count(old) == 1, 'Tidak ketemu / ganda: ' + old[:60]
    s = s.replace(old, new)

# 1) State baru untuk modal Beri Akses
swap("currentView: 'catalog', // 'catalog' | 'upload'",
"""currentView: 'catalog', // 'catalog' | 'upload'
    isGrantModalOpen: false,
    isGranting: false,
    grantEmail: '',
    grantBookId: '',
    grantResult: '',""")

# 2) Fungsi baru
swap("resetFilters() {",
"""get paidBooks() {
     return this.catalog.filter(b => b.accessType === 'Berbayar');
   },

   openGrantModal() {
     this.grantEmail = '';
     this.grantBookId = '';
     this.grantResult = '';
     this.isGrantModalOpen = true;
   },

   closeGrantModal() {
     if (this.isGranting) return;
     this.isGrantModalOpen = false;
   },

   async grantAccess() {
     if (!this.isAdmin || !this.supabaseClient) return;
     const email = this.grantEmail.trim().toLowerCase();
     const bookId = Number(this.grantBookId);
     if (!email || !bookId) {
       this.grantResult = '❌ Isi email pembeli dan pilih bukunya dulu.';
       return;
     }
     this.isGranting = true;
     this.grantResult = '';
     try {
       const { data, error } = await this.supabaseClient.rpc('grant_book_access', { p_email: email, p_book_id: bookId });
       if (error) throw error;
       const book = this.catalog.find(b => String(b.id) === String(bookId));
       const title = book ? book.title : 'buku';
       if (data === 'OK') {
         this.grantResult = `✅ Akses "${title}" sudah diberikan ke ${email}.`;
         this.grantEmail = '';
       } else if (data === 'ALREADY') {
         this.grantResult = `ℹ️ ${email} sudah punya akses ke "${title}".`;
       } else if (data === 'EMAIL_NOT_FOUND') {
         this.grantResult = `❌ Email ${email} belum terdaftar. Minta pembeli daftar dulu di Pustaka WebBook.`;
       } else {
         this.grantResult = '⚠️ Respon tidak dikenal: ' + data;
       }
     } catch (err) {
       this.grantResult = '❌ Gagal: ' + (err.message || err);
     } finally {
       this.isGranting = false;
     }
   },

   resetFilters() {""")

# 3) Tutup celah localStorage: status pembelian hanya dari database
swap("const savedPurchases = localStorage.getItem('purchasedBookIds');",
     "const savedPurchases = null; localStorage.removeItem('purchasedBookIds');")
swap("this.purchasedBookIds = [...new Set([...this.purchasedBookIds, ...remoteIds])];",
     "this.purchasedBookIds = remoteIds;")
swap("localStorage.setItem('purchasedBookIds', JSON.stringify(this.purchasedBookIds));",
     "// status pembelian tidak lagi disimpan di browser")

open(p, 'w', encoding='utf-8').write(s)
print('Selesai, script.js berhasil ditambal')