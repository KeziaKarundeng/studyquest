"""Flask Application: StudyQuest - Kuliah Jadi Game"""
import os
from datetime import date
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from models.user import User
from models.management import PengelolaMisi
from models.storage import PenyimpananJSON

app = Flask(__name__)
app.secret_key = "studyquest_secret_key_2024"

# Inisialisasi penyimpanan
penyimpanan = PenyimpananJSON()


# --- Helper: Cek Role ---

def role_wajib():
    """Return True jika role sudah login di session."""
    return session.get("role") in ("dosen", "mahasiswa")


def muat_kredensial():
    """Muat data kredensial dosen & mahasiswa dari JSON."""
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "credentials.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"dosen": [], "mahasiswa": []}


def muat_soal():
    """Muat data soal dari JSON."""
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "soal.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def muat_soal_universal():
    """Muat data soal universal yang diunggah dosen."""
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "soal_universal.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def tulis_soal_universal(data):
    """Tulis data soal universal ke JSON."""
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "soal_universal.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def muat_jawaban_mahasiswa():
    """Muat data jawaban mahasiswa."""
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "jawaban_mahasiswa.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def tulis_jawaban_mahasiswa(data):
    """Tulis data jawaban mahasiswa ke JSON."""
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "jawaban_mahasiswa.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- Route Login ---

@app.route("/login", methods=["GET", "POST"])
def login():
    """Halaman login: pilih tab Dosen/Mahasiswa lalu isi kredensial."""
    if role_wajib():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        return _proses_login()

    error = request.args.get("error", "")
    active_tab = request.args.get("role", "dosen")
    return render_template("login.html", error=error, active_tab=active_tab)


@app.route("/do-login", methods=["POST"])
def do_login():
    """Verifikasi kredensial dan set session."""
    if role_wajib():
        return redirect(url_for("dashboard"))
    return _proses_login()


def _proses_login():
    """Proses verifikasi kredensial dari form login."""
    role = request.form.get("role", "")
    creds = muat_kredensial()

    if role == "dosen":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        for d in creds.get("dosen", []):
            if d.get("username", "").lower() == username and d.get("password") == password:
                session.clear()
                session["role"] = "dosen"
                session["user_name"] = d.get("name", username.capitalize())
                return redirect(url_for("dashboard"))
        return render_template("login.html", error="Username atau password dosen salah.", active_tab="dosen")

    elif role == "mahasiswa":
        nama = request.form.get("nama", "").strip().lower()
        nim = request.form.get("nim", "").strip()
        for m in creds.get("mahasiswa", []):
            if m.get("nama", "").lower() == nama and m.get("nim") == nim:
                session.clear()
                session["role"] = "mahasiswa"
                session["user_name"] = m.get("name", nama.title())
                session["nim"] = nim
                return redirect(url_for("dashboard"))
        return render_template("login.html", error="Nama atau NIM mahasiswa tidak terdaftar.", active_tab="mahasiswa")

    return redirect(url_for("login"))


@app.route("/ganti-role")
def ganti_role():
    """Dosen bisa pindah ke mode mahasiswa (cek soal), mahasiswa asli tidak bisa pindah ke dosen."""
    if not role_wajib():
        return redirect(url_for("login"))

    if session.get("role") == "dosen":
        # Dosen -> mode mahasiswa (preview untuk cek soal)
        creds = muat_kredensial()
        m = creds.get("mahasiswa", [{}])[0] if creds.get("mahasiswa") else {}
        session["dosen_name"] = session.get("user_name", "Dosen")
        session["role"] = "mahasiswa"
        session["preview_as_dosen"] = True
        session["user_name"] = m.get("name", "Mahasiswa")
        session["nim"] = m.get("nim", "")
        return redirect(url_for("dashboard"))

    if session.get("preview_as_dosen"):
        # Mode preview mahasiswa (dari dosen) -> kembali ke dosen
        session["role"] = "dosen"
        session["user_name"] = session.get("dosen_name", "Dosen")
        session.pop("preview_as_dosen", None)
        session.pop("nim", None)
        session.pop("dosen_name", None)
        return redirect(url_for("dashboard"))

    # Mahasiswa asli -> tidak boleh ganti ke dosen
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    """Hapus session dan kembali ke login."""
    session.clear()
    return redirect(url_for("login"))


