// Konfigurasi Kredensial Supabase
const SUPABASE_URL = 'https://klumtyeooujhonbrhnzv.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_GFJBw5j2h8_AdR_ge2ci-Q_WtiBCFtb';
const SUPABASE_STORAGE_BUCKET = 'books'; // Nama Supabase Storage Bucket (Public)
const ADMIN_WHATSAPP_NUMBER = '6285794506290'; // Sesuaikan dengan nomor WhatsApp Admin (awali dengan 62)

function portalEngine() {
  return {
    currentView: 'catalog', // 'catalog' | 'upload'
    
    // Auth State
    currentUser: null,
    authMode: 'login', // 'login' | 'register'
    authEmail: '',
    authPassword: '',
    authLoading: false,
    authError: '',
    authSuccess: '',
    darkMode: false,
    supabaseClient: null,
    isSaving: false,
    isLoadingChapters: false,
    isTocDrawerOpen: false,
    activeBook: null,
    readerTab: 'overview', // 'overview' | 'text' | 'document' | 'external'
    isEmbedFullscreen: false,
    activeBookSignedUrl: '',
    isFloatingBookNavOpen: false,
    floatingBookSearch: '',
    isDownloadingPdf: false,
    isLoadingDocument: false,
    currentChapterIndex: 0,
    isSpeaking: false,
    synth: window.speechSynthesis,
    readerFontSize: 16,

    // Toast Notifikasi
    toast: { show: false, message: '', type: 'info', timeout: null },
    showToast(message, type = 'info') {
      this.toast.message = message;
      this.toast.type = type;
      this.toast.show = true;
      clearTimeout(this.toast.timeout);
      this.toast.timeout = setTimeout(() => { this.toast.show = false; }, 3500);
    },

    // State Modal Edit Profil Saya
    isProfileModalOpen: false,
    isUpdatingProfile: false,
    profileForm: {
      author: '',
      authorBio: '',
      authorPhoto: '',
      authorPhotoFile: null,
      authorLinks: { instagram: '', x: '', facebook: '', tiktok: '', linkedin: '', whatsapp: '', website: '' }
    },

    get book() {
      return this.activeBook;
    },

    // State Modal Checkout Pembayaran
    adminWaNumber: ADMIN_WHATSAPP_NUMBER,
    isPaymentModalOpen: false,
    checkoutBook: null,
    selectedPaymentMethod: 'qris',
    isProcessingPayment: false,
    paymentMethods: [
      { id: 'qris', name: 'QRIS / E-Wallet', desc: 'GoPay, OVO, ShopeePay, Dana', badge: 'Instan' },
      { id: 'va', name: 'Virtual Account', desc: 'BCA, Mandiri, BNI, BRI', badge: 'Otomatis' },
      { id: 'cc', name: 'Kartu Kredit / Debit', desc: 'Visa, Mastercard, JCB', badge: 'Aman' }
    ],
    purchasedBookIds: [],

    // State Modal Bagikan Buku
    isShareModalOpen: false,
    shareBookData: null,
    isLinkCopied: false,
    get isNativeShareSupported() {
      return typeof navigator !== 'undefined' && Boolean(navigator.share);
    },

    // State Modal Edit Buku
    isEditModalOpen: false,
    isUpdatingBook: false,
    editForm: {
      originalBook: null,
      category: '',
      id: '',
      title: '',
      author: '',
      authorBio: '',
      authorPhoto: '',
      authorPhotoFile: null,
      blurb: '',
      authorLinks: {
        instagram: '',
        x: '',
        facebook: '',
        tiktok: '',
        linkedin: '',
        whatsapp: '',
        website: ''
      },
      price: 0,
      external_link: ''
    },

    // State Filter
    scopeFilter: 'all', // 'all' | 'my-books'
    searchQuery: '',
    selectedCategory: 'Semua',
    selectedAccess: 'Semua',
    selectedAuthor: 'Semua Penulis',
    accessOptions: ['Semua', 'Gratis', 'Semi Berbayar', 'Berbayar'],
    sortBy: 'newest',

    // State Modal Media Sosial Penulis
    isAuthorSocialModalOpen: false,
    socialModalTarget: 'upload', // 'upload' | 'edit'
    socialModalForm: {
      instagram: '',
      x: '',
      facebook: '',
      tiktok: '',
      linkedin: '',
      whatsapp: '',
      website: ''
    },

    // Daftar Kategori Dinamis
    categories: ['Semua', 'Teknologi & AI', 'Edukasi & Parenting', 'Bisnis & SOP', 'Agama & Pemikiran'],

    init() {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        this.darkMode = true;
        document.documentElement.classList.add('dark');
      } else {
        this.darkMode = false;
        document.documentElement.classList.remove('dark');
      }

      const savedSize = localStorage.getItem('readerFontSize');
      if (savedSize) {
        this.readerFontSize = parseInt(savedSize, 10) || 16;
      }

      const savedPurchases = localStorage.getItem('purchasedBookIds');
      if (savedPurchases) {
        try {
          this.purchasedBookIds = JSON.parse(savedPurchases);
        } catch (e) {
          this.purchasedBookIds = [];
        }
      }

      // Inisialisasi Supabase
      if (window.supabase && SUPABASE_URL !== 'https://YOUR_PROJECT_ID.supabase.co') {
        this.supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        
        // Cek Sesi Pengguna Aktif
        this.supabaseClient.auth.getSession().then(({ data: { session } }) => {
          this.currentUser = session?.user || null;
          if (this.currentUser) {
            this.fetchUserPurchases();
            this.loadAuthorProfile();
          }
        });

        this.supabaseClient.auth.onAuthStateChange((_event, session) => {
          this.currentUser = session?.user || null;
          if (this.currentUser) {
            this.fetchUserPurchases();
            this.loadAuthorProfile();
          }
        });

        this.fetchBooks();
      }
    },

    async fetchBooks() {
      if (!this.supabaseClient) return;
      try {
        const { data, error } = await this.supabaseClient
          .from('books')
          .select('*')
          .order('created_at', { ascending: false });

        if (error) throw error;

        if (data && data.length > 0) {
          const chaptersByBook = {};
          try {
            const { data: chData } = await this.supabaseClient
              .from('chapters')
              .select('id, book_id, title, chapter_order, is_preview')
              .order('chapter_order', { ascending: true });

            if (chData) {
              chData.forEach(ch => {
                const bId = String(ch.book_id);
                if (!chaptersByBook[bId]) chaptersByBook[bId] = [];
                chaptersByBook[bId].push(ch);
              });
            }
          } catch (chErr) {
            console.warn('Gagal memuat relasi chapters:', chErr);
          }

          this.catalog = data.map(item => {
            const bookIdStr = String(item.id);
            const bookChapters = chaptersByBook[bookIdStr] || (Array.isArray(item.chapters) && item.chapters.length > 0 ? item.chapters : null);
            return {
              id: String(item.id),
              userId: item.user_id || null,
              title: item.title,
              category: item.category,
              author: item.author,
              authorBio: item.author_bio || null,
              authorPhoto: item.author_photo || null,
              authorLinks: item.author_links || null,
              createdAt: item.created_at ? item.created_at.split('T')[0] : new Date().toISOString().split('T')[0],
              blurb: item.blurb,
              accessType: item.access_type || 'Gratis',
              price: item.price || 0,
              isPrivate: Boolean(item.is_private),
              coverUrl: item.cover_url || '',
              fileName: item.file_name || null,
              external_link: item.external_link || null,
              fileUrl: item.file_url || null,
              chapters: bookChapters && bookChapters.length > 0 
                ? bookChapters.sort((a, b) => (a.chapter_order || 0) - (b.chapter_order || 0))
                : [{
                    title: 'Bab 1: Pengantar ' + item.title,
                    content: ''
                  }]
            };
          });

          const fetchedCategories = [...new Set(this.catalog.map(b => b.category))];
          this.categories = ['Semua', ...new Set([...this.categories.slice(1), ...fetchedCategories])];

          if (this.currentUser) {
            this.loadAuthorProfile();
          }

          const urlParams = new URLSearchParams(window.location.search);
          const sharedBookId = urlParams.get('book');
          if (sharedBookId) {
            const targetBook = this.catalog.find(b => String(b.id) === String(sharedBookId));
            if (targetBook) {
              this.openBook(targetBook);
            }
          }
        }
      } catch (err) {
        console.error('Gagal mengambil data dari Supabase:', err.message);
      }
    },

    async fetchUserPurchases() {
      if (!this.supabaseClient || !this.currentUser) return;
      try {
        const { data, error } = await this.supabaseClient
          .from('purchases')
          .select('book_id')
          .eq('user_id', this.currentUser.id);
        if (!error && data && data.length > 0) {
          const remoteIds = data.map(row => String(row.book_id));
          this.purchasedBookIds = [...new Set([...this.purchasedBookIds, ...remoteIds])];
          localStorage.setItem('purchasedBookIds', JSON.stringify(this.purchasedBookIds));
        }
      } catch (err) {
        console.error('Gagal mengambil riwayat pembelian akun:', err);
      }
    },

    toggleDarkMode() {
      this.darkMode = !this.darkMode;
      localStorage.setItem('theme', this.darkMode ? 'dark' : 'light');
      if (this.darkMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    },

    get availableCategories() {
      return this.categories.filter(c => c !== 'Semua');
    },

    get floatingBooks() {
      const q = this.floatingBookSearch ? this.floatingBookSearch.toLowerCase().trim() : '';
      return this.catalog.filter(b => !q || b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q));
    },

    get authorList() {
      return [...new Set(this.catalog.map(b => b.author))].sort();
    },

    async handleAuth() {
      if (!this.supabaseClient) {
        this.authError = 'Layanan database belum terhubung.';
        return;
      }
      this.authLoading = true;
      this.authError = '';
      this.authSuccess = '';

      try {
        if (this.authMode === 'login') {
          const { data, error } = await this.supabaseClient.auth.signInWithPassword({
            email: this.authEmail,
            password: this.authPassword
          });
          if (error) throw error;
          this.currentUser = data.user;
          this.authPassword = '';
          this.loadAuthorProfile();
          await this.fetchBooks();
        } else {
          const { data, error } = await this.supabaseClient.auth.signUp({
            email: this.authEmail,
            password: this.authPassword
          });
          if (error) throw error;
          this.authSuccess = 'Pendaftaran berhasil! Silakan periksa email Anda jika verifikasi aktif, atau langsung masuk.';
          if (data.session) {
            this.currentUser = data.user;
            await this.fetchBooks();
            this.loadAuthorProfile();
          }
        }
      } catch (err) {
        this.authError = err.message || 'Terjadi kesalahan saat otentikasi.';
      } finally {
        this.authLoading = false;
      }
    },

    async handleLogout() {
      this.stopTTS();
      if (this.supabaseClient) {
        await this.supabaseClient.auth.signOut();
      }
      this.currentUser = null;
      this.scopeFilter = 'all';
      this.purchasedBookIds = [];
      this.activeBook = null;
      this.activeBookSignedUrl = '';
      localStorage.removeItem('purchasedBookIds');
      this.clearAuthorProfileFromForm();
      await this.fetchBooks();
    },

    async saveAuthorProfileLocally(profile) {
      if (!this.currentUser) return;
      try {
        localStorage.setItem('author_profile_' + this.currentUser.id, JSON.stringify(profile));
      } catch (e) {
        console.warn('Gagal menyimpan profil penulis secara lokal:', e);
      }

      if (this.supabaseClient) {
        try {
          const { error } = await this.supabaseClient
            .from('profiles')
            .upsert({
              id: this.currentUser.id,
              author: profile.author || null,
              author_bio: profile.authorBio || null,
              author_photo: profile.authorPhoto || null,
              author_links: profile.authorLinks || {},
              updated_at: new Date().toISOString()
            }, { onConflict: 'id' });
          if (error) console.warn('Gagal sinkronisasi profil ke Supabase:', error.message);
        } catch (err) {
          console.warn('Kesalahan saat upsert profil ke Supabase:', err);
        }
      }
    },

    async loadAuthorProfile() {
      if (!this.currentUser) return;
      try {
        const raw = localStorage.getItem('author_profile_' + this.currentUser.id);
        let profile = raw ? JSON.parse(raw) : null;

        if (this.supabaseClient) {
          const { data, error } = await this.supabaseClient
            .from('profiles')
            .select('author, author_bio, author_photo, author_links')
            .eq('id', this.currentUser.id)
            .maybeSingle();

          if (!error && data) {
            profile = {
              author: data.author || '',
              authorBio: data.author_bio || '',
              authorPhoto: data.author_photo || '',
              authorLinks: data.author_links || { instagram: '', x: '', facebook: '', tiktok: '', linkedin: '', whatsapp: '', website: '' }
            };
            localStorage.setItem('author_profile_' + this.currentUser.id, JSON.stringify(profile));
          }
        }

        if (!profile && this.catalog && this.catalog.length > 0) {
          const myLastBook = this.catalog.find(b => b.userId === this.currentUser.id);
          if (myLastBook) {
            profile = {
              author: myLastBook.author || '',
              authorBio: myLastBook.authorBio || '',
              authorPhoto: myLastBook.authorPhoto || '',
              authorLinks: myLastBook.authorLinks || { instagram: '', x: '', facebook: '', tiktok: '', linkedin: '', whatsapp: '', website: '' }
            };
            this.saveAuthorProfileLocally(profile);
          }
        }

        if (profile) {
          if (profile.author && !this.uploadForm.author) this.uploadForm.author = profile.author;
          if (profile.authorBio && !this.uploadForm.authorBio) this.uploadForm.authorBio = profile.authorBio;
          if (profile.authorPhoto && !this.uploadForm.authorPhoto) this.uploadForm.authorPhoto = profile.authorPhoto;
          if (profile.authorLinks && !this.hasAuthorLinks(this.uploadForm.authorLinks)) {
            this.uploadForm.authorLinks = JSON.parse(JSON.stringify(profile.authorLinks));
          }
        }
      } catch (e) {
        console.warn('Gagal memuat profil penulis:', e);
      }
    },

    clearAuthorProfileFromForm() {
      this.uploadForm.author = '';
      this.uploadForm.authorBio = '';
      this.uploadForm.authorPhoto = '';
      this.uploadForm.authorPhotoFile = null;
      this.uploadForm.authorLinks = { instagram: '', x: '', facebook: '', tiktok: '', linkedin: '', whatsapp: '', website: '' };
    },

    openProfileModal() {
      this.profileForm = {
        author: this.uploadForm.author || '',
        authorBio: this.uploadForm.authorBio || '',
        authorPhoto: this.uploadForm.authorPhoto || '',
        authorPhotoFile: null,
        authorLinks: this.uploadForm.authorLinks 
          ? JSON.parse(JSON.stringify(this.uploadForm.authorLinks)) 
          : { instagram: '', x: '', facebook: '', tiktok: '', linkedin: '', whatsapp: '', website: '' }
      };
      this.isProfileModalOpen = true;
    },

    closeProfileModal() {
      if (this.isUpdatingProfile) return;
      this.isProfileModalOpen = false;
      this.profileForm.authorPhotoFile = null;
    },

    handleProfilePhotoUpload(event) {
      const file = event.target.files[0];
      if (file) {
        if (file.size > 2 * 1024 * 1024) {
          this.showToast('Ukuran foto profil melebihi batas 2 MB.', 'error');
          event.target.value = '';
          return;
        }
        this.profileForm.authorPhotoFile = file;
        const reader = new FileReader();
        reader.onload = (e) => { this.profileForm.authorPhoto = e.target.result; };
        reader.readAsDataURL(file);
      }
    },

    async saveProfileModal() {
      if (!this.profileForm.author.trim()) return;
      this.isUpdatingProfile = true;
      try {
        let uploadedPhoto = this.profileForm.authorPhoto;
        if (this.supabaseClient && this.profileForm.authorPhotoFile) {
          const cleanName = this.profileForm.authorPhotoFile.name.replace(/[^a-zA-Z0-9._-]/g, '_');
          const photoPath = `authors/${Date.now()}_${cleanName}`;
          const res = await this.uploadToStorage(SUPABASE_STORAGE_BUCKET, photoPath, this.profileForm.authorPhotoFile);
          if (res) uploadedPhoto = res;
        }
        const updated = {
          author: this.profileForm.author.trim(),
          authorBio: this.profileForm.authorBio ? this.profileForm.authorBio.trim() : '',
          authorPhoto: uploadedPhoto ? uploadedPhoto.trim() : '',
          authorLinks: this.profileForm.authorLinks || {}
        };
        await this.saveAuthorProfileLocally(updated);

        if (this.supabaseClient && this.currentUser) {
          const bookPayload = {
            author: updated.author,
            author_bio: updated.authorBio || null,
            author_photo: updated.authorPhoto || null,
            author_links: updated.authorLinks || null
          };

          let { error: bookUpdateErr } = await this.supabaseClient
            .from('books')
            .update(bookPayload)
            .eq('user_id', this.currentUser.id);

         if (bookUpdateErr && (bookUpdateErr.message?.includes('author_bio') || bookUpdateErr.message?.includes('author_photo') || bookUpdateErr.message?.includes('author_links'))) {
           delete bookPayload.author_bio;
           delete bookPayload.author_photo;
           delete bookPayload.author_links;
           await this.supabaseClient
             .from('books')
             .update(bookPayload)
             .eq('user_id', this.currentUser.id);
         }
       }

       this.catalog.forEach(b => {
         if (this.currentUser && b.userId === this.currentUser.id) {
           b.author = updated.author;
           b.authorBio = updated.authorBio;
           b.authorPhoto = updated.authorPhoto;
           b.authorLinks = updated.authorLinks;
         }
       });

       if (this.activeBook && this.currentUser && this.activeBook.userId === this.currentUser.id) {
         Object.assign(this.activeBook, updated);
       }
       await this.loadAuthorProfile();

       this.uploadForm.author = updated.author;
       this.uploadForm.authorBio = updated.authorBio;
       this.uploadForm.authorPhoto = updated.authorPhoto;
       this.uploadForm.authorLinks = JSON.parse(JSON.stringify(updated.authorLinks || {}));

       this.closeProfileModal();
       this.showToast('Profil penulis berhasil diperbarui.', 'success');
     } catch (err) {
       this.showToast('Gagal menyimpan profil: ' + err.message, 'error');
     } finally {
       this.isUpdatingProfile = false;
     }
   },

   // Form Upload State
   isDragging: false,
   uploadMessage: { text: '', type: 'success' },
   isEditingId: null,
   uploadForm: {
     title: '',
     author: '',
     authorBio: '',
     authorPhoto: '',
     authorPhotoFile: null,
     authorLinks: {
       instagram: '',
       x: '',
       facebook: '',
       tiktok: '',
       linkedin: '',
       whatsapp: '',
       website: ''
     },
     foreword: '',
     introduction: '',
     glossary: '',
     bibliography: '',
     category: 'Teknologi & AI',
     accessType: 'Gratis',
     price: 0,
     isPrivate: 'false',
     coverUrl: '',
     coverFile: null,
     external_link: '',
     blurb: '',
     chapters: [
       { title: '', content: '' }
     ],
     file: null,
     fileName: '',
     fileSize: '',
     fileExtension: '',
     fileUrl: ''
   },

   addChapter() {
     this.uploadForm.chapters.push({ title: '', content: '' });
   },

   removeChapter(index) {
     if (this.uploadForm.chapters.length > 1) {
       this.uploadForm.chapters.splice(index, 1);
     }
   },

   // Data Katalogs
   catalog: [],

   get filteredBooks() {
     return this.catalog.filter(book => {
       if (book.isPrivate && (!this.currentUser || book.userId !== this.currentUser.id)) return false;

       if (this.scopeFilter === 'my-books') {
         if (!this.currentUser || book.userId !== this.currentUser.id) return false;
       }

       const matchesCategory = this.selectedCategory === 'Semua' || book.category === this.selectedCategory;
       const matchesAccess = this.selectedAccess === 'Semua' || book.accessType === this.selectedAccess;
       const matchesAuthor = this.selectedAuthor === 'Semua Penulis' || book.author === this.selectedAuthor;
       
       const q = this.searchQuery.toLowerCase().trim();
       const matchesQuery = q === '' || 
                            book.title.toLowerCase().includes(q) || 
                            book.author.toLowerCase().includes(q);

       return matchesCategory && matchesAccess && matchesAuthor && matchesQuery;
     }).sort((a, b) => {
       if (this.sortBy === 'title') return a.title.localeCompare(b.title);
       if (this.sortBy === 'author') return a.author.localeCompare(b.author);
       if (this.sortBy === 'newest') return new Date(b.createdAt) - new Date(a.createdAt);
       return 0;
     });
   },

   handleFileChange(event) {
     const files = event.target.files;
     if (files && files.length > 0) {
       this.processSelectedFile(files[0]);
     }
   },

   handleFileDrop(event) {
     this.isDragging = false;
     const files = event.dataTransfer.files;
     if (files && files.length > 0) {
       this.processSelectedFile(files[0]);
     }
   },

   processSelectedFile(file) {
     const MAX_DOC_SIZE_MB = 15;
     if (file.size > MAX_DOC_SIZE_MB * 1024 * 1024) {
       this.showToast(`Ukuran berkas melebihi batas maksimal ${MAX_DOC_SIZE_MB} MB.`, 'error');
       this.clearFile();
       return;
     }

     this.uploadForm.file = file;
     this.uploadForm.fileName = file.name;
     
     const sizeInKB = (file.size / 1024).toFixed(1);
     this.uploadForm.fileSize = file.size > 1024 * 1024 
       ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` 
       : `${sizeInKB} KB`;

     const ext = file.name.split('.').pop().toUpperCase();
     this.uploadForm.fileExtension = ext;

     if (!this.uploadForm.title) {
       const cleanName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
       this.uploadForm.title = cleanName.replace(/[-_]/g, ' ');
     }

     const textExtensions = ['txt', 'md', 'markdown', 'html', 'json'];
     const fileExtLower = file.name.split('.').pop().toLowerCase();
     if (textExtensions.includes(fileExtLower)) {
       const reader = new FileReader();
       reader.onload = (e) => {
         const text = e.target.result;
         if (this.uploadForm.chapters.length > 0 && !this.uploadForm.chapters[0].content) {
           this.uploadForm.chapters[0].content = `<p>${text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>')}</p>`;
         }
       };
       reader.readAsText(file);
     }
   },

   handleCoverUpload(event) {
     const file = event.target.files[0];
     if (file) {
       const MAX_IMG_SIZE_MB = 2;
       if (file.size > MAX_IMG_SIZE_MB * 1024 * 1024) {
         this.showToast(`Ukuran gambar sampul melebihi ${MAX_IMG_SIZE_MB} MB.`, 'error');
         event.target.value = '';
         return;
       }

       if (!file.type.startsWith('image/')) {
         this.showToast('Silakan pilih berkas gambar yang valid (JPG, PNG, WebP).', 'error');
         return;
       }
       this.uploadForm.coverFile = file;
       const reader = new FileReader();
       reader.onload = (e) => {
         this.uploadForm.coverUrl = e.target.result;
       };
       reader.readAsDataURL(file);
     }
   },

   handleAuthorPhotoUpload(event) {
     const file = event.target.files[0];
     if (file) {
       const MAX_IMG_SIZE_MB = 2;
       if (file.size > MAX_IMG_SIZE_MB * 1024 * 1024) {
         this.showToast(`Ukuran foto penulis melebihi ${MAX_IMG_SIZE_MB} MB.`, 'error');
         event.target.value = '';
         return;
       }
       if (!file.type.startsWith('image/')) {
         this.showToast('Silakan pilih berkas gambar yang valid (JPG, PNG, WebP).', 'error');
         return;
       }
       this.uploadForm.authorPhotoFile = file;
       const reader = new FileReader();
       reader.onload = (e) => {
         this.uploadForm.authorPhoto = e.target.result;
       };
       reader.readAsDataURL(file);
     }
   },

   handleEditAuthorPhotoUpload(event) {
     const file = event.target.files[0];
     if (file) {
       const MAX_IMG_SIZE_MB = 2;
       if (file.size > MAX_IMG_SIZE_MB * 1024 * 1024) {
         this.showToast(`Ukuran foto penulis melebihi ${MAX_IMG_SIZE_MB} MB.`, 'error');
         event.target.value = '';
         return;
       }
       if (!file.type.startsWith('image/')) {
         this.showToast('Silakan pilih berkas gambar yang valid (JPG, PNG, WebP).', 'error');
         return;
       }
       this.editForm.authorPhotoFile = file;
       const reader = new FileReader();
       reader.onload = (e) => {
         this.editForm.authorPhoto = e.target.result;
       };
       reader.readAsDataURL(file);
     }
   },

   clearFile() {
     this.uploadForm.file = null;
     this.uploadForm.fileName = '';
     this.uploadForm.fileSize = '';
     this.uploadForm.fileExtension = '';
     this.uploadForm.fileUrl = '';
     if (this.$refs.fileInput) {
       this.$refs.fileInput.value = '';
     }
   },

   async uploadToStorage(bucketName, filePath, file) {
     const { error: uploadError } = await this.supabaseClient.storage
       .from(bucketName)
       .upload(filePath, file, {
         cacheControl: '3600',
         upsert: true
       });

     if (uploadError) {
       throw new Error(`Unggah berkas [${filePath}] gagal: ${uploadError.message}`);
     }

     const { data } = this.supabaseClient.storage
       .from(bucketName)
       .getPublicUrl(filePath);

     return data?.publicUrl || '';
   },

   async saveNewBook() {
     const preliminaryChapters = [];
     if (this.uploadForm.foreword && this.uploadForm.foreword.trim()) {
       preliminaryChapters.push({
         title: 'Kata Pengantar',
         content: `<p>${this.uploadForm.foreword.trim().replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>')}</p>`
       });
     }
     if (this.uploadForm.introduction && this.uploadForm.introduction.trim()) {
       preliminaryChapters.push({
         title: 'Pendahuluan',
         content: `<p>${this.uploadForm.introduction.trim().replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>')}</p>`
       });
     }

     const userChapters = this.uploadForm.chapters
       .filter(chap => chap.title.trim() || chap.content.trim())
       .map((chap, idx) => ({
         title: chap.title.trim() || `Bab ${idx + 1}: ${this.uploadForm.title.trim() || 'Materi'}`,
         content: chap.content.trim() || (idx === 0 
           ? `<p>${this.uploadForm.blurb.trim()}</p><p class="text-xs text-slate-500 mt-4 italic">Dokumen terlampir: ${this.uploadForm.fileName || 'Tidak ada file fisik'}</p>`
           : '<p class="text-slate-400 italic">Konten bab ini belum tersedia.</p>')
       }));

     const concludingChapters = [];
     if (this.uploadForm.glossary && this.uploadForm.glossary.trim()) {
       concludingChapters.push({
         title: 'Glosarium',
         content: `<p>${this.uploadForm.glossary.trim().replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>')}</p>`
       });
     }
     if (this.uploadForm.bibliography && this.uploadForm.bibliography.trim()) {
       concludingChapters.push({
         title: 'Daftar Pustaka',
         content: `<p>${this.uploadForm.bibliography.trim().replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>')}</p>`
       });
     }

     let formattedChapters = [...preliminaryChapters, ...userChapters, ...concludingChapters];
     if (formattedChapters.length === 0) {
       formattedChapters = [{
         title: `Bab 1: Pengantar ${this.uploadForm.title.trim() || 'Materi'}`,
         content: `<p>${this.uploadForm.blurb.trim()}</p><p class="text-xs text-slate-500 mt-4 italic">Dokumen terlampir: ${this.uploadForm.fileName || 'Tidak ada file fisik'}</p>`
       }];
     }

     if (this.isEditingId) {
       const targetId = this.isEditingId;
       if (this.supabaseClient) {
         this.isSaving = true;
         try {
           let coverUrlToSave = this.uploadForm.coverUrl || '';
           if (this.uploadForm.coverFile) {
             const cleanCoverName = this.uploadForm.coverFile.name.replace(/[^a-zA-Z0-9._-]/g, '_');
             const coverPath = `covers/${Date.now()}_${cleanCoverName}`;
             const uploadedCoverUrl = await this.uploadToStorage(SUPABASE_STORAGE_BUCKET, coverPath, this.uploadForm.coverFile);
             if (uploadedCoverUrl) this.uploadForm.coverUrl = uploadedCoverUrl;
           }

           let authorPhotoToSave = this.uploadForm.authorPhoto ? this.uploadForm.authorPhoto.trim() : null;
           if (this.uploadForm.authorPhotoFile) {
             const cleanPhotoName = this.uploadForm.authorPhotoFile.name.replace(/[^a-zA-Z0-9._-]/g, '_');
             const photoPath = `authors/${Date.now()}_${cleanPhotoName}`;
             const uploadedPhotoUrl = await this.uploadToStorage(SUPABASE_STORAGE_BUCKET, photoPath, this.uploadForm.authorPhotoFile);
             if (uploadedPhotoUrl) this.uploadForm.authorPhoto = uploadedPhotoUrl;
           }

           let fileUrlToSave = this.uploadForm.fileUrl || null;
           if (this.uploadForm.file) {
             const cleanDocName = this.uploadForm.file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
             const docPath = `documents/${Date.now()}_${cleanDocName}`;
             const uploadedDocUrl = await this.uploadToStorage(SUPABASE_STORAGE_BUCKET, docPath, this.uploadForm.file);
             if (uploadedDocUrl) this.uploadForm.fileUrl = uploadedDocUrl;
           }

           const calculatedAccess = Number(this.uploadForm.price) > 0 ? 'Berbayar' : this.uploadForm.accessType;

           const updatePayload = {
             title: this.uploadForm.title.trim(),
             author: this.uploadForm.author.trim(),
             author_bio: this.uploadForm.authorBio?.trim() || null,
             author_photo: this.uploadForm.authorPhoto?.trim() || null,
             author_links: this.uploadForm.authorLinks || null,
             category: this.uploadForm.category,
             access_type: calculatedAccess,
             price: calculatedAccess === 'Berbayar' ? Number(this.uploadForm.price) || 0 : 0,
             is_private: this.uploadForm.isPrivate === 'true',
             cover_url: this.uploadForm.coverUrl || '',
             blurb: this.uploadForm.blurb.trim(),
             external_link: this.uploadForm.external_link?.trim() || null,
             file_url: this.uploadForm.fileUrl || fileUrlToSave,
             file_name: this.uploadForm.fileName || null
           };

           const { data: updatedData, error: updateErr } = await this.supabaseClient
             .from('books')
             .update(updatePayload)
             .eq('id', targetId)
             .select('id');

           if (updateErr) throw updateErr;
           if (!updatedData || updatedData.length === 0) throw new Error('Pembaruan buku ditolak oleh izin database (RLS) atau buku tidak ditemukan.');

           await this.supabaseClient.from('chapters').delete().eq('book_id', targetId);
           const updatedChapterRows = formattedChapters.map((chap, index) => ({
             book_id: targetId,
             title: chap.title,
             content: chap.content,
             chapter_order: index + 1,
             is_preview: index === 0 || this.uploadForm.accessType !== 'Berbayar'
           }));
           await this.supabaseClient.from('chapters').insert(updatedChapterRows);
           
           await this.fetchBooks();
         } catch (err) {
           this.uploadMessage = { text: 'Gagal memperbarui: ' + err.message, type: 'error' };
           this.isSaving = false;
           return;
         } finally {
           this.isSaving = false;
         }
       }

       const bookIdx = this.catalog.findIndex(b => b.id === targetId);
       if (bookIdx !== -1) {
         this.catalog[bookIdx].title = this.uploadForm.title.trim();
         this.catalog[bookIdx].author = this.uploadForm.author.trim();
         this.catalog[bookIdx].chapters = formattedChapters;
         this.catalog[bookIdx].blurb = this.uploadForm.blurb.trim();
         this.catalog[bookIdx].price = Number(this.uploadForm.price) || 0;
         this.catalog[bookIdx].coverUrl = this.uploadForm.coverUrl;
         this.catalog[bookIdx].external_link = this.uploadForm.external_link;
         this.catalog[bookIdx].fileUrl = this.uploadForm.fileUrl;
         this.catalog[bookIdx].fileName = this.uploadForm.fileName;
       }
       this.cancelEditMode();
       this.goToCatalog();
       return;
     }

     this.saveAuthorProfileLocally({
       author: this.uploadForm.author.trim(),
       authorBio: this.uploadForm.authorBio ? this.uploadForm.authorBio.trim() : '',
       authorPhoto: this.uploadForm.authorPhoto ? this.uploadForm.authorPhoto.trim() : '',
       authorLinks: this.uploadForm.authorLinks || {}
     });
     const calculatedAccess = Number(this.uploadForm.price) > 0 ? 'Berbayar' : this.uploadForm.accessType;

     const newBook = {
       id: 'book-' + Date.now(),
       userId: this.currentUser?.id || null,
       title: this.uploadForm.title.trim(),
       author: this.uploadForm.author.trim(),
       authorBio: this.uploadForm.authorBio ? this.uploadForm.authorBio.trim() : null,
       authorPhoto: this.uploadForm.authorPhoto ? this.uploadForm.authorPhoto.trim() : null,
       authorLinks: this.uploadForm.authorLinks || null,
       category: this.uploadForm.category,
       accessType: calculatedAccess,
       price: calculatedAccess === 'Berbayar' ? Number(this.uploadForm.price) || 0 : 0,
       createdAt: new Date().toISOString().split('T')[0],
       blurb: this.uploadForm.blurb.trim(),
       isPrivate: this.uploadForm.isPrivate === 'true',
       coverUrl: this.uploadForm.coverUrl.trim() || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80',
       external_link: this.uploadForm.external_link.trim() || null,
       fileName: this.uploadForm.fileName || null,
       fileUrl: this.uploadForm.fileUrl || null,
       chapters: formattedChapters
     };

     if (this.supabaseClient) {
       this.isSaving = true;
       try {
         if (this.uploadForm.coverFile) {
           const cleanCoverName = this.uploadForm.coverFile.name.replace(/[^a-zA-Z0-9._-]/g, '_');
           const coverPath = `covers/${Date.now()}_${cleanCoverName}`;
           const uploadedCoverUrl = await this.uploadToStorage(SUPABASE_STORAGE_BUCKET, coverPath, this.uploadForm.coverFile);
           if (uploadedCoverUrl) {
             newBook.coverUrl = uploadedCoverUrl;
           }
         }

         if (this.uploadForm.authorPhotoFile) {
           const cleanPhotoName = this.uploadForm.authorPhotoFile.name.replace(/[^a-zA-Z0-9._-]/g, '_');
           const photoPath = `authors/${Date.now()}_${cleanPhotoName}`;
           const uploadedPhotoUrl = await this.uploadToStorage(SUPABASE_STORAGE_BUCKET, photoPath, this.uploadForm.authorPhotoFile);
           if (uploadedPhotoUrl) {
             newBook.authorPhoto = uploadedPhotoUrl;
           }
         }

         if (this.uploadForm.file) {
           const cleanDocName = this.uploadForm.file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
           const docPath = `documents/${Date.now()}_${cleanDocName}`;
           const uploadedDocUrl = await this.uploadToStorage(SUPABASE_STORAGE_BUCKET, docPath, this.uploadForm.file);
           if (uploadedDocUrl) {
             newBook.fileUrl = uploadedDocUrl;
           }
         }

         const bookPayload = {
           title: newBook.title,
           author: newBook.author,
           author_bio: newBook.authorBio,
           author_photo: newBook.authorPhoto,
           author_links: newBook.authorLinks,
           category: newBook.category,
           access_type: newBook.accessType,
           price: newBook.price,
           is_private: newBook.isPrivate,
           cover_url: newBook.coverUrl,
           blurb: newBook.blurb
         };

         if (this.currentUser?.id) bookPayload.user_id = this.currentUser.id;
         if (newBook.external_link) bookPayload.external_link = newBook.external_link;
         if (newBook.fileUrl) bookPayload.file_url = newBook.fileUrl;
         if (newBook.fileName) bookPayload.file_name = newBook.fileName;

         let { data, error } = await this.supabaseClient
           .from('books')
           .insert([bookPayload])
           .select('id')
           .single();

         if (error && (error.message?.includes('author_bio') || error.message?.includes('author_photo') || error.message?.includes('author_links'))) {
           delete bookPayload.author_bio;
           delete bookPayload.author_photo;
           delete bookPayload.author_links;
           const retry = await this.supabaseClient
             .from('books')
             .insert([bookPayload])
             .select('id')
             .single();
           data = retry.data;
           error = retry.error;
         }

         if (error) throw error;
         if (!data) throw new Error('Gagal menambahkan buku baru (RLS Supabase membatasi penambahan data).');
         if (data) {
           newBook.id = String(data.id);

           const chapterRows = newBook.chapters.map((chap, index) => ({
             book_id: data.id,
             title: chap.title,
             content: chap.content,
             chapter_order: index + 1,
             is_preview: index === 0 || newBook.accessType !== 'Berbayar'
           }));

           await this.supabaseClient
             .from('chapters')
             .insert(chapterRows);
         }
       } catch (err) {
         const detailedError = err?.message || err?.details || JSON.stringify(err);
         console.error('Supabase upload/insert error:', detailedError, err);
         this.uploadMessage = { text: 'Gagal menyimpan ke database Supabase: ' + detailedError, type: 'error' };
         this.isSaving = false;
         return;
       } finally {
         this.isSaving = false;
       }
     }

     this.catalog.unshift(newBook);
     this.clearFile();
     this.uploadForm.title = '';
     this.uploadForm.category = 'Teknologi & AI';
     this.uploadForm.isPrivate = 'false';
     this.uploadForm.fileName = '';
     this.uploadForm.authorPhotoFile = null;
     this.loadAuthorProfile();
     this.uploadForm.foreword = '';
     this.uploadForm.introduction = '';
     this.uploadForm.glossary = '';
     this.uploadForm.bibliography = '';
     this.uploadForm.blurb = '';
     this.uploadForm.accessType = 'Gratis';
     this.uploadForm.price = 0;
     this.uploadForm.coverUrl = '';
     this.uploadForm.coverFile = null;
     this.uploadForm.external_link = '';
     this.uploadForm.fileUrl = '';
     this.uploadForm.chapters = [{ title: '', content: '' }];
     this.currentView = 'catalog';
     window.scrollTo({ top: 0, behavior: 'smooth' });
   },

   extractStoragePath(publicUrl, bucketName) {
     if (!publicUrl) return null;
     try {
       let path = publicUrl;
       if (path.includes(`/${bucketName}/`)) {
         const marker = `/${bucketName}/`;
         const index = path.indexOf(marker);
         path = path.substring(index + marker.length);
       }
       path = path.split('?')[0];
       return decodeURIComponent(path);
     } catch (e) {
       return null;
     }
   },

   safeUrl(url) {
     if (!url || typeof url !== 'string') return '';
     const trimmed = url.trim();
     return /^https?:\/\//i.test(trimmed) ? trimmed : '';
   },

   getAuthorInitials(name) {
     if (!name) return 'WB';
     return name
       .split(' ')
       .filter(Boolean)
       .slice(0, 2)
       .map(part => part[0].toUpperCase())
       .join('');
   },

   getSanitizedContent(rawHtml) {
     if (!rawHtml) return '<p class="text-slate-400 italic">Tidak ada isi konten pada bab ini.</p>';
     if (typeof DOMPurify !== 'undefined') {
       return DOMPurify.sanitize(rawHtml, {
         ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'img', 'br', 'hr', 'span', 'div'],
         ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'target', 'rel'],
         ADD_ATTR: ['target'],
         FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form'],
         FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover']
       });
     }
     return rawHtml;
   },

   getEmbedUrl(url) {
     if (!url) return '';
     const lower = url.toLowerCase();
     return (lower.endsWith('.pdf') || lower.includes('.pdf?')) 
       ? url 
       : `<https://docs.google.com/viewer?url=${encodeURIComponent(url)}&embedded=true>`;
   },

   async deleteBook(book) {
     if (!confirm(`Apakah Anda yakin ingin menghapus buku "${book.title}"?`)) {
       return;
     }

     if (this.supabaseClient) {
       try {
         const filesToRemove = [];
         const coverPath = this.extractStoragePath(book.coverUrl, SUPABASE_STORAGE_BUCKET);
         const filePath = this.extractStoragePath(book.fileUrl, SUPABASE_STORAGE_BUCKET);
         
         if (coverPath) filesToRemove.push(coverPath);
         if (filePath) filesToRemove.push(filePath);

         if (filesToRemove.length > 0) {
           await this.supabaseClient.storage
             .from(SUPABASE_STORAGE_BUCKET)
             .remove(filesToRemove);
         }

         const { error } = await this.supabaseClient
           .from('books')
           .delete()
           .eq('id', book.id);
         if (error) throw error;
       } catch (err) {
         this.showToast('Gagal menghapus buku: ' + err.message, 'error');
         return;
       }
     }

     this.catalog = this.catalog.filter(b => b.id !== book.id);
     if (this.activeBook?.id === book.id) {
       this.closeReader();
     }
     this.showToast('Buku berhasil dihapus dari rak.', 'info');
   },

   openEditModal(book) {
     this.editForm = {
       originalBook: book,
       category: book.category || 'Teknologi & AI',
       id: book.id,
       title: book.title,
       author: book.author || '',
       authorBio: book.authorBio || '',
       authorPhoto: book.authorPhoto || '',
       authorLinks: book.authorLinks ? JSON.parse(JSON.stringify(book.authorLinks)) : { instagram: '', x: '', facebook: '', tiktok: '', linkedin: '', whatsapp: '', website: '' },
       authorPhotoFile: null,
       blurb: book.blurb,
       price: book.price || 0,
       external_link: book.external_link || ''
     };
     this.isEditModalOpen = true;
   },

   openAuthorSocialModal(target = 'upload') {
     this.socialModalTarget = target;
     const sourceLinks = target === 'upload' ? this.uploadForm.authorLinks : this.editForm.authorLinks;
     this.socialModalForm = {
       instagram: sourceLinks?.instagram || '',
       x: sourceLinks?.x || '',
       facebook: sourceLinks?.facebook || '',
       tiktok: sourceLinks?.tiktok || '',
       linkedin: sourceLinks?.linkedin || '',
       whatsapp: sourceLinks?.whatsapp || '',
       website: sourceLinks?.website || ''
     };
     this.isAuthorSocialModalOpen = true;
   },

   closeAuthorSocialModal() {
     this.isAuthorSocialModalOpen = false;
   },

   shareBook(book) {
     if (!book) return;
     this.shareBookData = book;
     this.isLinkCopied = false;
     this.isShareModalOpen = true;
   },

   closeShareModal() {
     this.isShareModalOpen = false;
     this.shareBookData = null;
     this.isLinkCopied = false;
   },

   getShareBookLink(book) {
     if (!book) return window.location.href;
     const url = new URL(window.location.href);
     url.searchParams.set('book', book.id);
     return url.toString();
   },

   getShareUrl(platform) {
     if (!this.shareBookData) return '#';
     const book = this.shareBookData;
     const shareUrl = this.getShareBookLink(book);
     const text = `Baca "${book.title}" karya ${book.author} di Pustaka WebBook:\n`;
     
     switch (platform) {
       case 'whatsapp':
         return `<https://wa.me/?text=${encodeURIComponent(text> + shareUrl)}`;
       case 'x':
         return `<https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareUrl)}>`;
       case 'telegram':
         return `<https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(text)}>`;
       case 'facebook':
         return `<https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}>`;
       default:
         return '#';
     }
   },

   async copyShareLink(book) {
     const link = this.getShareBookLink(book);
     try {
       await navigator.clipboard.writeText(link);
     } catch (e) {
       const temp = document.createElement('input');
       temp.value = link;
       document.body.appendChild(temp);
       temp.select();
       document.execCommand('copy');
       document.body.removeChild(temp);
     }
     this.isLinkCopied = true;
     setTimeout(() => { this.isLinkCopied = false; }, 2500);
   },

   async triggerNativeShare(book) {
     if (!book) return;
     const shareUrl = this.getShareBookLink(book);
     try {
       await navigator.share({
         title: book.title,
         text: `Baca "${book.title}" karya ${book.author} di Pustaka WebBook`,
         url: shareUrl
       });
     } catch (e) {
       console.log('Share native dibatalkan/tidak didukung:', e);
     }
   },

   saveAuthorSocialModal() {
     const cloned = JSON.parse(JSON.stringify(this.socialModalForm));
     if (this.socialModalTarget === 'upload') {
       this.uploadForm.authorLinks = cloned;
       if (this.currentUser) {
         this.saveAuthorProfileLocally({
           author: this.uploadForm.author ? this.uploadForm.author.trim() : '',
           authorBio: this.uploadForm.authorBio ? this.uploadForm.authorBio.trim() : '',
           authorPhoto: this.uploadForm.authorPhoto ? this.uploadForm.authorPhoto.trim() : '',
           authorLinks: cloned
         });
       }
     } else {
       this.editForm.authorLinks = cloned;
     }
     this.closeAuthorSocialModal();
   },

   hasAuthorLinks(links) {
     if (!links) return false;
     return Object.values(links).some(val => val && val.trim());
   },

   formatSocialUrl(value, prefix) {
     if (!value) return '#';
     const val = value.trim();
     if (/^javascript:/i.test(val) || /^data:/i.test(val)) return '#';
     return val.startsWith('http://') || val.startsWith('https://') ? val : prefix + val.replace(/^@/, '');
   },

   formatWhatsappUrl(wa) {
     if (!wa) return '#';
     const clean = wa.replace(/\D/g, '').replace(/^0/, '62');
     return `<https://wa.me/${clean}>`;
   },

   async editInFullForm() {
     const b = this.editForm.originalBook;
     if (!b) return;
     this.isEditingId = b.id;
     this.uploadForm = {
       title: b.title || '',
       author: b.author || '',
       authorBio: b.authorBio || '',
       authorPhoto: b.authorPhoto || '',
       authorLinks: b.authorLinks ? JSON.parse(JSON.stringify(b.authorLinks)) : { instagram: '', x: '', facebook: '', tiktok: '', linkedin: '', whatsapp: '', website: '' },
       authorPhotoFile: null,
       foreword: '',
       introduction: '',
       glossary: '',
       bibliography: '',
       category: b.category || 'Teknologi & AI',
       accessType: b.accessType || 'Gratis',
       price: b.price || 0,
       isPrivate: b.isPrivate ? 'true' : 'false',
       coverUrl: b.coverUrl || '',
       coverFile: null,
       external_link: b.external_link || '',
       blurb: b.blurb || '',
       chapters: b.chapters && b.chapters.length ? JSON.parse(JSON.stringify(b.chapters)) : [{ title: '', content: '' }],
       file: null,
       fileName: b.fileName || '',
       fileSize: '',
       fileExtension: '',
       fileUrl: b.fileUrl || ''
     };
     this.closeEditModal();
     this.currentView = 'upload';
     window.scrollTo({ top: 0, behavior: 'smooth' });

     const isNumericId = /^\d+$/.test(String(b.id));
     const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(String(b.id));
     if (this.supabaseClient && (isNumericId || isUuid)) {
       try {
         const { data, error } = await this.supabaseClient
           .from('chapters')
           .select('id, title, content, chapter_order, is_preview')
           .eq('book_id', b.id)
           .order('chapter_order', { ascending: true });

         if (!error && data && data.length > 0) {
           this.uploadForm.chapters = data.map(ch => ({
             title: ch.title || '',
             content: ch.content || ''
           }));
         }
       } catch (err) {
         console.error('Gagal mengambil bab sebelumnya:', err);
       }
     }
   },

   cancelEditMode() {
     this.isEditingId = null;
     this.clearFile();
     this.uploadForm.title = '';
     this.uploadForm.authorPhotoFile = null;
     this.loadAuthorProfile();
     this.uploadForm.foreword = '';
     this.uploadForm.introduction = '';
     this.uploadForm.glossary = '';
     this.uploadForm.bibliography = '';
     this.uploadForm.blurb = '';
     this.uploadForm.coverUrl = '';
     this.uploadForm.coverFile = null;
     this.uploadForm.external_link = '';
     this.uploadForm.fileUrl = '';
     this.uploadForm.chapters = [{ title: '', content: '' }];
   },

   closeEditModal() {
     if (this.isUpdatingBook) return;
     this.isEditModalOpen = false;
     this.editForm.authorPhotoFile = null;
   },

   async updateBook() {
     if (!this.editForm.title.trim() || !this.editForm.author.trim()) return;
     this.isUpdatingBook = true;

     try {
       let uploadedPhotoUrl = this.editForm.authorPhoto;
       if (this.supabaseClient && this.editForm.authorPhotoFile) {
         const cleanPhotoName = this.editForm.authorPhotoFile.name.replace(/[^a-zA-Z0-9._-]/g, '_');
         const photoPath = `authors/${Date.now()}_${cleanPhotoName}`;
         const resUrl = await this.uploadToStorage(SUPABASE_STORAGE_BUCKET, photoPath, this.editForm.authorPhotoFile);
         if (resUrl) {
           uploadedPhotoUrl = resUrl;
         }
       }

       const calculatedAccess = Number(this.editForm.price) > 0 ? 'Berbayar' : 'Gratis';
       const payload = {
         title: this.editForm.title.trim(),
         author: this.editForm.author.trim(),
         author_bio: this.editForm.authorBio ? this.editForm.authorBio.trim() : null,
         author_links: this.editForm.authorLinks || null,
         author_photo: uploadedPhotoUrl ? uploadedPhotoUrl.trim() : null,
         blurb: this.editForm.blurb.trim(),
         access_type: calculatedAccess,
         price: Number(this.editForm.price) || 0,
         external_link: this.editForm.external_link ? this.editForm.external_link.trim() : null
       };

       if (this.supabaseClient) {
         let { error } = await this.supabaseClient
           .from('books')
           .update(payload)
           .eq('id', this.editForm.id)
           .select('id');

         if (error && (error.message?.includes('author_bio') || error.message?.includes('author_photo') || error.message?.includes('author_links'))) {
           delete payload.author_bio;
           delete payload.author_photo;
           delete payload.author_links;
           const retry = await this.supabaseClient
             .from('books')
             .update(payload)
             .eq('id', this.editForm.id)
             .select('id');
           error = retry.error;
         }

         if (error && (error.message?.includes('external_link') || error.details?.includes('external_link'))) {
           delete payload.external_link;
           const retry = await this.supabaseClient
             .from('books')
             .update(payload)
             .eq('id', this.editForm.id)
             .select('id');
           error = retry.error;
         }
         if (error) throw error;
       }

       if (this.currentUser) {
         this.saveAuthorProfileLocally({
           author: payload.author,
           authorBio: payload.author_bio || '',
           authorPhoto: payload.author_photo || '',
           authorLinks: payload.author_links || {}
         });
       }

       const bookIndex = this.catalog.findIndex(b => b.id === this.editForm.id);
       if (bookIndex !== -1) {
         this.catalog[bookIndex].title = payload.title;
         this.catalog[bookIndex].author = payload.author;
         this.catalog[bookIndex].authorBio = payload.author_bio;
         this.catalog[bookIndex].authorPhoto = payload.author_photo;
         this.catalog[bookIndex].authorLinks = payload.author_links;
         this.catalog[bookIndex].blurb = payload.blurb;
         this.catalog[bookIndex].price = payload.price;
         this.catalog[bookIndex].accessType = payload.access_type;
         this.catalog[bookIndex].external_link = payload.external_link;
       }

       if (this.activeBook?.id === this.editForm.id) {
         this.activeBook.title = payload.title;
         this.activeBook.author = payload.author;
         this.activeBook.authorBio = payload.author_bio;
         this.activeBook.authorPhoto = payload.author_photo;
         this.activeBook.authorLinks = payload.author_links;
         this.activeBook.blurb = payload.blurb;
         this.activeBook.accessType = payload.access_type;
         this.activeBook.price = payload.price;
         this.activeBook.external_link = payload.external_link;
       }

       this.closeEditModal();
       this.showToast('Informasi buku berhasil diperbarui.', 'success');
     } catch (err) {
       this.showToast('Gagal memperbarui buku: ' + err.message, 'error');
     } finally {
       this.isUpdatingBook = false;
     }
   },

   resetFilters() {
     this.scopeFilter = 'all';
     this.searchQuery = '';
     this.selectedCategory = 'Semua';
     this.selectedAccess = 'Semua';
     this.selectedAuthor = 'Semua Penulis';
     this.sortBy = 'newest';
   },

   goToCatalog() {
     if (this.isEditingId) this.cancelEditMode();
     this.closeReader();
     this.currentView = 'catalog';
   },

   handleBookClick(book) {
     this.openBook(book);
   },

   startReading(chapterIndex = 0) {
     if (this.activeBook?.accessType === 'Berbayar' && !this.purchasedBookIds.includes(this.activeBook.id) && chapterIndex > 0) {
       this.openPaymentModal(this.activeBook);
       return;
     }
     this.stopTTS();

     // Jika buku memiliki file dokumen (PDF), samakan fungsi membuka ke Embedded Viewer
     if (this.activeBook?.fileUrl) {
       this.readerTab = 'document';
       this.loadSignedUrlForActiveBook();
       window.scrollTo({ top: 0, behavior: 'smooth' });
       return;
     }

     this.currentChapterIndex = chapterIndex;
     this.readerTab = 'text';
     window.scrollTo({ top: 0, behavior: 'smooth' });
   },

   selectChapterFromDrawer(chapterIndex) {
     this.stopTTS();
     this.isTocDrawerOpen = false;
     this.startReading(chapterIndex);
   },

   canDownloadBook(book = this.activeBook) {
     if (!book || !book.fileUrl) return false;
     if (book.accessType === 'Gratis') return true;
     if (this.currentUser && book.userId === this.currentUser.id) return true;
     return this.purchasedBookIds.includes(book.id);
   },

   async getSignedFileUrl(book, expiresIn = 3600) {
     if (!this.supabaseClient || !book?.fileUrl) return book?.fileUrl || '';
     let path = this.extractStoragePath(book.fileUrl, SUPABASE_STORAGE_BUCKET);
     if (!path && !book.fileUrl.startsWith('http')) {
       path = book.fileUrl;
     }
     if (!path) return book.fileUrl;

     const { data, error } = await this.supabaseClient.storage
       .from(SUPABASE_STORAGE_BUCKET)
       .createSignedUrl(path, expiresIn);

     if (error) {
       console.error('Gagal membuat Signed URL:', error.message);
       return book.fileUrl;
     }
     return data?.signedUrl || book.fileUrl;
   },

   async loadSignedUrlForActiveBook() {
     if (!this.activeBook || !this.activeBook.fileUrl) return;
     if (!this.canDownloadBook(this.activeBook)) {
       this.activeBookSignedUrl = '';
       return;
     }
     this.isLoadingDocument = true;
     try {
       this.activeBookSignedUrl = await this.getSignedFileUrl(this.activeBook, 3600);
     } finally {
       this.isLoadingDocument = false;
     }
   },

   async downloadPDF(book = this.activeBook) {
     if (!this.canDownloadBook(book)) {
       this.openPaymentModal(book);
       return;
     }
     this.isDownloadingPdf = true;
     try {
       const downloadUrl = await this.getSignedFileUrl(book, 120);
       const response = await fetch(downloadUrl);
       if (!response.ok) throw new Error('Gagal mengunduh berkas PDF.');
       const existingPdfBytes = await response.arrayBuffer();

       let pdfBytesToDownload = existingPdfBytes;
       if (window.PDFLib) {
         const { PDFDocument, rgb, degrees } = window.PDFLib;
         const pdfDoc = await PDFDocument.load(existingPdfBytes, { ignoreEncryption: true });
         const pages = pdfDoc.getPages();
         const userText = this.currentUser?.email || 'Pembaca Terverifikasi';
         const watermarkText = `Dilisensikan untuk ${userText}`;

         for (const page of pages) {
           const { width, height } = page.getSize();
           page.drawText(watermarkText, {
             x: width / 2 - 140,
             y: height / 2,
             size: 15,
             color: rgb(0.3, 0.3, 0.3),
             opacity: 0.25,
             rotate: degrees(45)
           });
         }
         pdfBytesToDownload = await pdfDoc.save();
       }

       const blob = new Blob([pdfBytesToDownload], { type: 'application/pdf' });
       const blobUrl = URL.createObjectURL(blob);
       const link = document.createElement('a');
       link.href = blobUrl;
       link.download = book.fileName || `${book.title}.pdf`;
       document.body.appendChild(link);
       link.click();
       document.body.removeChild(link);
       setTimeout(() => URL.revokeObjectURL(blobUrl), 1500);
     } catch (err) {
       this.showToast('Gagal mengunduh dokumen PDF: ' + err.message, 'error');
     } finally {
       this.isDownloadingPdf = false;
     }
   },

   async openBook(book) {
     this.stopTTS();
     this.activeBook = { ...book, chapters: book.chapters ? [...book.chapters] : [] };
     this.activeBookSignedUrl = '';
     this.currentChapterIndex = 0;
     this.isEmbedFullscreen = false;
     this.readerTab = book.external_link ? 'external' : 'overview';

     const isNumericId = /^\d+$/.test(String(book.id));
     const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(String(book.id));

     if (this.supabaseClient && (isNumericId || isUuid)) {
       this.isLoadingChapters = true;
       try {
         const isOwner = this.currentUser && book.userId === this.currentUser.id;
         const hasPurchased = this.purchasedBookIds.includes(String(book.id));
         const canAccessFull = book.accessType !== 'Berbayar' || isOwner || hasPurchased;

         const { data, error } = await this.supabaseClient
           .from('chapters')
           .select('id, title, content, chapter_order, is_preview')
           .eq('book_id', book.id)
           .order('chapter_order', { ascending: true });

         if (!error && data && data.length > 0) {
           this.activeBook.chapters = data.map((ch, idx) => {
             const isAllowed = canAccessFull || ch.is_preview || idx === 0;
             return {
               ...ch,
               content: isAllowed ? (ch.content || '') : '<p class="text-amber-600 dark:text-amber-400 font-semibold p-4 border border-amber-300 dark:border-amber-700 rounded-xl bg-amber-50 dark:bg-amber-950/30 text-center">🔒 Bab ini terkunci. Silakan buka akses penuh buku untuk membaca isi materi.</p>'
             };
           });
         }
       } catch (err) {
         console.error('Gagal memuat bab:', err);
       } finally {
         this.isLoadingChapters = false;
       }
     }
     if (this.canDownloadBook(this.activeBook)) {
       this.loadSignedUrlForActiveBook();
     }
     window.scrollTo({ top: 0, behavior: 'smooth' });
   },

   closeReader() {
     this.stopTTS();
     this.isTocDrawerOpen = false;
     this.isEmbedFullscreen = false;
     this.readerTab = 'overview';
     this.activeBook = null;
   },

   openPaymentModal(book) {
     this.checkoutBook = book;
     this.selectedPaymentMethod = 'qris';
     this.isProcessingPayment = false;
     this.isPaymentModalOpen = true;
   },

   closePaymentModal() {
     if (this.isProcessingPayment) return;
     this.isPaymentModalOpen = false;
     this.checkoutBook = null;
   },

   async processPayment() {
     this.isProcessingPayment = true;

     const selectedMethodObj = this.paymentMethods.find(m => m.id === this.selectedPaymentMethod);
     const methodName = selectedMethodObj ? selectedMethodObj.name : 'Transfer Manual';
     const userEmail = this.currentUser?.email || 'Tamu / Belum Login';
     const formattedPrice = this.formatCurrency(this.checkoutBook?.price);
     const invoiceId = 'WB-' + Date.now().toString(36).toUpperCase();

     const waText = `Halo Admin Pustaka WebBook,\n\nSaya ingin mengonfirmasi pesanan buku:\n🧾 *No. Invoice*: ${invoiceId}\n📖 *Judul*: ${this.checkoutBook?.title}\n✍️ *Penulis*: ${this.checkoutBook?.author}\n💰 *Harga*: ${formattedPrice}\n💳 *Metode*: ${methodName}\n👤 *Akun*: ${userEmail}\n\nMohon petunjuk rekening/QRIS pembayaran dan aktivasi akses buku saya. Terima kasih!`;
     const waUrl = `<https://wa.me/${this.adminWaNumber}?text=${encodeURIComponent(waText)}>`;
     
     if (this.supabaseClient && this.currentUser && this.checkoutBook) {
       try {
         await this.supabaseClient.from('purchases').upsert([{
           user_id: this.currentUser.id,
           book_id: this.checkoutBook.id
         }], { onConflict: 'user_id,book_id' });
       } catch (err) {
         console.error('Gagal mencatat transaksi di Supabase:', err);
       }
     }

     setTimeout(() => {
       if (this.checkoutBook) {
         if (!this.purchasedBookIds.includes(this.checkoutBook.id)) {
           this.purchasedBookIds.push(this.checkoutBook.id);
           localStorage.setItem('purchasedBookIds', JSON.stringify(this.purchasedBookIds));
         }
         const bookToOpen = this.checkoutBook;
         this.isProcessingPayment = false;
         this.isPaymentModalOpen = false;

         window.open(waUrl, '_blank');
         this.openBook(bookToOpen);
       }
     }, 1200);
   },

   formatCurrency(amount) {
     if (!amount || isNaN(amount)) return 'Rp 0';
     return 'Rp ' + Number(amount).toLocaleString('id-ID');
   },

   increaseFontSize() {
     if (this.readerFontSize < 24) {
       this.readerFontSize += 2;
       localStorage.setItem('readerFontSize', this.readerFontSize);
     }
   },

   decreaseFontSize() {
     if (this.readerFontSize > 12) {
       this.readerFontSize -= 2;
       localStorage.setItem('readerFontSize', this.readerFontSize);
     }
   },

   getReadingTime(content) {
     if (!content) return '1 mnt baca';
     const text = content.replace(/<[^>]*>/g, '').trim();
     const words = text ? text.split(/\s+/).length : 0;
     const minutes = Math.max(1, Math.ceil(words / 180));
     return `~${minutes} mnt baca`;
   },

   nextChapter() {
     if (this.activeBook && this.currentChapterIndex < this.activeBook.chapters.length - 1) {
       if (this.activeBook.accessType === 'Berbayar' && !this.purchasedBookIds.includes(this.activeBook.id)) {
         this.openPaymentModal(this.activeBook);
         return;
       }
       this.stopTTS();
       this.currentChapterIndex++;
       window.scrollTo({ top: 0, behavior: 'smooth' });
     }
   },

   prevChapter() {
     if (this.currentChapterIndex > 0) {
       this.stopTTS();
       this.currentChapterIndex--;
       window.scrollTo({ top: 0, behavior: 'smooth' });
     }
   },

   toggleTTS() {
     if (this.isSpeaking) {
       this.stopTTS();
     } else {
       this.startTTS();
     }
   },

   startTTS() {
     if (!('speechSynthesis' in window) || !window.speechSynthesis) {
       this.showToast('Browser Anda belum mendukung fitur Text-to-Speech.', 'error');
       return;
     }

     this.stopTTS();

     const currentChapter = this.activeBook?.chapters?.[this.currentChapterIndex];
     const rawHtml = currentChapter ? this.getSanitizedContent(currentChapter.content) : '';
     const tempDiv = document.createElement('div');
     tempDiv.innerHTML = rawHtml;
     const textToRead = (tempDiv.innerText || tempDiv.textContent || '').trim();

     const utterance = new SpeechSynthesisUtterance(textToRead);
     utterance.lang = 'id-ID';
     utterance.rate = 0.95;

     if (!textToRead) {
       this.showToast('Tidak ada materi teks pada bab ini untuk dibacakan.', 'info');
       return;
     }

     utterance.onend = () => { this.isSpeaking = false; };
     utterance.onerror = (e) => {
       console.warn('Speech synthesis error:', e);
       this.isSpeaking = false;
     };

     this.synth = window.speechSynthesis;
     this.synth.speak(utterance);
     this.isSpeaking = true;
   },

   stopTTS() {
     if (window.speechSynthesis) {
       window.speechSynthesis.cancel();
     }
     this.isSpeaking = false;
   }
 };
}
