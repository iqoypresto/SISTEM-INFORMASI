from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import firebase_admin
from firebase_admin import credentials, firestore
from functools import wraps
import requests
from requests.structures import CaseInsensitiveDict

cred = credentials.Certificate('firebase.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask ('__name__')
app.secret_key = "iTulaH"

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' in session :
            return f(*args, **kwargs)
        
        else:
            flash("Anda harus login terlebih dahulu!", "danger")
            return redirect(url_for('login'))
    return wrapper

def send_wa(m, p):
    api = "276ae77385b483b3c0b75330b955f8d184f96392"
    url = "https://starsender.online/api/sendText"

    data = {
        "tujuan": p,
        "message": m
    }

    headers = CaseInsensitiveDict()
    headers["apikey"] = api 

    res = requests.post(url, json=data, headers=headers)
    return res.text

# harus install firebase admin untuk menghubungkan dengan firebase #

@app.route('/')
def index():
    return render_template ('index.html')

@app.route('/dashboard')
@login_required
def dashboard ():
    return render_template ('dashboard.html')

@app.route('/mahasiswa')
@login_required
def mahasiswa ():
    # panggil data di database
    # lakukan pengulangan terhadap data
    # simpan data yang sudah di uland dalam sebuah array

    maba = db.collection("mahasiswa").stream()
    mb = []

    for mhs in maba :
        m = mhs.to_dict()
        m["id"] = mhs.id
        mb.append(m)

    return render_template ('mahasiswa.html', mb=mb)

@app.route('/mahasiswa/tambah', methods=["GET", "POST"])
@login_required
def tambah_mhs ():
    if request.method == 'POST':
        data = {
            "nama": request.form["nama"],
            "nim": request.form["nim"],
            "email": request.form["email"],
            "jurusan": request.form["jurusan"]

        }
        db.collection("mahasiswa").document().set(data)
        flash ("Berhasil Menambahkan Mahasiswa", "success")
        return redirect(url_for('mahasiswa'))
        
        
    return render_template ('add_mhs.html')

@app.route('/mahasiswa/hapus/<uid>')
def hapus_mhs (uid):
    db.collection('mahasiswa').document(uid).delete()
    flash("Berhasil Menghapus Mahasiswa", "danger")
    return redirect(url_for('mahasiswa'))


@app.route('/mahasiswa/lihat/<uid>')
def lihat_mhs (uid):
    user = db.collection('mahasiswa').document(uid).get().to_dict()
    return render_template ('lihat_mhs.html', user=user)

@app.route('/mahasiswa/ubah/<uid>', methods = ["GET", "POST"])
def ubah_mhs (uid):
    # menentukan method
    if request.method == 'POST':
        data = {
            "nama": request.form["nama"],
            "nim": request.form["nim"],
            "email": request.form["email"],
            "jurusan": request.form["jurusan"]

        }
        db.collection('mahasiswa').document(uid).set(data, merge=True)
        return redirect(url_for('mahasiswa'))
    # menerima data baru
    # set di database

    # mengambil data
    user = db.collection('mahasiswa').document(uid).get().to_dict()
    user ['id'] = uid
    # render template
    return render_template('ubah_mhs.html', user=user)

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        data = {
        "namalengkap": request.form["namalengkap"],
        "tanggallahir": request.form["tanggallahir"],
        "nohp": request.form["nohp"],
        "email": request.form["email"]
        }

        
        users = db.collection('users').where("email", "==", data['email']).stream()
        user = {}

        for us in users :
            user = us
        
        if user:
            flash("Email sudah terdaftar! Silahkan gunakan email lain", "danger")
            return redirect(url_for('register'))

        data["password"] = generate_password_hash(request.form["password"], 'sha256')

        send_wa(f"Selamat Datang! *{data['namalengkap']}* Akun anda telah dibuat", data['nohp'])
        db.collection('users').document().set(data)
        flash ("Berhasil Register, silahkan Login", "success")
        return redirect(url_for('login'))

    
    return render_template ('register.html')

@app.route('/login', methods = ["GET", "POST"])
def login ():
    if request.method == "POST":
        data= {
            "email": request.form["email"],
            "password": request.form["password"]

        }

        users=db.collection('users').where("email", "==", data["email"]).stream()
        user = {}

        for us in users :
            user = us.to_dict()
        
        if user:
            if check_password_hash(user["password"], data["password"]):
                session["user"] = user
                flash("Selamat Anda Berhasil Login", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Maaf Password Anda Salah! Silahkan Coba Lagi", "danger")
                return redirect(url_for('login'))
        else:
            flash("Akun anda belum Terdaftar, Silahkan mendaftar terlebih dahulu", "danger")
            return redirect(url_for('login'))
        
    if 'user' in session:
        return redirect (url_for('dashboard'))

    return render_template ('login.html')

@app.route('/logout')
def logout ():
    session.clear()
    return redirect (url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)