# --- Route Utama ---

@app.route("/")
def index():
    """Redirect ke login jika belum login, selainnya ke dashboard."""
    if not role_wajib():
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


# --- Dashboard ---

@app.route("/dashboard")
def dashboard():
    """Halaman dashboard utama."""
    if not role_wajib():
        return redirect(url_for("login"))
    pengelola = penyimpanan.baca_data()
    user = pengelola.user
    stats = pengelola.get_statistik()
    misi_terdekat = pengelola.get_misu_terdekat_tenggat()
    
    stats_summary = {
        'aktif': stats['aktif'],
        'selesai': stats['selesai'],
        'lewat_tenggat': stats['lewat_tenggat'],
        'total': stats['total'],
        'level': user.level
    }
    return render_template("dashboard.html",
        today=date.today(),
        user_name=session.get("user_name", user.name),
        user_avatar=user.avatar,
        total_xp=user.total_xp,
        level=user.level,
        progress=user.progress,
        stats=stats_summary,
        misi_terdekat=misi_terdekat,
        user_badges=user.badges,
        role=session.get("role"),
        preview_as_dosen=session.get("preview_as_dosen", False),
        soal_universal=muat_soal_universal(),
    )


# --- API Routes untuk Misi ---

@app.route("/api/missions", methods=["GET"])
def list_missions():
    """Daftar misi dengan filter opsional."""
    pengelola = penyimpanan.baca_data()
    
    # Filter params
    jenis_filter = request.args.get("jenis", "semua")
    status_filter = request.args.get("status", "semua")
    cari = request.args.get("cari", "")
    
    misi_list = pengelola._misi_list
    
    # Filter jenis
    if jenis_filter != "semua":
        misi_list = pengelola.filter_jenis(jenis_filter)
    
    # Filter status
    if status_filter != "semua":
        misi_list = pengelola.filter_status(status_filter)
    
    # Cari
    if cari:
        misi_list = pengelola.cari_misu(cari)
    
    # Konversi ke dict
    results = [m.to_dict() for m in misi_list]
    
    return jsonify({
        "status": "sukses",
        "misi": results,
        "total": len(results),
    })


@app.route("/api/missions", methods=["POST"])
def tambah_mission():
    """Tambah misi baru."""
    pengelola = penyimpanan.baca_data()
    
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "pesan": "Data tidak diterima"}), 400
    
    try:
        misi_result = pengelola.tambah_misu(
            judul=data.get("judul", ""),
            mata_kuliah=data.get("mata_kuliah", ""),
            deskripsi=data.get("deskripsi", ""),
            jenis=data.get("jenis", "individu"),
            tingkat_kesulitan=data.get("tingkat_kesulitan", "mudah"),
            tenggat=data.get("tengggat"),
        )
        penyimpanan.tulis_data(pengelola)
        return jsonify({"status": "sukses", "data": misi_result}), 201
    except ValueError as e:
        return jsonify({"status": "error", "pesan": str(e)}), 400


@app.route("/api/missions/<misi_id>", methods=["PUT"])
def edit_mission(misi_id):
    """Edit misi."""
    pengelola = penyimpanan.baca_data()
    
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "pesan": "Data tidak diterima"}), 400
    
    try:
        result = pengelola.edit_misu(
            misi_id=misi_id,
            judul=data.get("judul"),
            mata_kuliah=data.get("mata_kuliah"),
            deskripsi=data.get("deskripsi"),
            jenis=data.get("jenis"),
            tingkat_kesulitan=data.get("tingkat_kesulitan"),
            tenggat=data.get("tengggat"),
            status=data.get("status"),
        )
        penyimpanan.tulis_data(pengelola)
        return jsonify({"status": "sukses", "data": result}), 200
    except ValueError as e:
        return jsonify({"status": "error", "pesan": str(e)}), 400


@app.route("/api/missions/<misi_id>/complete", methods=["POST"])
def complete_mission(misi_id):
    """Selesaikan misi - memberikan XP."""
    pengelola = penyimpanan.baca_data()
    
    try:
        result = pengelola.selesaikan_misu(misi_id)
        penyimpanan.tulis_data(pengelola)
        return jsonify({"status": "sukses", "data": result}), 200
    except ValueError as e:
        return jsonify({"status": "error", "pesan": str(e)}), 400


@app.route("/api/missions/<misi_id>", methods=["DELETE"])
def hapus_mission(misi_id):
    """Hapus misi."""
    pengelola = penyimpanan.baca_data()
    
    try:
        result = pengelola.hapus_misu(misi_id)
        penyimpanan.tulis_data(pengelola)
        return jsonify({"status": "sukses", "data": result}), 200
    except ValueError as e:
        return jsonify({"status": "error", "pesan": str(e)}), 400


# --- Achievements ---

@app.route("/api/achievements")
def achievements():
    """Ringkasan badge pengguna."""
    pengelola = penyimpanan.baca_data()
    user = pengelola.user
    
    # Count misi selesai per jenis
    misi_selesai = len([m for m in pengelola._misi_list if m.status == "selesai"])
    misi_ujian_selesai = len([m for m in pengelola._misi_list 
                              if m.status == "selesai" and m.jenis == "ujian"])
    
    # Badges berdasarkan kriteria
    badges = {
        "langkah_pertama": "Langkah Pertama" in user.badges,
        "pemburu_misi": "Pemburu Misi" in user.badges and misi_selesai >= 5,
        "pejuang_ujian": "Pejuang Ujian" in user.badges and misi_ujian_selesai >= 3,
        "naik_kelas": "Naik Kelas" in user.badges and user.level >= 5,
    }
    
    # Hitung progres badge
    badge_progres = {
        "langkah_pertama": {
            "kriteria": "Selesaikan 1 misi",
            "tercapai": badges["langkah_pertama"],
        },
        "pemburu_misi": {
            "kriteria": "Selesaikan 5 misi",
            "tercapai": badges["pemburu_misi"],
            "progress": min(misi_selesai / 5 * 100, 100),
        },
        "pejuang_ujian": {
            "kriteria": "Selesaikan 3 misi ujian",
            "tercapai": badges["pejuang_ujian"],
            "progress": min(misi_ujian_selesai / 3 * 100, 100),
        },
        "naik_kelas": {
            "kriteria": "Pencapaian level 5",
            "tercapai": badges["naik_kelas"],
        },
    }
    
    return jsonify({
        "status": "sukses",
        "badges": badges,
        "badge_progres": badge_progres,
        "user_badges": user.badges,
        "misi_selesai_total": misi_selesai,
        "level": user.level,
    })


# --- History ---

@app.route("/api/history")
def history():
    """Riwayat penyelesaian misi."""
    pengelola = penyimpanan.baca_data()
    
    # Ambil riwayat (misi yang sudah selesai)
    selesai_list = [m for m in pengelola._misi_list if m.status == "selesai"]
    
    # Urutkan berdasarkan waktu penyelesaian terbaru (sort berdasarkan id atau timestamp)
    # Asumsi: misi yang diselesaikan lebih baru memiliki ID yang lebih tinggi atau waktu diselesaikan lebih baru
    selesai_list.sort(key=lambda x: x.diselesaikan_pada or "", reverse=True)
    
    results = []
    for m in selesai_list[:20]:  # Ambil 20 terbaru
        results.append({
            "judul": m.judul,
            "jenis": m.jenis,
            "tingkat_kesulitan": m.tingkat_kesulitan,
            "xp_dapat": m.hitung_xp(),
            "w_selesai": m.diselesaikan_pada or "Belum tercatat",
        })
    
    return jsonify({
        "status": "sukses",
        "history": results,
        "total": len(results),
    })


