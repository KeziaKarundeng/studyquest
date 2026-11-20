// StudyQuest JavaScript - Fungsi Interaktif untuk Aplikasi Web

// Cek preferensi reduced motion (hormi pengaturan pengguna)
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Fungsi bantuan untuk animasi (matikan jika reduced motion)
function animateElement(element, animationName, duration = 0.5) {
    if (prefersReducedMotion) {
        element.style.opacity = 1;
        element.style.transform = '';
        return;
    }
    
    element.style.animation = `${animationName} ${duration}s ease`;
    setTimeout(() => {
        element.style.animation = '';
    }, duration * 1000);
}

// Tampilkan modal XP Gain
function showXPModal(amount, reason) {
    const modal = document.getElementById('xp-modal');
    const xpAmount = document.getElementById('xp-amount');
    const xpReason = document.getElementById('xp-reason');
    
    xpAmount.textContent = `+${amount} XP`;
    xpReason.textContent = reason || 'Misi berhasil';
    
    modal.classList.add('active');
    
    // Otomatis tutup setelah 2 detik
    setTimeout(closeXPModal, 2000);
}

// Tutup modal XP
function closeXPModal() {
    const modal = document.getElementById('xp-modal');
    modal.classList.remove('active');
}

// Tampilkan modal Level Up
function showLevelUpModal(oldLevel, newLevel, xpGained) {
    const modal = document.getElementById('levelup-modal');
    const oldLevelEl = document.getElementById('old-level');
    const newLevelEl = document.getElementById('new-level');
    const levelupXp = document.getElementById('levelup-xp');
    
    oldLevelEl.textContent = oldLevel;
    newLevelEl.textContent = newLevel;
    levelupXp.textContent = `+${xpGained} XP`;
    
    modal.classList.add('active');
}

// Tutup modal Level Up
function closeLevelUpModal() {
    const modal = document.getElementById('levelup-modal');
    modal.classList.remove('active');
}

// Tampilkan modal Badge Unlock
function showBadgeModal(badgeName, badgeDesc, iconClass) {
    const modal = document.getElementById('badge-modal');
    const badgeIcon = document.getElementById('badge-icon');
    const badgeNameEl = document.getElementById('badge-name');
    const badgeDescEl = document.getElementById('badge-desc');
    
    badgeIcon.innerHTML = `<span class="fas ${iconClass}" style="color: var(--secondary);"></span>`;
    badgeNameEl.textContent = badgeName;
    badgeDescEl.textContent = badgeDesc;
    
    modal.classList.add('active');
}

// Tutup modal Badge
function closeBadgeModal() {
    const modal = document.getElementById('badge-modal');
    modal.classList.remove('active');
}

// Update dashboard setelah perubahan
function updateDashboard() {
    // Refresh data dari server
    fetch('/dashboard')
        .then(response => response.json())
        .then(data => {
            // Update UI elements
            if (data.user) {
                const user = data.user;
                
                // Update level dan progress
                const levelEl = document.getElementById('user-level');
                const xpEl = document.getElementById('user-xp');
                const progressFill = document.querySelector('.progress-fill');
                const progressText = document.querySelector('.progress-text');
                
                if (levelEl) levelEl.textContent = `Lvl ${user.level}`;
                if (xpEl) xpEl.textContent = user.total_xp || 0;
                if (progressFill) progressFill.style.width = (user.progress || 0) + '%';
                if (progressText) progressText.textContent = `${user.progress || 0}% ke level berikutnya`;
            }
            
            // Update stats
            if (data.stats) {
                const stats = data.stats;
                document.getElementById('stat-aktif').textContent = stats.aktif;
                document.getElementById('stat-selesai').textContent = stats.selesai;
                document.getElementById('stat-lewat').textContent = stats.lewat_tengggat;
            }
            
            // Update misi terdekat
            if (data.misi_terdekat) {
                const listEl = document.getElementById('misi-terdekat-list');
                listEl.innerHTML = '';
                data.misi_terdekat.forEach(m => {
                    const div = document.createElement('div');
                    div.className = `mission-item ${m.status !== 'selesai' ? '' : ''}`;
                    div.setAttribute('data-id', m.id);
                    div.innerHTML = `
                        <div class="mission-info">
                            <h4 class="mission-title">${m.judul}</h4>
                            <p class="mission-mata-kuliah">${m.mata_kuliah}</p>
                            <p class="mission-tengggat">Tenggat: ${m.tengggat || 'Tidak ada'}</p>
                        </div>
                        <div class="mission-status ${m.status}">${m.status}</div>
                        ${m.status !== 'selesai' ? `<button class="btn-complete" onclick="completeMission('${m.id}')">Selesaikan</button>` : ''}
                    `;
                    listEl.appendChild(div);
                });
            }
            
            // Update badge grid
            if (data.badges !== undefined) {
                const badgesGrid = document.getElementById('badges-grid');
                // ... update badge items
            }
        });
}

// Update profil UI
function updateProfileUI(name, avatar) {
    const previewAvatar = document.getElementById('preview-avatar');
    const previewName = document.getElementById('preview-name');
    
    if (previewAvatar) {
        previewAvatar.className = 'preview-avatar ' + avatar;
    }
    if (previewName) {
        previewName.textContent = name || 'Mahasiswa';
    }
}

// Event listeners untuk modals
document.addEventListener('DOMContentLoaded', function() {
    // Close modals on background click
    ['xp-modal', 'levelup-modal', 'badge-modal'].forEach(id => {
        const modal = document.getElementById(id);
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // Keyboard shortcut: Esc to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            ['xp-modal', 'levelup-modal', 'badge-modal'].forEach(id => {
                const modal = document.getElementById(id);
                modal.classList.remove('active');
            });
        }
    });
});

// Load page content via AJAX - hanya ambil isi main-content dari response
function loadPageContent(page) {
    const contentMap = {
        'dashboard': '/dashboard',
        'missions': '/missions',
        'achievements': '/achievements',
        'history': '/history',
        'profile': '/profile'
    };
    
    const target = contentMap[page];
    if (!target) return;
    
    fetch(target)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const fetchedContent = doc.querySelector('.main-content');
            const mainContent = document.querySelector('.main-content');
            if (fetchedContent && mainContent) {
                mainContent.innerHTML = fetchedContent.innerHTML;
                document.dispatchEvent(new Event('page-loaded'));
            }
        })
        .catch(error => {
            console.error(`Gagal memuat halaman ${page}:`, error);
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {
                mainContent.innerHTML = `<p>Gagal memuat halaman ${page}</p>`;
            }
        });
}

// Handle sidebar navigation
document.querySelectorAll('.sidebar nav ul li a').forEach(link => {
    if (link.getAttribute('href') !== '#') return; // Lewati link non-AJAX (mis. Ganti Role)
    link.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.sidebar nav ul li a').forEach(l => l.classList.remove('active'));
        this.classList.add('active');
        const linkId = this.getAttribute('id');
        const pageMap = {
            'nav-dashboard': 'dashboard',
            'nav-missions': 'missions',
            'nav-achievements': 'achievements',
            'nav-history': 'history',
            'nav-profile': 'profile'
        };
        const page = pageMap[linkId];
        if (page) loadPageContent(page);
    });
});

// Disable animations if user prefers reduced motion
if (prefersReducedMotion) {
    console.log('Animasi dinonaktifkan sesuai pengaturan pengguna');
    const style = document.createElement('style');
    style.textContent = '* { animation: none !important; transition: none !important; }';
    document.head.appendChild(style);
}