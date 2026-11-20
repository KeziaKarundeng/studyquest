"""Model OOP: Class MisiIndividu mewarisi Misi"""
import uuid
from models.mission import Misi


class MisiIndividu(Misi):
    """Class MisiIndividu merepresentasikan misi individu (tugas individu)."""

    def hitung_xp(self) -> int:
        """Mengembalikan XP dasar berdasarkan tingkat kesulitan."""
        xp_dasar = {"mudah": 20, "sedang": 40, "sulit": 60}
        return xp_dasar.get(self._tingkat_kesulitan, 20)