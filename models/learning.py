"""Project existing assignments and uploaded content into one mission list.

Completion records remain per student in jawaban_mahasiswa.json. Reading this
view never changes the legacy files or shared mission definitions.
"""
from models.mission import Misi
from models.user import User


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


def learning_view(manager, contents, answers, nim, student_ids=None):
    manager._misi_list.extend(mission_from_content(s) for s in contents)
    # The legacy global profile cannot identify who earned its XP/completions.
    # Keep that source file intact, but derive personal progress only from records
    # carrying a NIM. Otherwise every new student inherits another user's work.
    manager.user = User()
    for mission in manager._misi_list:
        mission.status = 'belum mulai'
        mission._diselesaikan_pada = None
        mission.xp_diberikan = False
    submissions = {}
    started = set()
    for answer in answers:
        owner = answer.get('nim')
        if not owner or (nim and owner != nim):
            continue
        mid = ('soal_' + answer['id_soal']) if answer.get('id_soal') else answer.get('id_misi')
        if not manager._cari_misu_objek(mid):
            continue
        key = (owner, mid)
        if answer.get('status') == 'sedang dikerjakan':
            started.add(key)
        elif answer.get('jawaban'):
            submissions.setdefault(key, answer)
    for mission in manager._misi_list:
        completed = {owner for owner, mid in submissions if mid == mission.id}
        active = {owner for owner, mid in started if mid == mission.id} - completed
        mission.total_jawab = len(completed)
        mission.total_mulai = len(active)
        if not nim:
            # Teacher status is a class summary, not the last student's status.
            if student_ids and set(student_ids) <= completed:
                mission.status = 'selesai'
            elif completed or active:
                mission.status = 'sedang dikerjakan'
            continue
        answer = submissions.get((nim, mission.id))
        if answer:
            mission.status = 'selesai'
            mission._diselesaikan_pada = answer.get('waktu_dikerjakan')
            mission.xp_diberikan = True
            mission.awarded_xp = answer.get('xp_diberikan', mission.hitung_xp())
            manager.user.mark_mission_complete(mission.id)
            manager.user.add_xp(mission.awarded_xp)
        elif (nim, mission.id) in started:
            mission.status = 'sedang dikerjakan'
    completed = [m for m in manager._misi_list if m.status == 'selesai'] if nim else []
    if completed:
        manager.user._badges.add('Langkah Pertama')
    if len(completed) >= 5:
        manager.user._badges.add('Pemburu Misi')
    if sum(m.jenis == 'ujian' for m in completed) >= 3:
        manager.user._badges.add('Pejuang Ujian')
    return manager
