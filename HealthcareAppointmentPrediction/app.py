from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

from database import get_connection, init_db
from model import predict_no_show


app = Flask(__name__)

# Secret key for login sessions
app.secret_key = "healthcare_secret_key_123"


# Initialize database when application starts
init_db()


# ============================================================
# LOGIN
# ============================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        flash("Invalid username or password")

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()

    patients = conn.execute(
        "SELECT COUNT(*) AS count FROM patients"
    ).fetchone()["count"]

    doctors = conn.execute(
        "SELECT COUNT(*) AS count FROM doctors"
    ).fetchone()["count"]

    appointments = conn.execute(
        "SELECT COUNT(*) AS count FROM appointments"
    ).fetchone()["count"]

    no_shows = conn.execute(
        "SELECT COUNT(*) AS count FROM appointments "
        "WHERE status = 'No Show'"
    ).fetchone()["count"]

    recent = conn.execute("""
        SELECT
            appointments.*,
            patients.name AS patient_name,
            doctors.name AS doctor_name
        FROM appointments
        JOIN patients
            ON appointments.patient_id = patients.patient_id
        JOIN doctors
            ON appointments.doctor_id = doctors.doctor_id
        ORDER BY appointment_id DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        patients=patients,
        doctors=doctors,
        appointments=appointments,
        no_shows=no_shows,
        recent=recent
    )


# ============================================================
# PATIENTS
# ============================================================

@app.route("/patients", methods=["GET", "POST"])
def patients():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()

    if request.method == "POST":

        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        phone = request.form.get("phone")

        conn.execute("""
            INSERT INTO patients
            (name, age, gender, phone)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            age,
            gender,
            phone
        ))

        conn.commit()

        flash("Patient added successfully")

    patient_list = conn.execute("""
        SELECT *
        FROM patients
        ORDER BY patient_id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "patients.html",
        patients=patient_list
    )


# ============================================================
# DOCTORS
# ============================================================

@app.route("/doctors", methods=["GET", "POST"])
def doctors():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()

    if request.method == "POST":

        name = request.form.get("name")
        specialization = request.form.get("specialization")
        department = request.form.get("department")

        conn.execute("""
            INSERT INTO doctors
            (name, specialization, department)
            VALUES (?, ?, ?)
        """, (
            name,
            specialization,
            department
        ))

        conn.commit()

        flash("Doctor added successfully")

    doctor_list = conn.execute("""
        SELECT *
        FROM doctors
        ORDER BY doctor_id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "doctors.html",
        doctors=doctor_list
    )


# ============================================================
# APPOINTMENTS
# ============================================================

@app.route("/appointments", methods=["GET", "POST"])
def appointments():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()

    if request.method == "POST":

        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")
        appointment_date = request.form.get("appointment_date")
        appointment_time = request.form.get("appointment_time")

        cursor = conn.execute("""
            INSERT INTO appointments
            (
                patient_id,
                doctor_id,
                appointment_date,
                appointment_time,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            patient_id,
            doctor_id,
            appointment_date,
            appointment_time,
            "Scheduled"
        ))

        appointment_id = cursor.lastrowid

        reminder_sent = int(
            request.form.get("reminder_sent", 0)
        )

        previous_no_shows = int(
            request.form.get("previous_no_shows", 0)
        )

        waiting_days = int(
            request.form.get("waiting_days", 0)
        )

        conn.execute("""
            INSERT INTO appointment_features
            (
                appointment_id,
                reminder_sent,
                previous_no_shows,
                waiting_days
            )
            VALUES (?, ?, ?, ?)
        """, (
            appointment_id,
            reminder_sent,
            previous_no_shows,
            waiting_days
        ))

        conn.commit()

        flash("Appointment booked successfully")

    patient_list = conn.execute("""
        SELECT *
        FROM patients
        ORDER BY name
    """).fetchall()

    doctor_list = conn.execute("""
        SELECT *
        FROM doctors
        ORDER BY name
    """).fetchall()

    appointment_list = conn.execute("""
        SELECT
            appointments.*,
            patients.name AS patient_name,
            doctors.name AS doctor_name
        FROM appointments
        JOIN patients
            ON appointments.patient_id = patients.patient_id
        JOIN doctors
            ON appointments.doctor_id = doctors.doctor_id
        ORDER BY appointment_id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "appointments.html",
        patients=patient_list,
        doctors=doctor_list,
        appointments=appointment_list
    )


# ============================================================
# NO-SHOW PREDICTION
# ============================================================

@app.route("/prediction", methods=["GET", "POST"])
def prediction():

    if "user_id" not in session:
        return redirect(url_for("login"))

    result = None

    if request.method == "POST":

        appointment_id = request.form.get("appointment_id")

        reminder_sent = int(
            request.form.get("reminder_sent", 0)
        )

        previous_no_shows = int(
            request.form.get("previous_no_shows", 0)
        )

        waiting_days = int(
            request.form.get("waiting_days", 0)
        )

        probability, risk = predict_no_show(
            reminder_sent,
            previous_no_shows,
            waiting_days
        )

        conn = get_connection()

        conn.execute("""
            INSERT INTO predictions
            (
                appointment_id,
                no_show_probability,
                risk_level
            )
            VALUES (?, ?, ?)
        """, (
            appointment_id,
            probability,
            risk
        ))

        conn.commit()
        conn.close()

        result = {
            "probability": probability,
            "risk": risk
        }

    conn = get_connection()

    appointment_list = conn.execute("""
        SELECT
            appointments.appointment_id,
            patients.name AS patient_name,
            doctors.name AS doctor_name
        FROM appointments
        JOIN patients
            ON appointments.patient_id = patients.patient_id
        JOIN doctors
            ON appointments.doctor_id = doctors.doctor_id
        ORDER BY appointments.appointment_id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "prediction.html",
        appointments=appointment_list,
        result=result
    )


# ============================================================
# HOME / HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return "Healthcare Appointment Prediction System is Running!"


# ============================================================
# ERROR HANDLING
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested page does not exist.</p>
    """, 404


@app.errorhandler(500)
def internal_error(error):

    return """
    <h1>500 - Internal Server Error</h1>
    <p>Something went wrong on the server.</p>
    """, 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("--------------------------------------------")
    print("Healthcare Appointment Prediction System")
    print("--------------------------------------------")
    print("Server: http://127.0.0.1:5000")
    print("Login: admin")
    print("Password: admin123")
    print("--------------------------------------------")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )