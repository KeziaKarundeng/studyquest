"""Model OOP: Class Misi Abstrak (Misi)"""
import uuid
from abc import ABC, abstractmethod
from datetime import datetime


class Misi(ABC):
    """Class Misi abstrak yang merupakan dasar untuk semua jenis misi."""
    
    def __init__(self, id: str = None, judul: str = "", mata_kuliah: str = "",
                 deskripsi: str = "", jenis: str = "individu", 
                 tingkat_kesulitan: str = "mudah", tenggat: str = None, status: str = "belum mulai"):
        self._id = id or f"misi_{uuid.uuid4().hex[:8]}"
        self._judul = judul
        self._mata_kuliah = mata_kuliah
        self._deskripsi = deskripsi
        self._jenis = jenis
        self._tingkat_kesulitan = tingkat_kesulitan
        self._tenggat = tenggat
        self._status = status
        self._dibuat_pada = datetime.now().isoformat()
        self._diselesaikan_pada = None
        self._xp_diberikan = False
    
    # Property untuk id
    @property
    def id(self) -> str:
        return self._id
    
    # Property untuk judul
    @property
    def judul(self) -> str:
        return self._judul
    
    @judul.setter
    def judul(self, value: str):
        if not value or not value.strip():
            raise ValueError("Judul misi wajib diisi")
        self._judul = value.strip()
    
    # Property untuk mata_kuliah
    @property
    def mata_kuliah(self) -> str:
        return self._mata_kuliah
    
    @mata_kuliah.setter
    def mata_kuliah(self, value: str):
        if not value or not value.strip():
            raise ValueError("Mata kuliah wajib diisi")
        self._mata_kuliah = value.strip()
    
    # Property untuk deskripsi
    @property
    def deskripsi(self) -> str:
        return self._deskripsi
    
    @deskripsi.setter
    def deskripsi(self, value: str):
        self._deskripsi = value
    
    # Property untuk jenis
    @property
    def jenis(self) -> str:
        return self._jenis
    
    @jenis.setter
    def jenis(self, value: str):
        valid_jenis = ["individu", "kelompok", "ujian"]
        if value not in valid_jenis:
            raise ValueError("Jenis misi harus salah satu dari: " + str(valid_jenis))
        self._jenis = value
    
    # Property untuk tingkat_kesulitan
    @property
    def tingkat_kesulitan(self) -> str:
        return self._tingkat_kesulitan
    
    @tingkat_kesulitan.setter
    def tingkat_kesulitan(self, value: str):
        valid = ["mudah", "sedang", "sulit"]
        if value not in valid:
            raise ValueError("Tingkat kesulitan harus salah satu dari: " + str(valid))
        self._tingkat_kesulitan = value
    
    # Property untuk tenggat - menggunakan built-in property()
    def _get_tenggat(self):
        return self._tenggat
    
    def _set_tenggat(self, value):
        if value is None:
            self._tenggat = None
        else:
            try:
                self._tenggat = datetime.strptime(str(value), "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Tenggat harus berupa tanggal valid format YYYY-MM-DD")
    
    tenggat = property(_get_tenggat, _set_tenggat, 
                       doc="Tenggat misi (tanggal YYYY-MM-DD)")
    
    # Property untuk status
    @property
    def status(self) -> str:
        return self._status
    
    @status.setter
    def status(self, value: str):
        valid = ["belum mulai", "sedang dikerjakan", "selesai"]
        if value not in valid:
            raise ValueError("Status harus salah satu dari: " + str(valid))
        self._status = value
    
    # Property untuk dibuat_pada
    @property
    def dibuat_pada(self) -> str:
        return self._dibuat_pada
    
    # Property untuk diselesaikan_pada
    @property
    def diselesaikan_pada(self):
        return self._diselesaikan_pada
    
    @diselesaikan_pada.setter
    def diselesaikan_pada(self, value):
        self._diselesaikan_pada = datetime.now().isoformat() if value else None
    
    # Property untuk xp_diberikan
    @property
    def xp_diberikan(self) -> bool:
        return self._xp_diberikan
    
    @xp_diberikan.setter
    def xp_diberikan(self, value: bool):
        self._xp_diberikan = value
    
    # Abstract method
    
    @abstractmethod
    def hitung_xp(self) -> int:
        """Mengembalikan jumlah XP berdasarkan tingkat kesulitan dan jenis misi."""
        pass
    
    # Validasi status selesai
    
    @property
    def sudah_selesai(self) -> bool:
        return self._status == "selesai"
    
    def validasi_xp_diberikan(self) -> bool:
        """Cek apakah XP sudah diberikan untuk misi ini."""
        return self._xp_diberikan
    
    def tandai_xp_diberikan(self):
        """Tandai bahwa XP sudah diberikan."""
        self._xp_diberikan = True
    
    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "judul": self._judul,
            "mata_kuliah": self._mata_kuliah,
            "deskripsi": self._deskripsi,
            "jenis": self._jenis,
            "tingkat_kesulitan": self._tingkat_kesulitan,
            "tenggat": self._tenggat.isoformat() if self._tenggat else None,
            "status": self._status,
            "dibuat_pada": self._dibuat_pada,
            "diselesaikan_pada": self._diselesaikan_pada,
            "xp_diberikan": self._xp_diberikan,
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        jenis = data.get("jenis", "individu")
        
        # Determine the correct subclass based on jenis
        if jenis == "individu":
            from models.individu import MisiIndividu as _MisiClass
        elif jenis == "kelompok":
            from models.kelompok import MisiKelompok as _MisiClass
        elif jenis == "ujian":
            from models.ujian import MisiUjian as _MisiClass
        else:
            _MisiClass = cls
        
        m = _MisiClass(
            id=data.get("id"),
            judul=data.get("judul", ""),
            mata_kuliah=data.get("mata_kuliah", ""),
            deskripsi=data.get("deskripsi", ""),
            jenis=jenis,
            tingkat_kesulitan=data.get("tingkat_kesulitan", "mudah"),
            tenggat=data.get("tenggat"),
            status=data.get("status", "belum mulai"),
        )
        m._dibuat_pada = data.get("dibuat_pada", m._dibuat_pada)
        m._diselesaikan_pada = data.get("diselesaikan_pada")
        m._xp_diberikan = data.get("xp_diberikan", False)
        return m