# --- Profile ---

@app.route("/api/profile", methods=["GET"])
def profile_get():
    """Ambil data profil pengguna."""
    pengelola = penyimpanan.baca_data()
    user = pengelola.user
    return jsonify({
        "status": "sukses",
        "user": user.to_dict(),
    })


@app.route("/api/profile", methods=["POST"])
def profile_post():
    """Update profil pengguna (nama dan avatar)."""
    pengelola = penyimpanan.baca_data()
    
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "pesan": "Data tidak diterima"}), 400
    
    try:
        user = pengelola.user
        if "name" in data:
            user.name = data["name"]
        if "avatar" in data:
            user.avatar = data["avatar"]
        
        # Simpan ke file
        penyimpanan.tulis_data(pengelola)
        
        return jsonify({
            "status": "sukses",
            "user": user.to_dict(),
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "pesan": str(e)}), 400


# --- Halaman Statis ---

@app.route("/missions")
def page_missions():
    """Halaman daftar misi (khusus dosen)."""
    if not role_wajib():
        return redirect(url_for("login"))
    if session.get("role") != "dosen":
        return redirect(url_for("dashboard"))
    return render_template("missions.html", misi_list=penyimpanan.baca_data()._misi_list)

@app.route("/achievements")
def page_achievements():
    """Halaman pencapaian."""
    if not role_wajib():
        return redirect(url_for("login"))
    pengelola = penyimpanan.baca_data()
    user = pengelola.user
    
    # Count misi selesai per jenis
    misi_selesai = len([m for m in pengelola._misi_list if m.status == "selesai"])
    misi_ujian_selesai = len([m for m in pengelola._misi_list 
                              if m.status == "selesai" and m.jenis == "ujian"])
    
    # Badges berdasarkan kriteria
    badges = {
        "langkah_pertama": "Langkah Pertama" in user.badges,
        "pemburu_misi": "Pemburu Misi" in user.badges and misi_selesai >= 5,
        "pejuang_ujian": "Pejuang Ujian" in user.badges and misi_ujian_selesai >= 3,
        "naik_kelas": "Naik Kelas" in user.badges and user.level >= 5,
    }
    
    # Hitung progres badge
    badge_progres = {
        "langkah_pertama": {
            "kriteria": "Selesaikan 1 misi",
            "tercapai": badges["langkah_pertama"],
        },
        "pemburu_misi": {
            "kriteria": "Selesaikan 5 misi",
            "tercapai": badges["pemburu_misi"],
            "progress": min(misi_selesai / 5 * 100, 100),
        },
        "pejuang_ujian": {
            "kriteria": "Selesaikan 3 misi ujian",
            "tercapai": badges["pejuang_ujian"],
            "progress": min(misi_ujian_selesai / 3 * 100, 100),
        },
        "naik_kelas": {
            "kriteria": "Pencapaian level 5",
            "tercapai": badges["naik_kelas"],
        },
    }
    
    return render_template("achievements.html",
        badges=badges,
        badge_progres=badge_progres,
        user_badges=user.badges,
        level=user.level,
        total_xp=user.total_xp,
        progress=user.progress,
        misi_selesai_total=misi_selesai,
    )

@app.route("/history")
def page_history():
    """Halaman riwayat."""
    if not role_wajib():
        return redirect(url_for("login"))
    pengelola = penyimpanan.baca_data()
    selesai_list = [m for m in pengelola._misi_list if m.status == "selesai"]
    selesai_list.sort(key=lambda x: x.diselesaikan_pada or "", reverse=True)
    history_list = [{
        "judul": m.judul,
        "jenis": m.jenis,
        "tingkat_kesulitan": m.tingkat_kesulitan,
        "xp_dapat": m.hitung_xp(),
        "w_selesai": m.diselesaikan_pada,
    } for m in selesai_list[:20]]
    return render_template("history.html", history_list=history_list)

