"""Project existing assignments and uploaded content into one mission list.

Completion records remain per student in jawaban_mahasiswa.json. Reading this
view never changes the legacy files or shared mission definitions.
"""
from models.mission import Misi


def mission_from_content(content):
    mission = Misi.from_dict({
        'id': 'soal_' + content['id'],
        'judul': content.get('judul') or content.get('pertanyaan') or content.get('nama_asli') or 'Misi dari dosen',
        'mata_kuliah': content.get('mata_kuliah', ''),
        'deskripsi': content.get('deskripsi', ''),
        'jenis': content.get('jenis', 'individu'),
        'tingkat_kesulitan': content.get('tingkat_kesulitan', 'mudah'),
        'tenggat': content.get('tenggat'),
        'status': 'belum mulai',
    })
    mission.soal_id = content['id']
    mission.tipe = content.get('tipe', 'pilihan_ganda')
    return mission


def learning_view(manager, contents, answers, nim):
    manager._misi_list.extend(mission_from_content(s) for s in contents)
    seen = set()
    for answer in answers:
        if not nim or answer.get('nim') != nim:
            continue
        mid = ('soal_' + answer['id_soal']) if answer.get('id_soal') else answer.get('id_misi')
        mission = manager._cari_misu_objek(mid)
        if not mission or mid in seen:
            continue
        if answer.get('status') == 'sedang dikerjakan':
            mission.status = 'sedang dikerjakan'
            continue
        seen.add(mid)
        mission.status = 'selesai'
        mission._diselesaikan_pada = answer.get('waktu_dikerjakan')
        manager.user.mark_mission_complete(mid)
        manager.user.add_xp(answer.get('xp_diberikan', mission.hitung_xp()))
    completed = [m for m in manager._misi_list if m.status == 'selesai']
    if completed:
        manager.user._badges.add('Langkah Pertama')
    if len(completed) >= 5:
        manager.user._badges.add('Pemburu Misi')
    if sum(m.jenis == 'ujian' for m in completed) >= 3:
        manager.user._badges.add('Pejuang Ujian')
    return manager
