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
            response = self.client.post('/unggah-soal', data=data, follow_redirects=True)
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

    def test_api_requires_login_and_teacher_for_mutations(self):
        with self.client.session_transaction() as state:
            state.clear()
        for path in ['/api/missions', '/api/profile', '/api/history', '/api/achievements']:
            self.assertEqual(self.client.get(path).status_code, 401)
        for role in [None, 'mahasiswa']:
            if role:
                self.login(role)
            for method, path, payload in [('post', '/api/missions', {'judul': 'Illegal'}),
                    ('put', '/api/missions/demo_001', {'judul': 'Illegal'}),
                    ('delete', '/api/missions/demo_001', None),
                    ('post', '/api/penilaian-pdf', {'nilai': 100})]:
                response = getattr(self.client, method)(path, json=payload)
                self.assertIn(response.status_code, [401, 403])
        self.assertEqual(self.storage.baca_data()._cari_misu_objek('demo_001').judul, 'Kumpulkan Tugas PBO')

    def test_profile_is_personal_persistent_and_preview_readonly(self):
        self.login()
        self.assertEqual(self.client.get('/api/profile').json['user']['name'], 'Test')
        response = self.client.post('/api/profile', json={'name': 'Ayu', 'avatar': 'avatar3'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Ayu', self.client.get('/dashboard').get_data(as_text=True))
        self.login(nim='002')
        user = self.client.get('/api/profile').json['user']
        self.assertEqual((user['name'], user['avatar']), ('Test', 'avatar1'))
        self.login(preview=True)
        self.assertEqual(self.client.post('/api/profile', json={'name': 'Changed'}).status_code, 403)
        self.login()
        user = self.client.get('/api/profile').json['user']
        self.assertEqual((user['name'], user['avatar']), ('Ayu', 'avatar3'))
        self.assertEqual(self.storage.baca_data().user.name, 'Mahasiswa')

    def test_shared_legacy_progress_does_not_leak_into_student(self):
        manager = self.storage.baca_data()
        manager.selesaikan_misu('demo_001')
        self.storage.tulis_data(manager)
        self.login(nim='new')
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 0)
        self.assertEqual(self.client.get('/api/history').json['history'], [])
        self.assertEqual(self.client.post('/api/missions/demo_001/start').status_code, 200)
        self.assertEqual(self.storage.baca_data().user.total_xp, 40)

    def test_filters_intersect_and_invalid_filter_returns_400(self):
        self.login()
        self.client.post('/api/missions/demo_001/start')
        data = self.client.get('/api/missions?jenis=ujian&status=sedang%20dikerjakan&cari=Tugas').json
        self.assertEqual(data['misi'], [])
        data = self.client.get('/api/missions?jenis=individu&status=sedang%20dikerjakan&cari=Tugas').json
        self.assertEqual(len(data['misi']), 1)
        self.assertEqual(self.client.get('/api/missions?jenis=invalid').status_code, 400)

    def test_edit_type_changes_reward_and_deadline_field_works(self):
        response = self.client.put('/api/missions/demo_001', json={'jenis': 'ujian', 'tenggat': '2027-01-03'})
        self.assertEqual(response.status_code, 200)
        mission = self.storage.baca_data()._cari_misu_objek('demo_001')
        self.assertEqual(mission.hitung_xp(), 60)
        self.assertEqual(mission.tenggat.isoformat(), '2027-01-03')
        self.assertEqual(self.client.put('/api/missions/demo_001', json={'tenggat': None}).status_code, 200)
        self.assertIsNone(self.storage.baca_data()._cari_misu_objek('demo_001').tenggat)
        self.assertEqual(self.client.put('/api/missions/demo_001', json={'status': 'selesai'}).status_code, 400)

    def test_started_mission_cannot_be_deleted_or_rewritten(self):
        self.login()
        self.client.post('/api/missions/demo_001/start')
        self.login('dosen')
        self.assertEqual(self.client.delete('/api/missions/demo_001').status_code, 409)
        self.assertEqual(self.client.put('/api/missions/demo_001', json={'judul': 'Changed'}).status_code, 409)

    def test_malformed_json_and_cross_origin_mutations_are_rejected(self):
        for payload in [['bad'], 'bad', {'judul': 42}, {'tenggat': []}]:
            self.assertEqual(self.client.post('/api/missions', json=payload).status_code, 400)
        self.login()
        for payload in [['bad'], {'id_soal': 'x', 'jawaban': None}]:
            self.assertEqual(self.client.post('/kirim-jawaban', json=payload).status_code, 400)
        response = self.client.post('/api/missions/demo_001/start', headers={'Origin': 'https://elsewhere.test'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.answers, [])

    def test_refresh_after_creation_does_not_duplicate_and_fake_pdf_rejected(self):
        data = dict(judul='New', mata_kuliah='PBO', tipe='tanpa_soal')
        response = self.client.post('/unggah-soal', data=data)
        self.assertEqual(response.status_code, 303)
        self.client.get(response.location)
        self.client.get(response.location)
        self.assertEqual(len(self.contents), 1)
        data.update(tipe='pdf', file_pdf=(io.BytesIO(b'not a pdf'), 'fake.pdf'))
        self.assertEqual(self.client.post('/unggah-soal', data=data).status_code, 400)
        self.assertEqual(len(self.contents), 1)

    def test_teacher_progress_includes_legacy_and_completion_beats_stale_start(self):
        self.login()
        self.client.post('/api/missions/demo_001/complete')
        self.answers.append(dict(nim='001', id_misi='demo_001', status='sedang dikerjakan'))
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 40)
        self.assertEqual(self.client.get('/api/history').json['total'], 1)
        self.login('dosen')
        html = self.client.get('/lihat-progres').get_data(as_text=True)
        self.assertIn('Kumpulkan Tugas PBO', html)
        self.assertIn('0 mulai · 1 mengirim', html)
        with patch.object(module, 'muat_kredensial', return_value={'mahasiswa': [{'nim': '001'}, {'nim': '002'}]}):
            mission = next(m for m in self.client.get('/api/missions').json['misi'] if m['id'] == 'demo_001')
            self.assertEqual(mission['status'], 'sedang dikerjakan')
            self.login(nim='002')
            self.client.post('/api/missions/demo_001/complete')
            self.login('dosen')
            mission = next(m for m in self.client.get('/api/missions').json['misi'] if m['id'] == 'demo_001')
            self.assertEqual(mission['status'], 'selesai')

    def test_parallel_submissions_keep_both_students_and_prevent_double_xp(self):
        from concurrent.futures import ThreadPoolExecutor
        sid = self.create()
        def submit(nim):
            client = module.app.test_client()
            with client.session_transaction() as state:
                state.update(role='mahasiswa', nim=nim, user_name='Test')
            return client.post('/kirim-jawaban', json={'id_soal': sid, 'jawaban': 'A'}).status_code
        with ThreadPoolExecutor(max_workers=4) as executor:
            statuses = list(executor.map(submit, ['001', '002', '001', '002']))
        self.assertEqual(sorted(statuses), [200, 200, 400, 400])
        self.assertEqual(len(self.answers), 2)
        self.login()
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 40)

    def test_empty_storage_bootstraps_and_corrupt_data_is_not_overwritten(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            storage = PenyimpananJSON(directory)
            self.assertEqual(storage.baca_data().user.total_xp, 0)
            path = Path(storage.get_data_path())
            path.write_text('{broken')
            with patch.object(module, 'penyimpanan', storage):
                response = self.client.get('/api/missions')
                self.assertEqual(response.status_code, 503)
            self.assertEqual(path.read_text(), '{broken')

    def test_model_badges_unlock_on_exact_completion_and_bad_edit_is_atomic(self):
        manager = PengelolaMisi()
        for i in range(3):
            mid = manager.tambah_misu('Exam', 'PBO', '', 'ujian', 'mudah', '')['misi_id']
            result = manager.selesaikan_misu(mid)
        self.assertIn('Pejuang Ujian', result['badges_earned'])
        manager.selesaikan_misu('demo_001')
        result = manager.selesaikan_misu('demo_002')
        self.assertIn('Pemburu Misi', result['badges_earned'])
        before = manager._cari_misu_objek('demo_003').judul
        with self.assertRaises(ValueError):
            manager.edit_misu('demo_003', judul='Changed', jenis='invalid')
        self.assertEqual(manager._cari_misu_objek('demo_003').judul, before)

    def test_failed_write_returns_error_not_success(self):
        self.login()
        with patch.object(module, 'tulis_jawaban_mahasiswa', side_effect=OSError('test failure')):
            response = self.client.post('/api/missions/demo_001/complete')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.answers, [])
        self.assertEqual(self.client.get('/api/profile').json['user']['total_xp'], 0)



if __name__ == '__main__':
    unittest.main()
