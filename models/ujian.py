"""Model OOP: Class MisiUjian mewarisi Misi"""
import uuid
from models.mission import Misi


class MisiUjian(Misi):
    """Class MisiUjian merepresentasikan misi persiapan ujian."""

    def hitung_xp(self) -> int:
        """Mengembalikan XP dasar + 20 berdasarkan tingkat kesulitan."""
        xp_dasar = {"mudah": 20, "sedang": 40, "sulit": 60}
        dasar = xp_dasar.get(self._tingkat_kesulitan, 20)
        return dasar + 20