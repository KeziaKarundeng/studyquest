"""Model OOP: Class Pengguna (User)"""
import uuid
from datetime import datetime


class User:
    """Class Pengguna merepresentasikan data pengguna aplikasi StudyQuest."""
    
    def __init__(self, name: str = "Mahasiswa", avatar: str = "avatar1"):
        self._id = str(uuid.uuid4())[:8]
        self._name = name
        self._avatar = avatar
        self._level = 1
        self._total_xp = 0
        self._badges = set()
        self._created_at = datetime.now().isoformat()
        self._completed_missions = []
    
    # Properties (Encapsulation)
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str):
        if not value or not value.strip():
            raise ValueError("Nama tidak boleh kosong")
        self._name = value.strip()
    
    @property
    def avatar(self) -> str:
        return self._avatar
    
    @avatar.setter
    def avatar(self, value: str):
        valid_avatars = ["avatar1", "avatar2", "avatar3", "avatar4"]
        if value not in valid_avatars:
            raise ValueError("Avatar harus salah satu dari: " + str(valid_avatars))
        self._avatar = value
    
    @property
    def level(self) -> int:
        """Rumus level: 1 + total XP dibagi 100 dengan pembagian bulat."""
        return 1 + self._total_xp // 100
    
    @property
    def total_xp(self) -> int:
        return self._total_xp
    
    @total_xp.setter
    def total_xp(self, value: int):
        """XP tidak boleh diubah langsung dari frontend."""
        raise PermissionError("total_xp tidak boleh diubah langsung, gunakan method tambah_xp()")
    
    @property
    def progress(self) -> int:
        """Progress menuju level berikutnya (sisa pembagian total XP dengan 100)."""
        return self._total_xp % 100
    
    @property
    def badges(self) -> list:
        return sorted(list(self._badges))
    
    @property
    def created_at(self) -> str:
        return self._created_at
    
    @property
    def completed_missions(self) -> list:
        return self._completed_missions
    
    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "name": self._name,
            "avatar": self._avatar,
            "level": self.level,
            "total_xp": self._total_xp,
            "badges": list(self._badges),
            "created_at": self._created_at,
            "completed_missions": self._completed_missions,
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        user = cls(name=data.get("name", "Mahasiswa"), avatar=data.get("avatar", "avatar1"))
        user._id = data.get("id", user._id)
        user._total_xp = data.get("total_xp", 0)
        user._badges = set(data.get("badges", []))
        user._completed_missions = data.get("completed_missions", [])
        user._created_at = data.get("created_at", user._created_at)
        return user
    
    def add_xp(self, amount: int) -> dict:
        """Menambah XP dan mengembalikan info level-up dan badge."""
        leveled_up = False
        leveled_up_to = self._level
        badges_earned = []
        
        self._total_xp += amount
        
        # Cek level up
        new_level = self.level
        if new_level > leveled_up_to:
            leveled_up = True
            leveled_up_to = new_level
        
        # Cek badge
        if len(self._badges) == 0:
            badges_earned.append("Langkah Pertama")
        
        if leveled_up_to >= 5 and "Naik Kelas" not in self._badges:
            badges_earned.append("Naik Kelas")
        
        # Cek Pemburu Misi (5 misi selesai)
        completed_count = len([m for m in self._completed_missions if m.get("status") == "selesai"])
        if completed_count >= 5 and "Pemburu Misi" not in self._badges:
            badges_earned.append("Pemburu Misi")
        
        # Cek Pejuang Ujian (3 misi ujian selesai)
        ujian_count = len([m for m in self._completed_missions if m.get("jenis") == "ujian" and m.get("status") == "selesai"])
        if ujian_count >= 3 and "Pejuang Ujian" not in self._badges:
            badges_earned.append("Pejuang Ujian")
        
        self._badges.update(badges_earned)
        
        return {
            "total_xp": self._total_xp,
            "level": self.level,
            "leveled_up": leveled_up,
            "leveled_up_to": leveled_up_to,
            "badges_earned": badges_earned,
        }
    
    def mark_mission_complete(self, mission_id: str):
        """Tanda tangani misi sebagai selesai."""
        if mission_id not in self._completed_missions:
            self._completed_missions.append(mission_id)
    
    def has_mission(self, mission_id: str) -> bool:
        return mission_id in self._completed_missions