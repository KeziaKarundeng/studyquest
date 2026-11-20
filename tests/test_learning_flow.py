"""Integration checks use disposable storage; no project data is changed."""
import copy
import io
import tempfile
import unittest
from unittest.mock import patch
import app as module
from models.management import PengelolaMisi
from models.storage import PenyimpananJSON


class LearningFlowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.storage = PenyimpananJSON(self.temp.name)
        self.storage.tulis_data(PengelolaMisi())
        self.contents, self.answers = [], []
        self.patches = [
            patch.object(module, 'penyimpanan', self.storage),
            patch.object(module, 'muat_soal_universal', side_effect=lambda: copy.deepcopy(self.contents)),
            patch.object(module, 'tulis_soal_universal', side_effect=lambda data: self.contents.__setitem__(slice(None), copy.deepcopy(data))),
            patch.object(module, 'muat_jawaban_mahasiswa', side_effect=lambda: copy.deepcopy(self.answers)),
            patch.object(module, 'tulis_jawaban_mahasiswa', side_effect=lambda data: self.answers.__setitem__(slice(None), copy.deepcopy(data))),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.temp.cleanup)
        module.app.config['TESTING'] = True
        self.client = module.app.test_client()
        self.login('dosen')

    def login(self, role='mahasiswa', nim='001', preview=False):
        with self.client.session_transaction() as session:
            session.clear()
            session.update(role=role, user_name='Test', nim=nim, preview_as_dosen=preview)

    def create(self, kind='pilihan_ganda'):
        data = dict(judul='Misi OOP', mata_kuliah='PBO', jenis='individu',
                    tingkat_kesulitan='sedang', tenggat='2026-12-01', tipe=kind,
                    pertanyaan='Apa itu class?', pilihan_a='Cetak biru', pilihan_b='Nilai',
                    pilihan_c='Loop', pilihan_d='Kondisi', jawaban_benar='A')
        if kind == 'pdf':
            data['file_pdf'] = (io.BytesIO(b'%PDF-1.4\n%%EOF'), 'test.pdf')
        with patch('werkzeug.datastructures.FileStorage.save'), patch('app.os.makedirs'):
            response = self.client.post('/unggah-soal', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('berhasil dibuat', response.get_data(as_text=True))
        return self.contents[-1]['id']

    def test_answer_completes_mission_and_awards_personal_xp_once(self):
        sid = self.create()
        self.login()
        response = self.client.post('/kirim-jawaban', json={'id_soal': sid, 'jawaban': 'B'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['benar_salah'], 'salah')
        self.assertEqual(response.json['xp_diberikan'], 40)
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 40)
        self.assertIn('Misi OOP', self.client.get('/history').get_data(as_text=True))
        self.assertIn('Langkah Pertama', self.client.get('/achievements').get_data(as_text=True))
        self.assertEqual(self.client.post('/kirim-jawaban', json={'id_soal': sid, 'jawaban': 'A'}).status_code, 400)
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 40)
        self.login(nim='002')
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 0)
        self.assertIn('Misi OOP', self.client.get('/dashboard').get_data(as_text=True))
        self.assertEqual(self.contents[0]['status'], 'belum_dikerjakan')
        self.assertEqual(self.storage.baca_data().user.total_xp, 0)

    def test_pdf_and_plain_task_use_same_completion_flow(self):
        for kind in ['pdf', 'tanpa_soal']:
            self.login('dosen')
            sid = self.create(kind)
            self.login()
            response = self.client.post('/kirim-jawaban', json={'id_soal': sid, 'jawaban': 'Hasil pengerjaan saya'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['xp_diberikan'], 40)
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 80)

    def test_bypass_and_preview_are_rejected(self):
        sid = self.create()
        self.assertEqual(self.client.post('/kirim-jawaban', json={'id_soal': sid, 'jawaban': 'A'}).status_code, 403)
        self.login(preview=True)
        self.assertEqual(self.client.post('/kirim-jawaban', json={'id_soal': sid, 'jawaban': 'A'}).status_code, 403)
        self.assertEqual(self.client.post('/api/missions/demo_001/complete').status_code, 403)
        self.login()
        self.assertEqual(self.client.post('/api/missions/soal_' + sid + '/complete').status_code, 400)
        self.assertEqual(self.client.post('/kirim-jawaban', json={'id_soal': sid, 'jawaban': 'E'}).status_code, 400)
        self.assertEqual(self.answers, [])

    def test_legacy_task_completion_is_personal_and_old_answers_still_work(self):
        self.login()
        self.assertEqual(self.client.post('/api/missions/demo_001/complete').json['data']['xp_diberikan'], 40)
        self.assertEqual(self.client.post('/api/missions/demo_001/complete').json['data']['xp_diberikan'], 0)
        self.login(nim='002')
        self.assertEqual(self.client.post('/api/missions/demo_001/complete').json['data']['xp_diberikan'], 40)
        self.assertEqual(self.storage.baca_data()._cari_misu_objek('demo_001').status, 'belum mulai')
        self.contents.append(dict(id='legacy', tipe='pilihan_ganda', pertanyaan='Old', mata_kuliah='Old', pilihan=['1','2','3','4'], jawaban_benar='A'))
        self.answers.append(dict(id_soal='legacy', nim='002', jawaban='A', waktu_dikerjakan='2024-01-01T00:00:00'))
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 60)
        self.assertEqual(self.client.get('/soal-mahasiswa').status_code, 200)

    def test_start_is_personal_idempotent_and_does_not_award_xp(self):
        sid = self.create()
        self.login()
        mid = 'soal_' + sid
        for _ in range(2):
            self.assertEqual(self.client.post('/api/missions/' + mid + '/start').status_code, 200)
        self.assertEqual(len(self.answers), 1)
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 0)
        self.assertIn('Sedang dikerjakan', self.client.get('/dashboard').get_data(as_text=True))
        self.assertEqual(self.client.get('/soal-mahasiswa').status_code, 200)
        self.login(nim='002')
        self.assertNotIn('Sedang dikerjakan', self.client.get('/dashboard').get_data(as_text=True))
        self.login()
        response = self.client.post('/kirim-jawaban', json={'id_soal': sid, 'jawaban': 'A'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.answers), 1)
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 40)
        self.assertEqual(self.client.post('/api/missions/' + mid + '/start').status_code, 200)
        self.assertEqual(len(self.answers), 1)
        self.assertNotIn('Sedang dikerjakan', self.client.get('/dashboard').get_data(as_text=True))

    def test_pdf_grading_and_revision_are_visible_only_to_the_student(self):
        sid = self.create('pdf')
        self.login()
        self.client.post('/api/missions/soal_' + sid + '/start')
        self.assertEqual(self.client.get('/history').status_code, 200)
        self.client.post('/kirim-jawaban', json={'id_soal': sid, 'jawaban': 'Jawaban lengkap PDF'})
        self.assertIn('Menunggu penilaian', self.client.get('/soal-mahasiswa').get_data(as_text=True))
        self.login('dosen')
        for grade in [0, 87.5]:
            response = self.client.post('/api/penilaian-pdf', json={'id_soal': sid, 'nim': '001', 'nilai': grade, 'catatan': 'Perbaiki contoh pewarisan.'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.answers[0]['nilai'], grade)
        self.assertIn('Simpan penilaian', self.client.get('/lihat-progres').get_data(as_text=True))
        self.login()
        html = self.client.get('/soal-mahasiswa').get_data(as_text=True)
        self.assertIn('87.5', html)
        self.assertIn('Perbaiki contoh pewarisan.', html)
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 40)
        self.assertEqual(self.client.post('/api/penilaian-pdf', json={'id_soal': sid, 'nim': '001', 'nilai': 100}).status_code, 403)
        self.login(nim='002')
        self.assertNotIn('Perbaiki contoh pewarisan.', self.client.get('/soal-mahasiswa').get_data(as_text=True))

    def test_invalid_grades_and_unsubmitted_pdf_cannot_be_graded(self):
        sid = self.create('pdf')
        for value in [-1, 101, 'nan', 'Infinity', '', 'abc', '4.123']:
            self.assertEqual(self.client.post('/api/penilaian-pdf', json={'id_soal': sid, 'nim': '001', 'nilai': value}).status_code, 400)
        self.assertEqual(self.client.post('/api/penilaian-pdf', json={'id_soal': sid, 'nim': '001', 'nilai': 90}).status_code, 404)
        self.login()
        self.client.post('/api/missions/soal_' + sid + '/start')
        self.login('dosen')
        self.assertEqual(self.client.get('/lihat-progres').status_code, 200)
        self.assertEqual(self.client.post('/api/penilaian-pdf', json={'id_soal': sid, 'nim': '001', 'nilai': 90}).status_code, 404)
        self.login(preview=True)
        self.assertEqual(self.client.post('/api/missions/soal_' + sid + '/start').status_code, 403)



if __name__ == '__main__':
    unittest.main()
