import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename


APP_NAME = "MediCobao"


def get_db_connection():
    # Allow overriding the database location via environment variable for hosting
    db_path = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), 'medicobao.db'))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Tabla de alumnos
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            matricula TEXT PRIMARY KEY,
            nombres TEXT,
            apellido_paterno TEXT,
            apellido_materno TEXT,
            semestre TEXT,
            grupo TEXT,
            foto_path TEXT
        );
        """
    )
    # Datos médicos
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS medical (
            matricula TEXT UNIQUE,
            tipo_sangre TEXT,
            alergias TEXT,
            padecimientos TEXT,
            vacunas_aplicadas TEXT,
            num_seguro_social TEXT,
            FOREIGN KEY(matricula) REFERENCES students(matricula) ON DELETE CASCADE
        );
        """
    )
    # Datos del tutor
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tutor (
            matricula TEXT UNIQUE,
            nombre_tutor TEXT,
            ap_paterno_tutor TEXT,
            ap_materno_tutor TEXT,
            domicilio TEXT,
            telefono TEXT,
            FOREIGN KEY(matricula) REFERENCES students(matricula) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'medicobao-secret-key')

# Configure upload storage and public URL path; defaults work locally.
BASE_DIR = os.path.dirname(__file__)
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'static', 'uploads'))
UPLOAD_URL_PATH = os.getenv('UPLOAD_URL_PATH', '/static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
init_db()


@app.route('/healthz')
def healthz():
    return ('ok', 200)

@app.route('/')
def home():
    return render_template('home.html', app_name=APP_NAME)


@app.route('/acceso', methods=['GET', 'POST'])
def acceso():
    if request.method == 'POST':
        matricula = request.form.get('matricula', '').strip()
        rol = request.form.get('rol', '').strip()
        if not matricula or not rol:
            flash('Ingresa la matrícula y selecciona un rol.')
            return redirect(url_for('acceso'))
        if rol == 'tutor':
            return redirect(url_for('tutor_view', matricula=matricula))
        if rol == 'medico':
            return redirect(url_for('medico_view', matricula=matricula))
        if rol == 'admin':
            return redirect(url_for('admin', q=matricula))
        flash('Rol inválido.')
        return redirect(url_for('acceso'))
    return render_template('acceso.html', app_name=APP_NAME)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Datos personales
        matricula = request.form.get('matricula', '').strip()
        nombres = request.form.get('nombres', '').strip()
        ap_paterno = request.form.get('apellido_paterno', '').strip()
        ap_materno = request.form.get('apellido_materno', '').strip()
        semestre = request.form.get('semestre', '').strip()
        grupo = request.form.get('grupo', '').strip()

        # Foto
        foto = request.files.get('foto')
        foto_path = None
        if foto and foto.filename:
            filename = secure_filename(f"{matricula}_" + foto.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(save_path)
            # Persist paths even if storage is outside /static by using a fixed URL base
            foto_path = f"{UPLOAD_URL_PATH}/{filename}"

        if not matricula:
            flash('La matrícula es obligatoria.')
            return redirect(url_for('registro'))

        conn = get_db_connection()
        cur = conn.cursor()
        # Upsert alumno
        cur.execute(
            """
            INSERT INTO students(matricula, nombres, apellido_paterno, apellido_materno, semestre, grupo, foto_path)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(matricula) DO UPDATE SET
                nombres=excluded.nombres,
                apellido_paterno=excluded.apellido_paterno,
                apellido_materno=excluded.apellido_materno,
                semestre=excluded.semestre,
                grupo=excluded.grupo,
                foto_path=COALESCE(excluded.foto_path, students.foto_path)
            ;
            """,
            (matricula, nombres, ap_paterno, ap_materno, semestre, grupo, foto_path)
        )

        # Datos médicos
        tipo_sangre = request.form.get('tipo_sangre', '').strip()
        alergias = request.form.get('alergias', '').strip()
        padecimientos = request.form.get('padecimientos', '').strip()
        vacunas_aplicadas = request.form.get('vacunas_aplicadas', '').strip()
        num_seguro_social = request.form.get('num_seguro_social', '').strip()

        cur.execute(
            """
            INSERT INTO medical(matricula, tipo_sangre, alergias, padecimientos, vacunas_aplicadas, num_seguro_social)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(matricula) DO UPDATE SET
                tipo_sangre=excluded.tipo_sangre,
                alergias=excluded.alergias,
                padecimientos=excluded.padecimientos,
                vacunas_aplicadas=excluded.vacunas_aplicadas,
                num_seguro_social=excluded.num_seguro_social
            ;
            """,
            (matricula, tipo_sangre, alergias, padecimientos, vacunas_aplicadas, num_seguro_social)
        )

        # Datos del tutor
        nombre_tutor = request.form.get('nombre_tutor', '').strip()
        ap_paterno_tutor = request.form.get('ap_paterno_tutor', '').strip()
        ap_materno_tutor = request.form.get('ap_materno_tutor', '').strip()
        domicilio = request.form.get('domicilio', '').strip()
        telefono = request.form.get('telefono', '').strip()

        cur.execute(
            """
            INSERT INTO tutor(matricula, nombre_tutor, ap_paterno_tutor, ap_materno_tutor, domicilio, telefono)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(matricula) DO UPDATE SET
                nombre_tutor=excluded.nombre_tutor,
                ap_paterno_tutor=excluded.ap_paterno_tutor,
                ap_materno_tutor=excluded.ap_materno_tutor,
                domicilio=excluded.domicilio,
                telefono=excluded.telefono
            ;
            """,
            (matricula, nombre_tutor, ap_paterno_tutor, ap_materno_tutor, domicilio, telefono)
        )

        conn.commit()
        conn.close()

        flash('Registro guardado correctamente.')
        return redirect(url_for('acceso'))

    return render_template('registro.html', app_name=APP_NAME)


def get_full_record(matricula: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE matricula=?", (matricula,))
    alumno = cur.fetchone()
    cur.execute("SELECT * FROM medical WHERE matricula=?", (matricula,))
    medico = cur.fetchone()
    cur.execute("SELECT * FROM tutor WHERE matricula=?", (matricula,))
    tutor_row = cur.fetchone()
    conn.close()
    return alumno, medico, tutor_row


@app.route('/tutor/<matricula>', methods=['GET', 'POST'])
def tutor_view(matricula):
    if request.method == 'POST':
        nombre_tutor = request.form.get('nombre_tutor', '').strip()
        ap_paterno_tutor = request.form.get('ap_paterno_tutor', '').strip()
        ap_materno_tutor = request.form.get('ap_materno_tutor', '').strip()
        domicilio = request.form.get('domicilio', '').strip()
        telefono = request.form.get('telefono', '').strip()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO tutor(matricula, nombre_tutor, ap_paterno_tutor, ap_materno_tutor, domicilio, telefono)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(matricula) DO UPDATE SET
                nombre_tutor=excluded.nombre_tutor,
                ap_paterno_tutor=excluded.ap_paterno_tutor,
                ap_materno_tutor=excluded.ap_materno_tutor,
                domicilio=excluded.domicilio,
                telefono=excluded.telefono
            ;
            """,
            (matricula, nombre_tutor, ap_paterno_tutor, ap_materno_tutor, domicilio, telefono)
        )
        conn.commit()
        conn.close()
        flash('Datos del tutor actualizados.')
        return redirect(url_for('tutor_view', matricula=matricula))

    alumno, medico, tutor_row = get_full_record(matricula)
    return render_template('tutor.html', app_name=APP_NAME, alumno=alumno, tutor=tutor_row)


@app.route('/medico/<matricula>', methods=['GET', 'POST'])
def medico_view(matricula):
    if request.method == 'POST':
        tipo_sangre = request.form.get('tipo_sangre', '').strip()
        alergias = request.form.get('alergias', '').strip()
        padecimientos = request.form.get('padecimientos', '').strip()
        vacunas_aplicadas = request.form.get('vacunas_aplicadas', '').strip()
        num_seguro_social = request.form.get('num_seguro_social', '').strip()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO medical(matricula, tipo_sangre, alergias, padecimientos, vacunas_aplicadas, num_seguro_social)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(matricula) DO UPDATE SET
                tipo_sangre=excluded.tipo_sangre,
                alergias=excluded.alergias,
                padecimientos=excluded.padecimientos,
                vacunas_aplicadas=excluded.vacunas_aplicadas,
                num_seguro_social=excluded.num_seguro_social
            ;
            """,
            (matricula, tipo_sangre, alergias, padecimientos, vacunas_aplicadas, num_seguro_social)
        )
        conn.commit()
        conn.close()
        flash('Datos médicos actualizados.')
        return redirect(url_for('medico_view', matricula=matricula))

    alumno, medico, tutor_row = get_full_record(matricula)
    return render_template('medico.html', app_name=APP_NAME, alumno=alumno, medico=medico)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    q = request.args.get('q', '').strip()
    record = None
    if q:
        record = get_full_record(q)
    return render_template('admin.html', app_name=APP_NAME, q=q, record=record)


@app.route('/admin/eliminar/<matricula>', methods=['POST'])
def eliminar(matricula):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM medical WHERE matricula=?", (matricula,))
    cur.execute("DELETE FROM tutor WHERE matricula=?", (matricula,))
    cur.execute("DELETE FROM students WHERE matricula=?", (matricula,))
    conn.commit()
    conn.close()
    flash('Registro eliminado.')
    return redirect(url_for('admin'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)