@app.route("/profile")
def page_profile():
    """Halaman profil."""
    if not role_wajib():
        return redirect(url_for("login"))
    pengelola = penyimpanan.baca_data()
    user = pengelola.user
    return render_template("profile.html",
        user_name=session.get("user_name", user.name),
        user_avatar=user.avatar,
        total_xp=user.total_xp,
        level=user.level,
        progress=user.progress,
        role=session.get("role"),
    )


@app.route("/cek-soal")
def page_cek_soal():
    """Halaman cek soal (khusus mahasiswa / dosen preview sebagai mahasiswa)."""
    if not role_wajib():
        return redirect(url_for("login"))
    if session.get("role") != "mahasiswa":
        return redirect(url_for("dashboard"))
    soal_list = muat_soal()
    return render_template("soal.html",
        soal_list=soal_list,
        user_name=session.get("user_name", "Mahasiswa"),
        role=session.get("role"),
        preview_as_dosen=session.get("preview_as_dosen", False),
    )


# --- Unggah Soal (Dosen) ---

@app.route("/unggah-soal", methods=["GET", "POST"])
def unggah_soal():
    """Halaman unggah soal untuk dosen."""
    if not role_wajib():
        return redirect(url_for("login"))
    if session.get("role") != "dosen":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        tipe = request.form.get("tipe", "")
        mata_kuliah = request.form.get("mata_kuliah", "").strip()

        if not mata_kuliah:
            return render_template("unggah-soal.html",
                error="Mata kuliah wajib diisi.",
                soal_list=muat_soal_universal(),
                role=session.get("role"),
            )

        soal_list = muat_soal_universal()
        id_soal = f"soal_{len(soal_list) + 1:03d}"

        if tipe == "pilihan_ganda":
            pertanyaan = request.form.get("pertanyaan", "").strip()
            pilihan = [
                request.form.get("pilihan_a", ""),
                request.form.get("pilihan_b", ""),
                request.form.get("pilihan_c", ""),
                request.form.get("pilihan_d", ""),
            ]
            jawaban_benar = request.form.get("jawaban_benar", "")

            if not pertanyaan or not jawaban_benar:
                return render_template("unggah-soal.html",
                    error="Pertanyaan dan jawaban benar wajib diisi.",
                    soal_list=soal_list,
                    role=session.get("role"),
                )

            soal_baru = {
                "id": id_soal,
                "tipe": "pilihan_ganda",
                "pertanyaan": pertanyaan,
                "pilihan": pilihan,
                "jawaban_benar": jawaban_benar,
                "mata_kuliah": mata_kuliah,
                "unggah_oleh": session.get("user_name", "Dosen"),
                "tanggal_unggah": __import__("datetime").datetime.now().isoformat(),
                "status": "belum_dikerjakan",
            }
        else:
            # PDF - simpan nama file saja
            file = request.files.get("file_pdf")
            if not file or not file.filename:
                return render_template("unggah-soal.html",
                    error="File PDF wajib diunggah.",
                    soal_list=soal_list,
                    role=session.get("role"),
                )

            import uuid
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext != "pdf":
                return render_template("unggah-soal.html",
                    error="File harus berformat PDF.",
                    soal_list=soal_list,
                    role=session.get("role"),
                )

            nama_file = f"{id_soal}_{uuid.uuid4().hex[:8]}.pdf"
            upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "soal")
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, nama_file))

            soal_baru = {
                "id": id_soal,
                "tipe": "pdf",
                "nama_file": nama_file,
                "nama_asli": file.filename,
                "mata_kuliah": mata_kuliah,
                "unggah_oleh": session.get("user_name", "Dosen"),
                "tanggal_unggah": __import__("datetime").datetime.now().isoformat(),
                "status": "belum_dikerjakan",
            }

        soal_list.append(soal_baru)
        tulis_soal_universal(soal_list)

        return render_template("unggah-soal.html",
            success=f"Soal {id_soal} berhasil diunggah!",
            soal_list=muat_soal_universal(),
            role=session.get("role"),
        )

    return render_template("unggah-soal.html",
        soal_list=muat_soal_universal(),
        role=session.get("role"),
    )


