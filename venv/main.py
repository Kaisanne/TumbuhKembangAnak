from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from config import Config
import MySQLdb.cursors
import re
import bcrypt 
from datetime import datetime
import pytz
from dateutil import relativedelta
from flask_cors import CORS, cross_origin
from Status import *

app = Flask(__name__)
cors = CORS(app)
app.config.from_object(Config())
mysql = MySQL(app)

# Account
## Register
@app.route('/register', methods =['POST'])
@cross_origin()
def register():
    msg = ''
    status = ''
    if request.method == 'POST' and 'username' in request.json and 'password' in request.json and 'email' in request.json and 'nama' in request.json :
        username = request.json['username']
        password = request.json['password']
        email = request.json['email']
        nama = request.json['nama']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM orangtua WHERE username = % s OR email = % s", (username, email, ))
        account = cursor.fetchone()
        if account:
            msg = 'Akun sudah ada'
            status = '400'
        elif not username or not password or not email or not nama:
            msg = 'Tolong isi data terlebih dahulu'
            status = '400'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Email tidak valid'
            status = '400'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username harus terdiri dari huruf dan angka'
            status = '400'
        elif len(email.split('@')[0]) > 64 or len(email.split('@')[1]) >255:
            msg = 'Email tidak valid.'
            status = '400'
        elif len(email) > 320:
            msg = 'Email terlalu panjang. Maksimum 320 karakter.'
            status = '400'
        elif len(username) > 50:
            msg = 'Username terlalu panjang. Maksimum 50 karakter.'
            status = '400'
        else:
            cursor.execute("INSERT INTO orangtua (nama, email, username, password) VALUES (% s, % s, % s, %s)", (nama, email, username, hashed_password, ))
            mysql.connection.commit()
            msg = 'Akun berhasil terbuat'
            status = '200'
    elif request.method == 'POST':
        msg = 'Tolong isi data terlebih dahulu!'
        status = '400'
    return jsonify({'status_code': status, 'message': msg})

## Sign In
@app.route('/signin', methods =['POST'])
@cross_origin()
def signin():
    msg = ''
    status = ''
    data = 0
    if request.method == 'POST' and 'username' in request.json and 'password' in request.json :
        username = request.json['username']
        password = request.json['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM orangtua WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account and bcrypt.checkpw(password.encode('utf-8'), account['password']):
            msg = 'Berhasil masuk ke akun'
            status = '200'
            data = account['id']
        elif not username or not password:
            msg = 'Tolong isi username atau password!'
            status = '400'
        else:
            msg = 'Username atau password tidak sesuai!'
            status = '400'
    else:
        msg = 'Tolong isi username atau password!'
        status = '400'
    return jsonify({'status_code': status, 'message': msg, 'data': data})

# ================
# Children
## Get Children List from Parent Id
@app.route('/children/<int:id_orangtua>')
@cross_origin()
def get_children_of_parent(id_orangtua):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM anak WHERE id_orangtua = %s;', (id_orangtua, ))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Add Child Data
@app.route('/children', methods =['POST'])
@cross_origin()
def add_children():
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST' and 'nama' in request.json and 'gender' in request.json and 'dob' in request.json and 'id_orangtua' in request.json :
        nama = request.json['nama']
        gender = request.json['gender']
        dob = request.json['dob']
        id_orangtua = request.json['id_orangtua']
        if not nama or not gender or not dob:
            msg = 'Tolong isi data terlebih dahulu'
            status = '400'
        else:
            cursor.execute("INSERT INTO anak (nama, gender, dob, id_orangtua) VALUES (% s, % s, % s, %s)", (nama, gender, dob, id_orangtua, ))
            mysql.connection.commit()
            msg = 'Berhasil ditambahkan'
            status = '200'
        
    else:
        msg = 'Tolong isi data terlebih dahulu'
        status = '400'

    return jsonify({'status_code': status, 'message': msg})


# ================
# TODO: belum dicoba
# DASHBOARD 
## Get growth status
@app.route('/dashboard-tumbuh/<int:id_anak>', methods=['GET'])
@cross_origin()
def get_status_tumbuh(id_anak):
    msg = ''
    status = ''
    getMonth = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    getMonth.execute('SELECT dob FROM anak WHERE id = %s;', (id_anak, ))
    # get two dates
    # d1 = str(getMonth)
    d1 = getMonth.fetchone()
    d2 = str(datetime.now(pytz.timezone('Asia/Jakarta')))
    d2 = d2[:10]

    # convert string to date object
    start_date = datetime.strptime(str(d1["dob"]), "%Y-%m-%d")
    end_date = datetime.strptime(d2, "%Y-%m-%d")

    # Get the relativedelta between two dates
    delta = relativedelta.relativedelta(end_date, start_date)
    bulan = delta.months
    tahun = delta.years
    total_bulan = (tahun * 12) + bulan
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM pertumbuhanPerBulan JOIN statusTinggi ON statusTinggi.id = pertumbuhanPerBulan.id_status_tinggi JOIN statusBerat ON statusBerat.id = pertumbuhanPerBulan.id_status_berat WHERE pertumbuhanPerBulan.id_anak = %s AND pertumbuhanPerBulan.bulan = %s ;', (id_anak, total_bulan,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Get development status
@app.route('/dashboard-kembang/<int:id_anak>', methods=['GET'])
@cross_origin()
def get_status_kembang(id_anak):
    msg = ''
    status = ''
    getMonth = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    getMonth.execute('SELECT dob FROM anak WHERE id = %s;', (id_anak, ))
    # get two dates
    # d1 = str(getMonth)
    d1 = getMonth.fetchone()
    d2 = str(datetime.now(pytz.timezone('Asia/Jakarta')))
    d2 = d2[:10]

    # convert string to date object
    start_date = datetime.strptime(str(d1["dob"]), "%Y-%m-%d")
    end_date = datetime.strptime(d2, "%Y-%m-%d")

    # Get the relativedelta between two dates
    delta = relativedelta.relativedelta(end_date, start_date)
    bulan = delta.months
    tahun = delta.years
    total_bulan = (tahun * 12) + bulan
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT statusPerkembangan.status FROM statusPerkembanganPerBulan JOIN statusPerkembangan ON statusPerkembanganPerBulan.id_status_perkembangan = statusPerkembangan.id WHERE statusPerkembanganPerBulan.id_anak = %s AND statusPerkembanganPerBulan.bulan = %s;', (id_anak, total_bulan, ))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Get vaccination 
@app.route('/dashboard-imunisasi/<int:id_anak>', methods=['GET'])
@cross_origin()
def get_current_vaccination(id_anak):
    msg = ''
    status = ''
    getMonth = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    getMonth.execute('SELECT dob FROM anak WHERE id = %s;', (id_anak, ))
    d1 = getMonth.fetchone()
    d2 = str(datetime.now(pytz.timezone('Asia/Jakarta')))
    d2 = d2[:10]

    # convert string to date object
    start_date = datetime.strptime(str(d1["dob"]), "%Y-%m-%d")
    end_date = datetime.strptime(d2, "%Y-%m-%d")

    # Get the relativedelta between two dates
    delta = relativedelta.relativedelta(end_date, start_date)
    bulan = delta.months
    tahun = delta.years
    total_bulan = (tahun * 12) + bulan
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM vaksin JOIN vaksin_detail ON vaksin_detail.id_vaksin = vaksin.id WHERE vaksin_detail.bulan_awal = %s',(total_bulan,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})


# ================
# Growth
## Get Growth based on child id and month
## TODO: Join dengan statusPertumbuhan dan artikel
@app.route('/detail-growth/<int:id_pertumbuhan>')
@cross_origin()
def get_child_growth(id_pertumbuhan):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM pertumbuhanPerBulan JOIN statusTinggi ON statusTinggi.id = pertumbuhanPerBulan.id_status_tinggi JOIN statusBerat ON statusBerat.id = pertumbuhanPerBulan.id_status_berat WHERE pertumbuhanPerBulan.id = %s;', (id_pertumbuhan,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Get Artikel based on Status Tinggi and Status Berat
@app.route('/detail-growth/article/<int:id_pertumbuhan>')
@cross_origin()
def get_growth_article(id_pertumbuhan):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id_status_tinggi, id_status_berat FROM pertumbuhanPerBulan WHERE pertumbuhanPerBulan.id = %s;', (id_pertumbuhan,))
    status = cursor.fetchone()
    cursor.execute('SELECT * FROM artikel WHERE id_statusTinggi = %s OR id_statusBerat = %s;', (status["id_status_tinggi"],status["id_status_berat"],))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Get List of Child Growth
@app.route('/list-growth/<int:id_anak>')
@cross_origin()
def get_child_list_growth(id_anak):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT DISTINCT id, bulan FROM pertumbuhanPerBulan WHERE id_anak = %s ORDER BY bulan DESC;', (id_anak,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Add Growth based on child id and month
@app.route('/growth/create/<int:id_anak>', methods =['POST'])
@cross_origin()
def create_child_growth(id_anak):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and 'bulan' in request.json and 'tinggi' in request.json and 'berat' in request.json and 'lingkarKepala' in request.json :
        tinggi = request.json['tinggi']
        berat = request.json['berat']
        lingkarKepala = request.json['lingkarKepala']
        bulan = request.json['bulan']
        if not berat and not tinggi:
            msg = 'Tolong isi data terlebih dahulu'
            status = '400'
        else:
            cursor.execute("SELECT gender FROM anak WHERE id = %s", (id_anak, ))
            genderData = cursor.fetchone()
            gender = str(genderData["gender"])
            statTinggi = statusTinggi(ZSHeight(gender, bulan, tinggi))
            statBerat = statusBerat(ZSWeight(gender, bulan, berat))
            cursor.execute("SELECT * FROM pertumbuhanPerBulan WHERE id_anak = %s AND bulan = %s", (id_anak, bulan, ))
            data = cursor.fetchone()
            if data:
                cursor.execute("UPDATE pertumbuhanPerBulan SET tinggi = %s, berat = %s, lingkar_kepala = %s, id_status_tinggi = %s, id_status_berat = %s  WHERE id_anak = %s AND bulan = %s", (tinggi, berat, lingkarKepala, statTinggi, statBerat, id_anak, bulan, ))
                mysql.connection.commit()
                msg = 'Data berhasil diubah'
                status = '200'
            else:
                cursor.execute("INSERT INTO pertumbuhanPerBulan (tinggi, berat, lingkar_kepala, id_status_tinggi, id_status_berat, id_anak, bulan) VALUES (% s, % s, %s, %s, %s, %s, %s)", (tinggi, berat, lingkarKepala, statTinggi, statBerat, id_anak, bulan, ))
                mysql.connection.commit()
                msg = 'Data Berhasil ditambahkan'
                status = '200'
    elif request.method == 'POST':
        msg = 'Tolong isi data terlebih dahulu'
        status = '400'
    return jsonify({'status_code': status, 'message': msg})


# ================
# DEVELOPMENT
## Get Development based on child id and month
@app.route('/detail-development/<int:id_anak>/<int:bulan>')
@cross_origin()
def get_child_development(id_anak, bulan):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM perkembanganPerBulan JOIN perkembangan ON perkembanganperbulan.id_perkembangan = perkembangan.id WHERE perkembanganperbulan.id_anak = %s AND perkembanganperbulan.bulan = %s ORDER BY perkembangan.bulan ASC;', (id_anak, bulan,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

@app.route('/exercise/<int:id_anak>/<int:bulan>')
@cross_origin()
def get_excercise(id_anak, bulan):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('CALL getExercise(%s, %s);', (id_anak, bulan,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Get list for Development history
@app.route('/list-development/<int:id_anak>')
@cross_origin()
def get_child_list_development(id_anak):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM perkembanganPerBulan WHERE id IN (SELECT MAX(id) FROM perkembanganperbulan WHERE id_anak = %s GROUP BY bulan) ORDER BY bulan DESC;', (id_anak,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Add or Delete Development based on child id and month
## TODO: Create Tambah ke statusPerkembanganPerBulan
@app.route('/development/create/<int:id_anak>/<int:bulan>', methods =['POST', 'DELETE'])
@cross_origin()
def create_child_development(id_anak, bulan):
    msg = ''
    status = ''
    if request.method == 'POST' and 'id_perkembangan' in request.json :
        id_perkembangan = request.json['id_perkembangan']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO perkembanganPerBulan (id_perkembangan, id_anak, bulan) VALUES (% s, % s, % s)", (id_perkembangan, id_anak, bulan, ))
        mysql.connection.commit()
        msg = 'Data Berhasil ditambahkan'
        status = '200'
    elif request.method == 'POST':
        msg = 'Tolong isi data terlebih dahulu'
        status = '400'
    return jsonify({'status_code': status, 'message': msg})

## Get last month development that haven't selected
@app.route('/last-dev/<int:id_anak>/<int:bulan>')
@cross_origin()
def get_last_development(id_anak, bulan):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('CALL getPastDev(%s, %s);', (id_anak, bulan, ))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Get last month development that haven't selected
@app.route('/curr-dev/<int:id_anak>/<int:bulan>')
@cross_origin()
def get_curr_development(id_anak, bulan):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('CALL getCurrDev(%s, %s);', (id_anak, bulan, ))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

@app.route('/next-dev/<int:id_anak>/<int:bulan>')
@cross_origin()
def get_next_development(id_anak, bulan):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('CALL getNextDev(%s, %s);', (id_anak, bulan, ))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

@app.route('/dev-now/<int:id_anak>')
@cross_origin()
def get_dev_now(id_anak):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT dob FROM anak WHERE id = %s;', (id_anak, ))
    # get two dates
    d1 = cursor.fetchone()
    d2 = str(datetime.now(pytz.timezone('Asia/Jakarta')))
    d2 = d2[:10]
    # convert string to date object
    start_date = datetime.strptime(str(d1["dob"]), "%Y-%m-%d")
    end_date = datetime.strptime(d2, "%Y-%m-%d")

    # Get the relativedelta between two dates
    delta = relativedelta.relativedelta(end_date, start_date)
    bulan = delta.months
    tahun = delta.years
    total_bulan = (tahun * 12) + bulan
    cursor.execute('SELECT * FROM perkembanganPerBulan JOIN perkembangan ON perkembanganperbulan.id_perkembangan = perkembangan.id WHERE perkembanganperbulan.id_anak = %s AND perkembanganperbulan.bulan = %s;', (id_anak, total_bulan,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Development Progress line
@app.route('/dev/progress/<int:id_anak>')
@cross_origin()
def get_dev_progress(id_anak):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT count(id_anak) FROM perkembanganperbulan WHERE id_anak = %s;', (id_anak, ))
    dev_progress = cursor.fetchone()

    # Get the relativedelta between two dates
    cursor.execute('SELECT count(keterangan) FROM perkembangan;')
    total_dev = cursor.fetchone()
    data = {
        "percentage": dev_progress["count(id_anak)"]/total_dev["count(keterangan)"],
        "total_dev": total_dev["count(keterangan)"],
        "dev_progress": dev_progress["count(id_anak)"]
    }
    
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

@app.route('/dev/month-progress/<int:id_anak>/<int:bulan>')
@cross_origin()
def get_dev_month_progress(id_anak, bulan):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT count(id_anak) FROM perkembanganperbulan JOIN perkembangan ON perkembanganperbulan.id_perkembangan = perkembangan.id WHERE perkembanganperbulan.id_anak = %s AND (perkembanganperbulan.bulan = %s OR perkembangan.bulan = %s);', (id_anak, bulan, bulan, ))
    dev_progress = cursor.fetchone()

    cursor.execute('SELECT count(keterangan) FROM perkembangan WHERE bulan = %s;', (bulan,))
    total_dev = cursor.fetchone()
    data = {
        "percentage": dev_progress["count(id_anak)"]/total_dev["count(keterangan)"],
        "total_dev": total_dev["count(keterangan)"],
        "dev_progress": dev_progress["count(id_anak)"]
    }
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

# ================
# FORUM
## Get all discussion
@app.route('/questions')
@cross_origin()
def get_all_discussions():
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT pertanyaan.id, pertanyaan.pertanyaan, pertanyaan.created_at, orangtua.nama FROM pertanyaan JOIN orangtua ON pertanyaan.id_orangtua = orangtua.id ORDER BY pertanyaan.created_at DESC;')
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Get reply based on discussion id
@app.route('/question/<int:id_pertanyaan>/reply', methods=['GET'])
@cross_origin()
def get_reply_id(id_pertanyaan):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT jawaban.id, jawaban.jawaban, jawaban.created_at, orangtua.nama FROM jawaban JOIN orangtua ON jawaban.id_orangtua = orangtua.id WHERE id_pertanyaan = %s ORDER BY jawaban.created_at DESC;', (id_pertanyaan, ))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Get dicussion based on discussion id
@app.route('/question/<int:id_pertanyaan>')
@cross_origin()
def get_discussion_id(id_pertanyaan):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT pertanyaan.id, pertanyaan.pertanyaan, pertanyaan.created_at, orangtua.nama FROM pertanyaan JOIN orangtua ON pertanyaan.id_orangtua = orangtua.id WHERE pertanyaan.id = %s;', (id_pertanyaan, ))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Create discussion
@app.route('/question', methods =['POST'])
@cross_origin()
def create_question():
    msg = ''
    status = ''
    if request.method == 'POST' and 'pertanyaan' in request.json and 'id_orangtua' in request.json :
        pertanyaan = request.json['pertanyaan']
        id_orangtua = request.json['id_orangtua']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute("INSERT INTO pertanyaan (pertanyaan, id_orangtua) VALUES (% s, % s)", (pertanyaan, id_orangtua, ))
        mysql.connection.commit()
        msg = 'Data Berhasil ditambahkan'
        status = '200'
    elif request.method == 'POST':
        msg = 'Tolong isi data terlebih dahulu'
        status = '400'
    return jsonify({'status_code': status, 'message': msg})

## Create reply
@app.route('/question/create/reply', methods =['POST'])
@cross_origin()
def create_reply():
    msg = ''
    status = ''
    if request.method == 'POST' and 'jawaban' in request.json and 'id_orangtua' in request.json and 'id_pertanyaan' in request.json :
        jawaban = request.json['jawaban']
        id_orangtua = request.json['id_orangtua']
        id_pertanyaan = request.json['id_pertanyaan']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute("INSERT INTO jawaban (jawaban, id_orangtua, id_pertanyaan) VALUES (% s, % s, %s)", (jawaban, id_orangtua, id_pertanyaan, ))
        mysql.connection.commit()
        msg = 'Data Berhasil ditambahkan'
        status = '200'
    elif request.method == 'POST':
        msg = 'Tolong isi data terlebih dahulu'
        status = '400'
    return jsonify({'status_code': status, 'message': msg})


# ================
# VACCINATION
## Vaccination history
@app.route('/vaccine/history/<int:id_anak>')
@cross_origin()
def get_vaccine_history(id_anak):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM history_vaksin JOIN vaksin_detail ON vaksin_detail.id = history_vaksin.id_vaksin_detail JOIN vaksin ON vaksin.id = vaksin_detail.id_vaksin JOIN vaksin_brand ON vaksin_brand.id = history_vaksin.id_vaksin_brand WHERE history_vaksin.id_anak = %s ORDER BY vaksin_detail.bulan_awal DESC;', (id_anak, ))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Not Recommended Vaccination
@app.route('/vaccine/not/<int:id_anak>')
@cross_origin()
def get_not_vaccine(id_anak):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM vaksin_not_recommend JOIN vaksin_detail ON vaksin_detail.id = vaksin_not_recommend.id_vaksin_detail JOIN vaksin ON vaksin.id = vaksin_detail.id_vaksin WHERE vaksin_not_recommend.id_anak = %s;', (id_anak, ))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Vaccination current
@app.route('/vaccine/current/<int:id_anak>')
@cross_origin()
def get_vaccine_current(id_anak):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT dob FROM anak WHERE id = %s;', (id_anak, ))
    # get two dates
    d1 = cursor.fetchone()
    d2 = str(datetime.now(pytz.timezone('Asia/Jakarta')))
    d2 = d2[:10]
    # convert string to date object
    start_date = datetime.strptime(str(d1["dob"]), "%Y-%m-%d")
    end_date = datetime.strptime(d2, "%Y-%m-%d")

    # Get the relativedelta between two dates
    delta = relativedelta.relativedelta(end_date, start_date)
    bulan = delta.months
    tahun = delta.years
    total_bulan = (tahun * 12) + bulan
    cursor.execute('CALL getCurrentVaccine(%s, %s);', (id_anak, total_bulan,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Vaccination next
@app.route('/vaccine/next/<int:id_anak>')
@cross_origin()
def get_vaccine_next(id_anak):
    msg = ''
    status = ''
    getMonth = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    getMonth.execute('SELECT dob FROM anak WHERE id = %s;', (id_anak, ))
    # get two dates
    # d1 = str(getMonth)
    d1 = getMonth.fetchone()
    d2 = str(datetime.now(pytz.timezone('Asia/Jakarta')))
    d2 = d2[:10]
    # convert string to date object
    start_date = datetime.strptime(str(d1["dob"]), "%Y-%m-%d")
    end_date = datetime.strptime(d2, "%Y-%m-%d")

    # Get the relativedelta between two dates
    delta = relativedelta.relativedelta(end_date, start_date)
    bulan = delta.months
    tahun = delta.years
    total_bulan = (tahun * 12) + bulan

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM vaksin JOIN vaksin_detail ON vaksin.id = vaksin_detail.id_vaksin WHERE vaksin_detail.bulan_awal > %s  AND vaksin_detail.id NOT IN (SELECT vaksin_detail.id FROM vaksin_not_recommend JOIN vaksin_detail ON vaksin_detail.id = vaksin_not_recommend.id_vaksin_detail WHERE vaksin_not_recommend.id_anak = id_anak)',(total_bulan,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Get Vaccine Detail
@app.route('/vaccine-detail/<int:id_vaksin>/<int:id_vaksin_detail>')
@cross_origin()
def get_vaccine_brand(id_vaksin, id_vaksin_detail):
    msg = ''
    status = ''

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM vaksin_brand JOIN vaksin ON vaksin.id = vaksin_brand.id_vaksin JOIN vaksin_detail ON vaksin_detail.id_vaksin = vaksin.id WHERE vaksin.id = %s AND vaksin_detail.id = %s',(id_vaksin, id_vaksin_detail,))
    data = cursor.fetchall()
    msg = 'Ok'
    status = '200'
    cursor.close()
    
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Edit vaccination
@app.route('/vaccine/<int:id_anak>', methods = ['POST'])
@cross_origin()
def edit_vaccine(id_anak):
    msg = ''
    status = ''

    if request.method == 'POST' and 'tanggal' in request.json and 'tempat' in request.json and 'pemberi' in request.json and 'no_batch' in request.json and 'id_vaksin_detail' in request.json and 'id_vaksin_brand' in request.json :
        tanggal = request.json['tanggal']
        tempat = request.json['tempat']
        pemberi = request.json['pemberi']
        noBatch = request.json['no_batch']
        id_vaksin_detail = request.json['id_vaksin_detail']
        id_vaksin_brand = request.json['id_vaksin_brand']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM history_vaksin WHERE id_anak = %s AND id_vaksin_detail = %s", (id_anak, id_vaksin_detail, ))
        data = cursor.fetchone()
        if data:
            cursor.execute("UPDATE history_vaksin SET tanggal = %s, tempat = %s, pemberi = %s, no_batch = %s, id_vaksin_brand = %s  WHERE id_anak = %s AND id_vaksin_detail = %s", (tanggal, tempat, pemberi, noBatch, id_vaksin_brand, id_anak, id_vaksin_detail, ))
            mysql.connection.commit()
            msg = 'Data berhasil diubah'
            status = '200'
        else:
            cursor.execute("INSERT INTO history_vaksin (tanggal, tempat, pemberi, no_batch, id_anak, id_vaksin_detail, id_vaksin_brand) VALUES (% s, % s, %s, %s, %s, %s, %s)", (tanggal, tempat, pemberi, noBatch, id_anak, id_vaksin_detail, id_vaksin_brand, ))
            mysql.connection.commit()
            msg = 'Data Berhasil ditambahkan'
            status = '200'
        mysql.connection.commit()
        msg = 'Data Berhasil ditambahkan'
        status = '200'
    elif request.method == 'POST':
        msg = 'Tolong isi data terlebih dahulu'
        status = '400'
    
    return jsonify({'status_code': status, 'message': msg})

## GET Edit vaccination
@app.route('/get-vaccine/<int:id_anak>/<int:id_history>')
@cross_origin()
def get_edit_vaccine(id_anak, id_history):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM history_vaksin JOIN vaksin_brand ON vaksin_brand.id = history_vaksin.id_vaksin_brand JOIN vaksin_detail ON vaksin_detail.id = history_vaksin.id_vaksin_detail JOIN vaksin ON vaksin_detail.id_vaksin = vaksin.id WHERE history_vaksin.id_anak = %s AND history_vaksin.id = %s;", (id_anak, id_history, ))
    data = cursor.fetchone()
    return jsonify({'status_code': status, 'message': msg, 'data': data})

## Not Recommend
@app.route('/vaccine/not', methods = ['POST'])
@cross_origin()
def not_vaccine():
    msg = ''
    status = ''

    if request.method == 'POST' and 'id_anak' in request.json and 'id_vaksin_detail' in request.json:
        id_anak = request.json['id_anak']
        id_vaksin_detail = request.json['id_vaksin_detail']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO vaksin_not_recommend (id_anak, id_vaksin_detail) VALUES (% s, % s)", (id_anak, id_vaksin_detail, ))
        
        mysql.connection.commit()
        msg = 'Data Berhasil ditambahkan'
        status = '200'
    elif request.method == 'POST':
        msg = 'Tolong isi data terlebih dahulu'
        status = '400'
    
    return jsonify({'status_code': status, 'message': msg})

## DELETE Not Recommend
@app.route('/vaccine/not/<int:id_vaksin_not_recommend>', methods = ['DELETE'])
@cross_origin()
def delete_not_vaccine(id_vaksin_not_recommend):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("DELETE FROM vaksin_not_recommend WHERE id = % s", (id_vaksin_not_recommend, ))
    
    mysql.connection.commit()
    msg = 'Data Berhasil dihapus'
    status = '200'
    
    return jsonify({'status_code': status, 'message': msg})

## DELETE History
@app.route('/delete/vaccine/<int:id_history>', methods = ['DELETE'])
@cross_origin()
def delete_hist_vaccine(id_history):
    msg = ''
    status = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("DELETE FROM history_vaksin WHERE id = % s", (id_history, ))
    
    mysql.connection.commit()
    msg = 'Data Berhasil dihapus'
    status = '200'
    
    return jsonify({'status_code': status, 'message': msg})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')