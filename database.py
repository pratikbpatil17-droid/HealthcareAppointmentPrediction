import sqlite3
from werkzeug.security import generate_password_hash


DB_NAME = "healthcare.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    conn = sqlite3.connect(DB_NAME)

    # Allows us to access columns by name
    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    conn = get_connection()

    cursor = conn.cursor()


    # ========================================================
    # USERS TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            user_id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password_hash TEXT NOT NULL,

            role TEXT NOT NULL

        )
    """)


    # ========================================================
    # PATIENTS TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (

            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            age INTEGER NOT NULL,

            gender TEXT NOT NULL,

            phone TEXT NOT NULL

        )
    """)


    # ========================================================
    # DOCTORS TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (

            doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            specialization TEXT NOT NULL,

            department TEXT NOT NULL

        )
    """)


    # ========================================================
    # APPOINTMENTS TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (

            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER NOT NULL,

            doctor_id INTEGER NOT NULL,

            appointment_date TEXT NOT NULL,

            appointment_time TEXT NOT NULL,

            status TEXT DEFAULT 'Scheduled',

            FOREIGN KEY (patient_id)
                REFERENCES patients(patient_id),

            FOREIGN KEY (doctor_id)
                REFERENCES doctors(doctor_id)

        )
    """)


    # ========================================================
    # APPOINTMENT FEATURES TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointment_features (

            feature_id INTEGER PRIMARY KEY AUTOINCREMENT,

            appointment_id INTEGER NOT NULL,

            reminder_sent INTEGER DEFAULT 0,

            previous_no_shows INTEGER DEFAULT 0,

            waiting_days INTEGER DEFAULT 0,

            FOREIGN KEY (appointment_id)
                REFERENCES appointments(appointment_id)

        )
    """)


    # ========================================================
    # PREDICTIONS TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (

            prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,

            appointment_id INTEGER NOT NULL,

            no_show_probability REAL,

            risk_level TEXT,

            FOREIGN KEY (appointment_id)
                REFERENCES appointments(appointment_id)

        )
    """)


    # ========================================================
    # CREATE DEFAULT ADMIN USER
    # ========================================================

    cursor.execute("""
        SELECT *
        FROM users
        WHERE username = ?
    """, ("admin",))


    existing_user = cursor.fetchone()


    if existing_user is None:

        password_hash = generate_password_hash("admin123")


        cursor.execute("""
            INSERT INTO users
            (
                username,
                password_hash,
                role
            )
            VALUES (?, ?, ?)
        """, (
            "admin",
            password_hash,
            "Admin"
        ))


    # Save changes
    conn.commit()

    # Close database
    conn.close()


# ============================================================
# TEST DATABASE
# ============================================================

if __name__ == "__main__":

    init_db()

    print("--------------------------------")
    print("Database created successfully!")
    print("--------------------------------")
    print("Database: healthcare.db")
    print("Username: admin")
    print("Password: admin123")
    print("--------------------------------")