# --- Soal untuk Mahasiswa ---

@app.route("/soal-mahasiswa")
def soal_mahasiswa():
    """Halaman soal untuk dikerjakan mahasiswa (atau dosen preview)."""
    if not role_wajib():
        return redirect(url_for("login"))
    if session.get("role") != "mahasiswa":
        return redirect(url_for("dashboard"))

    soal_list = muat_soal_universal()
    jawaban_list = muat_jawaban_mahasiswa()
    nim = session.get("nim", "")

    # Filter: soal yang belum dikerjakan mahasiswa ini
    soal_belum = []
    for s in soal_list:
        sudah = any(j.get("id_soal") == s["id"] and j.get("nim") == nim for j in jawaban_list)
        if not sudah:
            soal_belum.append(s)

    # Soal yang sudah dikerjakan
    soal_selesai = []
    for s in soal_list:
        jawab = next((j for j in jawaban_list if j.get("id_soal") == s["id"] and j.get("nim") == nim), None)
        if jawab:
            soal_selesai.append({"soal": s, "jawaban": jawab})

    return render_template("soal-mahasiswa.html",
        soal_belum=soal_belum,
        soal_selesai=soal_selesai,
        user_name=session.get("user_name", "Mahasiswa"),
        role=session.get("role"),
        preview_as_dosen=session.get("preview_as_dosen", False),
    )


# --- Kirim Jawaban (Mahasiswa saja, Dosen DILARANG) ---

@app.route("/kirim-jawaban", methods=["POST"])
def kirim_jawaban():
    """Kirim jawaban mahasiswa. Dosen DILARANG mengerjakan soal."""
    if not role_wajib():
        return redirect(url_for("login"))

    # BLOKIR: Dosen (baik asli maupun preview) tidak boleh mengerjakan soal
    if session.get("role") == "dosen":
        return jsonify({"status": "error", "pesan": "Dosen tidak boleh mengerjakan soal!"}), 403
    if session.get("preview_as_dosen"):
        return jsonify({"status": "error", "pesan": "Mode preview - Anda tidak bisa mengerjakan soal!"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "pesan": "Data tidak diterima"}), 400

    id_soal = data.get("id_soal", "")
    jawaban = data.get("jawaban", "").strip()

    if not id_soal or not jawaban:
        return jsonify({"status": "error", "pesan": "Soal dan jawaban wajib diisi"}), 400

    soal_list = muat_soal_universal()
    soal = next((s for s in soal_list if s["id"] == id_soal), None)
    if not soal:
        return jsonify({"status": "error", "pesan": "Soal tidak ditemukan"}), 404

    nim = session.get("nim", "")
    jawaban_list = muat_jawaban_mahasiswa()

    # Cek apakah sudah pernah dijawab
    if any(j.get("id_soal") == id_soal and j.get("nim") == nim for j in jawaban_list):
        return jsonify({"status": "error", "pesan": "Soal sudah pernah dijawab"}), 400

    # Hitung benar/salah (untuk pilihan ganda)
    benar_salah = None
    if soal.get("tipe") == "pilihan_ganda":
        benar_salah = "benar" if jawaban == soal.get("jawaban_benar") else "salah"

    jawaban_baru = {
        "id_soal": id_soal,
        "nim": nim,
        "nama": session.get("user_name", ""),
        "jawaban": jawaban,
        "benar_salah": benar_salah,
        "waktu_dikerjakan": __import__("datetime").datetime.now().isoformat(),
    }
    jawaban_list.append(jawaban_baru)
    tulis_jawaban_mahasiswa(jawaban_list)

    # Update status soal
    soal["status"] = "dikerjakan"
    tulis_soal_universal(soal_list)

    return jsonify({
        "status": "sukses",
        "pesan": "Jawaban berhasil dikirim!",
        "benar_salah": benar_salah,
    }), 200


