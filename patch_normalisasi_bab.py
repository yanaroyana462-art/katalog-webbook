#!/usr/bin/env python3
"""
Patch Pustaka WebBook: konten bab dari Word tidak lagi menyatu.

Yang ditambal:
  script.js  -> normalisasi teks polos jadi <p>, pembersih paste Word,
                unggah .docx otomatis (mammoth.js), perbaikan unggah .txt/.md
  dashboard.html -> @paste pada textarea bab/subbab, label & placeholder ramah awam,
                cache-bust script.js

Cara pakai (di folder yang berisi script.js dan dashboard.html):
  python3 patch_normalisasi_bab.py
  python3 patch_normalisasi_bab.py /path/ke/folder

Aman dijalankan ulang (idempotent). File asli dicadangkan sebagai *.bak.
"""
import shutil
import subprocess
import sys
from pathlib import Path

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
JS = folder / "script.js"
HTML = folder / "dashboard.html"

for f in (JS, HTML):
    if not f.exists():
        sys.exit(f"File tidak ditemukan: {f}")

report = []


def patch(text, label, old, new, marker=None):
    """Ganti `old` dengan `new` tepat satu kali. Lewati bila sudah terpasang."""
    if marker and marker in text:
        report.append(f"= {label}: sudah terpasang, dilewati")
        return text
    n = text.count(old)
    if n == 0:
        report.append(f"! {label}: ANCHOR TIDAK DITEMUKAN (tambal manual)")
        return text
    if n > 1:
        report.append(f"! {label}: anchor muncul {n}x, dilewati demi keamanan")
        return text
    report.append(f"+ {label}: OK")
    return text.replace(old, new)


# ---------------------------------------------------------------
# Blok helper JS (disisipkan sebelum getSanitizedContent)
# ---------------------------------------------------------------
HELPERS = r"""// ===== Normalisasi konten bab (teks Word -> paragraf) =====
   hasBlockHtml(s) {
     return /<\s*(p|h[1-6]|ul|ol|li|table|blockquote|div|section|pre|br)\b/i.test(s);
   },

   escapeHtml(s) {
     return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
   },

   plainTextToHtml(text) {
     const t = String(text).replace(/\r\n?/g, '\n').trim();
     if (!t) return '';
     const hasInlineTags = /<[a-z][\s\S]*>/i.test(t);
     // Teks dari Word biasanya hanya satu \n antar paragraf: tiap baris = paragraf
     const paras = /\n\s*\n/.test(t) ? t.split(/\n\s*\n/) : t.split('\n');
     return paras
       .map(p => p.trim())
       .filter(Boolean)
       .map(p => {
         const body = hasInlineTags ? p : this.escapeHtml(p);
         return `<p>${body.replace(/\n/g, '<br>')}</p>`;
       })
       .join('');
   },

   normalizeChapterContent(raw) {
     if (!raw || !String(raw).trim()) return raw || '';
     return this.hasBlockHtml(raw) ? raw : this.plainTextToHtml(raw);
   },

   // ===== Pembersih paste dari Word =====
   cleanPastedHtml(html) {
     const doc = new DOMParser().parseFromString(html, 'text/html');
     doc.querySelectorAll('style,script,meta,link,xml').forEach(n => n.remove());
     const allowed = new Set(['P','H1','H2','H3','H4','UL','OL','LI','B','STRONG','I','EM','U','BR','TABLE','THEAD','TBODY','TR','TH','TD','BLOCKQUOTE','A','SUB','SUP']);
     const walk = (node) => {
       let out = '';
       node.childNodes.forEach(c => {
         if (c.nodeType === 3) {
           out += this.escapeHtml(c.nodeValue.replace(/\s+/g, ' '));
         } else if (c.nodeType === 1) {
           const tag = c.tagName;
           const inner = walk(c);
           if (!allowed.has(tag)) { out += inner; return; }
           const t = tag.toLowerCase();
           if (tag === 'BR') {
             out += '<br>';
           } else if (tag === 'A') {
             const h = c.getAttribute('href') || '';
             out += /^https?:/i.test(h)
               ? `<a href="${h.replace(/"/g, '&quot;')}" target="_blank" rel="noopener noreferrer">${inner}</a>`
               : inner;
           } else {
             out += `<${t}>${inner}</${t}>`;
           }
         }
       });
       return out;
     };
     return walk(doc.body).replace(/<p>\s*<\/p>/g, '');
   },

   handleContentPaste(e, obj) {
     const html = e.clipboardData && e.clipboardData.getData('text/html');
     if (!html) return; // teks polos: biarkan, nanti dinormalisasi saat render/simpan
     e.preventDefault();
     const clean = this.cleanPastedHtml(html);
     const ta = e.target;
     const s = ta.selectionStart, en = ta.selectionEnd;
     const cur = obj.content || '';
     obj.content = cur.slice(0, s) + clean + cur.slice(en);
   },

   async loadMammoth() {
     if (window.mammoth) return window.mammoth;
     await new Promise((resolve, reject) => {
       const s = document.createElement('script');
       s.src = 'https://cdn.jsdelivr.net/npm/mammoth@1.8.0/mammoth.browser.min.js';
       s.onload = resolve;
       s.onerror = () => reject(new Error('Gagal memuat modul pembaca DOCX.'));
       document.head.appendChild(s);
     });
     return window.mammoth;
   },

   async importDocx(file) {
     try {
       this.showToast('Membaca berkas Word...', 'info');
       const mammoth = await this.loadMammoth();
       const buf = await file.arrayBuffer();
       const { value } = await mammoth.convertToHtml({ arrayBuffer: buf });
       if (!value || !value.trim()) return;

       const untouched = this.uploadForm.chapters.every(c => !(c.title || '').trim() && !(c.content || '').trim());
       const parts = value.split(/(?=<h1[^>]*>)/i).filter(s => s.trim());

       if (untouched && /<h1/i.test(value) && parts.length > 1) {
         // Pecah otomatis per Heading 1 menjadi bab-bab terpisah
         this.uploadForm.chapters = parts.map(p => {
           const m = p.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
           const title = m ? m[1].replace(/<[^>]+>/g, '').trim() : '';
           return { title, content: p.replace(/<h1[^>]*>[\s\S]*?<\/h1>/i, '').trim(), subchapters: [] };
         });
         this.showToast(`Naskah dipecah menjadi ${parts.length} bab otomatis.`, 'success');
       } else if (!(this.uploadForm.chapters[0].content || '').trim()) {
         this.uploadForm.chapters[0].content = value;
         this.showToast('Isi naskah Word dimasukkan ke Bab 1.', 'success');
       }
     } catch (err) {
       this.showToast('Gagal membaca DOCX: ' + err.message, 'error');
     }
   },

   """

