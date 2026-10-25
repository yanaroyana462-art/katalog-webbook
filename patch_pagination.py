import shutil, sys

def patch(path, edits):
    src = open(path, encoding="utf-8").read()
    if "pagedBooks" in src:
        print(f"[lewati] {path} sudah dipatch")
        return
    shutil.copy(path, path + ".bak")
    for label, old, new in edits:
        n = src.count(old)
        if n != 1:
            sys.exit(f"[GAGAL] {path}: anchor '{label}' ditemukan {n}x (harus 1x). Tidak ada yang diubah.")
        src = src.replace(old, new)
    open(path, "w", encoding="utf-8").write(src)
    print(f"[ok] {path} (cadangan: {path}.bak)")

# ---------- script.js ----------
js_state = """sortBy: 'newest',
    currentPage: 1,
    perPage: 12,"""

js_init = """init() {
      ['searchQuery', 'selectedCategory', 'selectedAccess', 'selectedAuthor', 'scopeFilter', 'sortBy']
        .forEach(key => this.$watch(key, () => { this.currentPage = 1; }));
"""

js_getters = """get totalPages() {
     return Math.max(1, Math.ceil(this.filteredBooks.length / this.perPage));
   },

   get pagedBooks() {
     const start = (this.currentPage - 1) * this.perPage;
     return this.filteredBooks.slice(start, start + this.perPage);
   },

   get pageNumbers() {
     const total = this.totalPages, cur = this.currentPage;
     const pages = [];
     for (let i = 1; i <= total; i++) {
       if (i === 1 || i === total || Math.abs(i - cur) <= 1) pages.push(i);
       else if (pages[pages.length - 1] !== '...') pages.push('...');
     }
     return pages;
   },

   goToPage(n) {
     if (n < 1 || n > this.totalPages) return;
     this.currentPage = n;
     window.scrollTo({ top: 0, behavior: 'smooth' });
   },

   handleFileChange(event) {"""

patch("script.js", [
    ("state", "sortBy: 'newest',", js_state),
    ("init", "init() {\n", js_init),
    ("getters", "handleFileChange(event) {", js_getters),
    ("reset", "this.sortBy = 'newest';", "this.sortBy = 'newest';\n     this.currentPage = 1;"),
])

# ---------- dashboard.html ----------
nav = """<!-- Navigasi Halaman -->
    <nav x-show="totalPages > 1" class="mt-8 flex items-center justify-center gap-1.5 flex-wrap" aria-label="Navigasi halaman">
      <button type="button" @click="goToPage(currentPage - 1)" :disabled="currentPage === 1"
            class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-stone-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-stone-700 dark:text-slate-200 disabled:opacity-40 hover:bg-stone-50 dark:hover:bg-slate-700 transition">
        &larr; Sebelumnya
      </button>

      <template x-for="(p, i) in pageNumbers" :key="i">
        <button type="button" @click="p !== '...' && goToPage(p)" :disabled="p === '...'"
              class="min-w-[2rem] px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition"
              :class="p === currentPage
                ? 'bg-indigo-600 border-indigo-600 text-white'
                : 'bg-white dark:bg-slate-800 border-stone-200 dark:border-slate-700 text-stone-700 dark:text-slate-200 hover:bg-stone-50 dark:hover:bg-slate-700'"
              x-text="p"></button>
      </template>

      <button type="button" @click="goToPage(currentPage + 1)" :disabled="currentPage === totalPages"
            class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-stone-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-stone-700 dark:text-slate-200 disabled:opacity-40 hover:bg-stone-50 dark:hover:bg-slate-700 transition">
        Berikutnya &rarr;
      </button>
    </nav>

    <!-- Tampilan Jika Buku Tidak Ditemukan -->"""

patch("dashboard.html", [
    ("grid", 'x-for="(book, index) in filteredBooks"', 'x-for="(book, index) in pagedBooks"'),
    ("nav", "<!-- Tampilan Jika Buku Tidak Ditemukan -->", nav),
])