# --- Lihat Progres (Dosen) ---

@app.route("/lihat-progres")
def lihat_progres():
    """Halaman lihat progres jawaban mahasiswa (khusus dosen)."""
    if not role_wajib():
        return redirect(url_for("login"))
    if session.get("role") != "dosen":
        return redirect(url_for("dashboard"))

    soal_list = muat_soal_universal()
    jawaban_list = muat_jawaban_mahasiswa()

    # Gabungkan data soal dengan jawaban
    progres = []
    for s in soal_list:
        jawaban_soal = [j for j in jawaban_list if j.get("id_soal") == s["id"]]
        progres.append({
            "soal": s,
            "jawaban_list": jawaban_soal,
            "total_jawab": len(jawaban_soal),
        })

    return render_template("lihat-progres.html",
        progres=progres,
        total_soal=len(soal_list),
        total_jawaban=len(jawaban_list),
        role=session.get("role"),
    )


# --- Perspektif Mahasiswa (Dosen lihat tapi TIDAK BISA mengerjakan) ---

@app.route("/perspektif-mahasiswa")
def perspektif_mahasiswa():
    """Dosen melihat dari posisi mahasiswa - READ ONLY, tidak bisa mengerjakan."""
    if not role_wajib():
        return redirect(url_for("login"))
    if session.get("role") != "dosen":
        return redirect(url_for("dashboard"))

    soal_list = muat_soal_universal()
    jawaban_list = muat_jawaban_mahasiswa()

    return render_template("perspektif-mahasiswa.html",
        soal_list=soal_list,
        jawaban_list=jawaban_list,
        role=session.get("role"),
        preview_only=True,
    )


# --- Static Data Demo (dijalankan sekali) ---

@app.route("/setup-demo", methods=["POST"])
def setup_demo():
    """Setup data demo awal (hanya untuk dosen)."""
    if session.get("role") != "dosen":
        return jsonify({"status": "error", "pesan": "Hanya dosen yang boleh setup demo"}), 403
    pengelola = penyimpanan.baca_data()
    
    # Cek apakah sudah ada data demo (lihat apakah misi ada dengan demo flag)
    # Jika belum, tambah data demo
    data_demo = pengelola.to_dict()
    
    # Tambahkan beberapa misi demo jika kosong
    if not pengelola._misi_list:
        from models.individu import MisiIndividu
        from models.kelompok import MisiKelompok
        from models.ujian import MisiUjian
        import uuid
        
        demo_misi = [
            MisiIndividu(
                id=f"demo_{i:03d}",
                judul=f"Tugas {i+1}: Analisis Requirements",
                mata_kuliah="Pemrograman Berorientasi Objek",
                deskripsi="Mengerjakan praktikum mengenai class dan object",
                jenis="individu",
                tingkat_kesulitan="sedang",
                tenggat=(__import__("datetime").date.today()).isoformat(),
                status="belum mulai",
            )
            for i in range(3)
        ]
        
        for m in demo_misi:
            pengelola._misi_list.append(m)
    
    # Tulis ke file
    penyimpanan.tulis_data(pengelola)
    
    return jsonify({
        "status": "sukses",
        "pesan": "Data demo berhasil di-setup",
    }), 200


# --- Error Handlers ---

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "pesan": "Endpoint tidak ditemukan"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"status": "error", "pesan": "Method tidak diizinkan"}), 405


# --- Main ---

if __name__ == "__main__":
    # Pastikan data directory ada
    os.makedirs(penyimpanan._data_dir, exist_ok=True)
    
    # Jalankan aplikasi
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)