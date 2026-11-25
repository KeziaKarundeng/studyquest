"""Model OOP: Class PengelolaMisi mengelola kumpulan objek misi"""
import uuid
from datetime import datetime, date
from models.user import User
from models.mission import Misi
from models.individu import MisiIndividu
from models.kelompok import MisiKelompok
from models.ujian import MisiUjian


def uuid_val():
    """Helper fungsi UUID untuk kompatibilitas."""
    return str(uuid.uuid4())[:8]


class PengelolaMisi:
    """Class PengelolaMisi mengelola kumpulan objek misi menggunakan list Python."""
    
    def __init__(self, user: User = None):
        self._user = user or User(name="Mahasiswa")
        self._misi_list = []
        self._load_default_data()
    
    def _load_default_data(self):
        """Muat data demo jika belum ada data user."""
        default_misi = [
            {
                "id": "demo_001",
                "judul": "Kumpulkan Tugas PBO",
                "mata_kuliah": "Pemrograman Berorientasi Objek",
                "deskripsi": "Mengerjakan praktikum mengenai class dan object",
                "jenis": "individu",
                "tingkat_kesulitan": "sedang",
                "tenggat": None,
                "status": "belum mulai",
                "demo": True,
            },
            {
                "id": "demo_002",
                "judul": "Presentasi Akhir PKN",
                "mata_kuliah": "Pancasila dan Kewarganegaraan",
                "deskripsi": "Persiapkan presentasi kelompok tentang nilai-nilai Pancasila",
                "jenis": "kelompok",
                "tingkat_kesulitan": "mudah",
                "tenggat": None,
                "status": "belum mulai",
                "demo": True,
            },
            {
                "id": "demo_003",
                "judul": "Persiapan Ujian Akhir Semester",
                "mata_kuliah": "Matematika Dasar",
                "deskripsi": "Review materi dan mengerjakan soal pengulangan",
                "jenis": "ujian",
                "tingkat_kesulitan": "sulit",
                "tenggat": None,
                "status": "belum mulai",
                "demo": True,
            },
        ]
        
        for data_misi in default_misi:
            jenis = data_misi.get("jenis", "individu")
            if jenis == "individu":
                m = MisiIndividu(
                    id=data_misi.get("id"),
                    judul=data_misi.get("judul", ""),
                    mata_kuliah=data_misi.get("mata_kuliah", ""),
                    deskripsi=data_misi.get("deskripsi", ""),
                    jenis=jenis,
                    tingkat_kesulitan=data_misi.get("tingkat_kesulitan", "sedang"),
                    tenggat=data_misi.get("tenggat"),
                    status=data_misi.get("status", "belum mulai"),
                )
            elif jenis == "kelompok":
                m = MisiKelompok(
                    id=data_misi.get("id"),
                    judul=data_misi.get("judul", ""),
                    mata_kuliah=data_misi.get("mata_kuliah", ""),
                    deskripsi=data_misi.get("deskripsi", ""),
                    jenis=jenis,
                    tingkat_kesulitan=data_misi.get("tingkat_kesulitan", "mudah"),
                    tenggat=data_misi.get("tenggat"),
                    status=data_misi.get("status", "belum mulai"),
                )
            elif jenis == "ujian":
                m = MisiUjian(
                    id=data_misi.get("id"),
                    judul=data_misi.get("judul", ""),
                    mata_kuliah=data_misi.get("mata_kuliah", ""),
                    deskripsi=data_misi.get("deskripsi", ""),
                    jenis=jenis,
                    tingkat_kesulitan=data_misi.get("tingkat_kesulitan", "sulit"),
                    tenggat=data_misi.get("tenggat"),
                    status=data_misi.get("status", "belum mulai"),
                )
            else:
                m = Misi(
                    id=data_misi.get("id"),
                    judul=data_misi.get("judul", ""),
                    mata_kuliah=data_misi.get("mata_kuliah", ""),
                    deskripsi=data_misi.get("deskripsi", ""),
                    jenis=jenis,
                    tingkat_kesulitan=data_misi.get("tingkat_kesulitan", "mudah"),
                    tenggat=data_misi.get("tenggat"),
                    status=data_misi.get("status", "belum mulai"),
                )
            self._misi_list.append(m)
    
    # CRUD Methods
    
    def tambah_misu(self, judul: str, mata_kuliah: str, deskripsi: str,
                    jenis: str, tingkat_kesulitan: str, tenggat: str) -> dict:
        """Menambah misi baru dengan validasi."""
        # Validasi judul dan mata kuliah wajib diisi
        if not judul or not judul.strip():
            raise ValueError("Judul misi wajib diisi")
        if not mata_kuliah or not mata_kuliah.strip():
            raise ValueError("Mata kuliah wajib diisi")
        
        # Validasi jenis, tingkat kesulitan
        valid_jenis = ["individu", "kelompok", "ujian"]
        if jenis not in valid_jenis:
            raise ValueError("Jenis misi harus salah satu dari: " + str(valid_jenis))
        
        valid_kesulitan = ["mudah", "sedang", "sulit"]
        if tingkat_kesulitan not in valid_kesulitan:
            raise ValueError("Tingkat kesulitan harus salah satu dari: " + str(valid_kesulitan))
        
        # Validasi tenggat tanggal
        tenggat_date = None
        if tenggat:
            try:
                tenggat_date = datetime.strptime(tenggat, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Tenggat harus berupa tanggal valid format YYYY-MM-DD")
        
        # Buah objek misi sesuai jenis
        if jenis == "individu":
            misi = MisiIndividu(
                id="misu_" + uuid_val(),
                judul=judul.strip(),
                mata_kuliah=mata_kuliah.strip(),
                deskripsi=deskripsi.strip(),
                jenis=jenis,
                tingkat_kesulitan=tingkat_kesulitan,
                tenggat=tenggat_date,
                status="belum mulai",
            )
        elif jenis == "kelompok":
            misi = MisiKelompok(
                id="misku_" + uuid_val(),
                judul=judul.strip(),
                mata_kuliah=mata_kuliah.strip(),
                deskripsi=deskripsi.strip(),
                jenis=jenis,
                tingkat_kesulitan=tingkat_kesulitan,
                tenggat=tenggat_date,
                status="belum mulai",
            )
        elif jenis == "ujian":
            misi = MisiUjian(
                id="misuo_" + uuid_val(),
                judul=judul.strip(),
                mata_kuliah=mata_kuliah.strip(),
                deskripsi=deskripsi.strip(),
                jenis=jenis,
                tingkat_kesulitan=tingkat_kesulitan,
                tenggat=tenggat_date,
                status="belum mulai",
            )
        
        self._misi_list.append(misi)
        return {"status": "sukses", "misi_id": misi.id, "judul": misi.judul}
    
    def edit_misu(self, misi_id: str, judul: str = None, mata_kuliah: str = None,
                  deskripsi: str = None, jenis: str = None, tingkat_kesulitan: str = None,
                  tenggat: str = None, status: str = None) -> dict:
        """Mengedit misi. Misi selesai tidak boleh diedit."""
        misi = self._cari_misu_objek(misi_id)
        if not misi:
            raise ValueError("Misi tidak ditemukan")
        
        # Cek apakah misi sudah selesai (dikelintasi)
        if misi.status == "selesai":
            raise ValueError("Tidak bisa mengedit misi yang sudah selesai - misi dikunci")
        
        # Reconstruct the subclass when type changes, so XP updates immediately.
        candidate = Misi.from_dict(misi.to_dict())
        updates = dict(judul=judul, mata_kuliah=mata_kuliah, deskripsi=deskripsi,
                       jenis=jenis, tingkat_kesulitan=tingkat_kesulitan, tenggat=tenggat)
        for key, value in updates.items():
            if value is not None:
                setattr(candidate, key, value)  # Validate without changing the original.
        if status is not None and status != misi.status:
            raise ValueError("Status pengerjaan diubah oleh mahasiswa, bukan dari edit misi.")
        replacement = Misi.from_dict(candidate.to_dict())
        self._misi_list = [replacement if item.id == misi_id else item for item in self._misi_list]

        return {"status": "sukses", "misi_id": misi.id}
    
    def hapus_misu(self, misi_id: str) -> dict:
        """Menghapus misi. Misi selesai tidak bisa dihapus."""
        misi = self._cari_misu_objek(misi_id)
        if not misi:
            raise ValueError("Misi tidak ditemukan")
        
        # Cek apakah misi sudah selesai
        if misi.status == "selesai":
            raise ValueError("Tidak bisa menghapus misi yang sudah selesai - misi dikunci")
        
        self._misi_list = [m for m in self._misi_list if m.id != misi_id]
        return {"status": "sukses", "misi_id": misi_id}
    
    def cari_misu(self, kata_kunci: str) -> list:
        """Cari misi berdasarkan judul (case-insensitive)."""
        hasil = []
        kunci = kata_kunci.lower().strip()
        for m in self._misi_list:
            if kunci in m.judul.lower():
                hasil.append(m)
        return hasil
    
    def filter_jenis(self, jenis: str) -> list:
        """Filter misi berdasarkan jenis."""
        valid_jenis = ["individu", "kelompok", "ujian", "semua"]
        if jenis not in valid_jenis:
            raise ValueError("Jenis filter harus salah satu dari: " + str(valid_jenis))
        if jenis == "semua":
            return self._misi_list
        return [m for m in self._misi_list if m.jenis == jenis]
    
    def filter_status(self, status: str) -> list:
        """Filter misi berdasarkan status."""
        valid_status = ["belum mulai", "sedang dikerjakan", "selesai", "semua"]
        if status not in valid_status:
            raise ValueError("Status filter harus salah satu dari: " + str(valid_status))
        if status == "semua":
            return self._misi_list
        return [m for m in self._misi_list if m.status == status]
    
    # Statistik dan Analisis
    
    def get_statistik(self) -> dict:
        """Mengembalikan statistik misi: aktif, selesai, lewat tenggat."""
        aktif = len([m for m in self._misi_list if m.status != "selesai"])
        selesai = len(self.filter_status("selesai"))
        
        # Cek lewat tenggat (tenggat sudah lewat dari hari ini)
        lewat_tenggat = 0
        hari_ini = date.today()
        for m in self._misi_list:
            if m.tenggat and m.tenggat < hari_ini and m.status != "selesai":
                lewat_tenggat += 1
        
        return {
            "aktif": aktif,
            "selesai": selesai,
            "lewat_tenggat": lewat_tenggat,
            "total": len(self._misi_list),
        }
    
    def get_tenggat_dekat(self, hari: int = 7) -> list:
        """Mengembalikan misi lewat tenggat dalam n hari ke depan (default 7 hari)."""
        dari_hingga = date.today()
        sampai_hingga = date.fromordinal(date.today().toordinal() + hari)
        
        results = []
        for m in self._misi_list:
            if m.tenggat and dari_hingga <= m.tenggat <= sampai_hingga and m.status != "selesai":
                results.append(m)
        return sorted(results, key=lambda x: x.tenggat if x.tenggat else date.max)
    
    def get_misu_terdekat_tenggat(self) -> list:
        """Daftar misi dengan tenggat terdekat (untuk tampilan dashboard)."""
        aktif_tetap = [m for m in self._misi_list if m.status != "selesai"]
        return sorted(aktif_tetap, key=lambda x: x.tenggat if x.tenggat else date.max)[:5]
    
    # Metode utama: selesaikan misi
    
    def selesaikan_misu(self, misi_id: str) -> dict:
        """Selesaikan misi: dapatkan XP, cek level up, badge, dan kunci misi."""
        misi = self._cari_misu_objek(misi_id)
        if not misi:
            raise ValueError("Misi tidak ditemukan")
        
        # Cek apakah misi sudah selesai (pencegahan ganda)
        if misi.status == "selesai":
            # Masih kembalikan info tapi tandai bahwa XP tidak diberikan
            return {
                "status": "sudah_selesai",
                "pesan": "Misi ini sudah selesai dan tidak bisa diberikan XP lagi",
                "xp_diberikan": 0,
                "level_baru": self._user.level,
                "total_xp": self._user.total_xp,
                "badge_terbaru": [],
            }
        
        # Dapatkan XP dari method polymorphic hitung_xp()
        xp_dapat = misi.hitung_xp()
        
        # Tandai misi selesai
        misi.status = "selesai"
        misi.diselesaikan_pada = True
        misi.xp_diberikan = True
        
        # Tandai di user
        self._user.mark_mission_complete(misi.id)
        xp_info = self._user.add_xp(xp_dapat)
        if sum(m.status == "selesai" and m.jenis == "ujian" for m in self._misi_list) >= 3 and "Pejuang Ujian" not in self._user.badges:
            self._user._badges.add("Pejuang Ujian")
            xp_info["badges_earned"].append("Pejuang Ujian")

        return {
            "status": "sukses",
            "pesan": "Misi '" + misi.judul + "' selesai! Mendapat " + str(xp_dapat) + " XP",
            "xp_diberikan": xp_dapat,
            "level_baru": xp_info["leveled_up_to"] if xp_info["leveled_up"] else self._user.level,
            "total_xp": self._user.total_xp,
            "leveled_up": xp_info["leveled_up"],
            "leveled_up_to": xp_info["leveled_up_to"] if xp_info["leveled_up"] else None,
            "badges_earned": xp_info["badges_earned"],
        }
    
    # Search & Helper
    
    def _cari_misu_objek(self, misi_id: str):
        """Cari objek misi berdasarkan ID."""
        for m in self._misi_list:
            if m.id == misi_id:
                return m
        return None
    
    # Getter untuk user
    
    @property
    def user(self) -> User:
        return self._user
    
    @user.setter
    def user(self, value: User):
        self._user = value
    
    def to_dict(self) -> dict:
        return {
            "user": self._user.to_dict(),
            "misi_list": [m.to_dict() for m in self._misi_list],
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        pengguna_data = data.get("user", {})
        user = User.from_dict(pengguna_data) if pengguna_data else User(name="Mahasiswa")
        
        pengelola = object.__new__(cls)
        pengelola._user = user
        pengelola._misi_list = []
        
        for m_data in data.get("misi_list", []):
            m = Misi.from_dict(m_data)
            pengelola._misi_list.append(m)
        
        return pengelola