# ---------------------------------------------------------------
# script.js
# ---------------------------------------------------------------
shutil.copy(JS, str(JS) + ".bak")
js = JS.read_text(encoding="utf-8")

js = patch(
    js,
    "script.js: helper + normalisasi di getSanitizedContent",
    "getSanitizedContent(rawHtml) {",
    HELPERS
    + "getSanitizedContent(rawHtml) {\n     rawHtml = this.normalizeChapterContent(rawHtml);",
    marker="normalizeChapterContent(raw) {",
)

js = patch(
    js,
    "script.js: normalisasi bab saat simpan",
    "content: chap.content.trim() || (idx === 0",
    "content: this.normalizeChapterContent(chap.content.trim()) || (idx === 0",
    marker="normalizeChapterContent(chap.content.trim())",
)

js = patch(
    js,
    "script.js: normalisasi subbab saat simpan",
    "content: subchapter.content.trim() || '<p class=\"text-slate-400 italic\">Konten subbab ini belum tersedia.</p>'",
    "content: this.normalizeChapterContent(subchapter.content.trim()) || '<p class=\"text-slate-400 italic\">Konten subbab ini belum tersedia.</p>'",
    marker="normalizeChapterContent(subchapter.content.trim())",
)

js = patch(
    js,
    "script.js: unggah .txt/.md pakai normalisasi",
    r"`<p>${text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>')}</p>`",
    "this.normalizeChapterContent(text)",
    marker="chapters[0].content = this.normalizeChapterContent(text)",
)

js = patch(
    js,
    "script.js: unggah .docx otomatis",
    "const textExtensions = ['txt', 'md', 'markdown', 'html', 'json'];",
    "if (file.name.split('.').pop().toLowerCase() === 'docx') this.importDocx(file);\n"
    "     const textExtensions = ['txt', 'md', 'markdown', 'html', 'json'];",
    marker="this.importDocx(file)",
)

JS.write_text(js, encoding="utf-8")

# ---------------------------------------------------------------
# dashboard.html
# ---------------------------------------------------------------
shutil.copy(HTML, str(HTML) + ".bak")
html = HTML.read_text(encoding="utf-8")

html = patch(
    html,
    "dashboard.html: textarea bab (paste Word)",
    '<textarea x-model="chap.content" rows="3" placeholder="Tuliskan isi materi bab di sini..."',
    '<textarea x-model="chap.content" rows="8" @paste="handleContentPaste($event, chap)" '
    'placeholder="Tempel naskah dari Word di sini, atau ketik biasa. Enter = paragraf baru."',
    marker='@paste="handleContentPaste($event, chap)"',
)

html = patch(
    html,
    "dashboard.html: textarea subbab (paste Word)",
    '<textarea x-model="subchap.content" rows="3" placeholder="Tuliskan isi materi subbab di sini..."',
    '<textarea x-model="subchap.content" rows="6" @paste="handleContentPaste($event, subchap)" '
    'placeholder="Tempel naskah dari Word di sini, atau ketik biasa."',
    marker='@paste="handleContentPaste($event, subchap)"',
)

html = patch(
    html,
    "dashboard.html: label 'HTML / Teks'",
    '<span class="text-[10px] text-slate-400">HTML / Teks</span>',
    '<span class="text-[10px] text-slate-400">Tempel dari Word atau ketik biasa</span>',
    marker="Tempel dari Word atau ketik biasa</span>",
)

html = patch(
    html,
    "dashboard.html: cache-bust script.js",
    "script.js?v=2.8",
    "script.js?v=2.9",
    marker="script.js?v=2.9",
)

HTML.write_text(html, encoding="utf-8")

# ---------------------------------------------------------------
# Laporan + cek sintaks JS (bila node tersedia)
# ---------------------------------------------------------------
print("\n".join(report))
try:
    r = subprocess.run(["node", "--check", str(JS)], capture_output=True, text=True)
    if r.returncode == 0:
        print("\nCek sintaks script.js: OK")
    else:
        print("\nCek sintaks script.js GAGAL:\n" + r.stderr)
        print("Pulihkan dengan: cp script.js.bak script.js")
except FileNotFoundError:
    print("\n(node tidak ditemukan, cek sintaks dilewati)")

print("\nSelesai. Cadangan: script.js.bak dan dashboard.html.bak")