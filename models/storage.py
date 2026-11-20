"""Model OOP: Class PenyimpananJSON untuk baca/tulis file JSON"""
import json
import os
import tempfile
from models.management import PengelolaMisi


class PenyimpananJSON:
    """Class PenyimpananJSON menangani baca dan tulis data ke file JSON."""
    
    FILE_NAME = "user_data.json"
    DEFAULT_DATA_FILE = "default_data.json"
    
    def __init__(self, data_dir: str = None):
        if data_dir:
            self._data_dir = data_dir
        else:
            # Direktur relatif terhadap folder aplikasi
            self._data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
        self._file_path = os.path.join(self._data_dir, self.FILE_NAME)
        self._default_path = os.path.join(self._data_dir, self.DEFAULT_DATA_FILE)
    
    def baca_data(self) -> PengelolaMisi:
        """Membaca data dari file JSON. Jika file belum ada, buat data awal."""
        if not os.path.exists(self._file_path):
            # Buat data awal valid
            data_demo = self._baca_default_demo()
            self.tulis_data(data_demo)
            return data_demo
        
        # Coba baca file
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PengelolaMisi.from_dict(data)
        except (json.JSONDecodeError, IOError) as e:
            # File rusak - tampilkan pesan dan gunakan data default
            print(f"PERINGATAN: File data rusak ({e}), menggunakan data default")
            data_demo = self._baca_default_demo()
            self.tulis_data(data_demo)
            return data_demo
    
    def _baca_default_demo(self) -> PengelolaMisi:
        """Baca data demo dari file default."""
        default_file = self._default_path
        if os.path.exists(default_file):
            try:
                with open(default_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return PengelolaMisi.from_dict(data)
            except Exception:
                pass
        
        # Buat data demo minimal jika file tidak ada
        dari_default = PengelolaMisi.__new__(PengelolaMisi)
        dari_default._user = User(name="Mahasiswa")
        dari_default._misi_list = []
        return dari_default
    
    def tulis_data(self, pengelola: PengelolaMisi) -> bool:
        """Menulis data ke file JSON dengan metode atomic write (sementara lalu geser)."""
        try:
            # Pastikan direktori ada
            os.makedirs(self._data_dir, exist_ok=True)
            
            # Konversi objek menjadi dict
            data = pengelola.to_dict()
            
        except Exception as e:
            print(f"Gagal mengonversi data: {e}")
            return False
        
        # Atomic write: tulis ke file sementara dulu
        tmp_path = self._file_path + ".tmp"
        
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Verifikasi file sementara bisa dibaca
            with open(tmp_path, "r", encoding="utf-8") as f:
                # Coba parse
                json.load(f)
            
            # Geser file sementara menjadi file utama
            os.replace(tmp_path, self._file_path)
            
            return True
            
        except IOError as e:
            # Jika gagal, bersihkan file tmp dan jangan overwrite
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            print(f"Gagal menulis data: {e}")
            return False
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            print(f"Error tak terduga saat menyimpan: {e}")
            return False
    
    def file_rusak(self) -> bool:
        """Cek apakah file data rusak (bukan valid JSON)."""
        if not os.path.exists(self._file_path):
            return False
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                json.load(f)
            return False
        except (json.JSONDecodeError, ValueError):
            return True
    
    def get_data_path(self) -> str:
        """Mengembalikan path ke file data pengguna."""
        return self._file_path
    
    def get_default_path(self) -> str:
        """Mengembalikan path ke file data demo."""
        return self._default_path