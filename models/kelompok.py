"""Model OOP: Class MisiKelompok mewarisi Misi"""
import uuid
from models.mission import Misi


class MisiKelompok(Misi):
    """Class MisiKelompok merepresentasikan misi kelompok."""

    def hitung_xp(self) -> int:
        """Mengembalikan XP dasar + 10 berdasarkan tingkat kesulitan."""
        xp_dasar = {"mudah": 20, "sedang": 40, "sulit": 60}
        dasar = xp_dasar.get(self._tingkat_kesulitan, 20)
        return dasar + 10