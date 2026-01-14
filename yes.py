
# ================================================================
# Railway Management System
# Created by Ayush Samanta and Sanshubh Kanaujia of XII A
# Delhi Public School, Panipat Refinery
#
# Only dependency: mysql.connector
# ================================================================

import mysql.connector as myc

# ---------------------- DATABASE CONFIG ------------------------

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "student",
    "database": "railway_ticketing_software"
}

# ---------------------- DB UTILITIES ---------------------------

def get_connection():
    return myc.connect(**DB_CONFIG)

def init_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_info(
        user_id INT PRIMARY KEY,
        user_name VARCHAR(50),
        user_age INT,
        user_gender VARCHAR(1),
        user_mobile_no VARCHAR(15),
        password VARCHAR(10),
        role VARCHAR(10)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS trains_info(
        train_id INT PRIMARY KEY,
        train_name VARCHAR(100),
        source VARCHAR(50),
        destination VARCHAR(50),
        interstations TEXT,
        fare TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS booking_info(
        booking_id INT PRIMARY KEY,
        train_id INT,
        user_id INT,
        date_of_journey DATE,
        fare INT,
        source VARCHAR(50),
        destination VARCHAR(50),
        status VARCHAR(20)
    )
    """)

    conn.commit()
    conn.close()

# ---------------------- VALIDATION ------------------------------

def input_int(prompt, length=None):
    while True:
        v = input(prompt).strip()
        if not v.isdigit():
            print("Only numeric input allowed.")
            continue
        if length and len(v) != length:
            print(f"Input must be exactly {length} digits.")
            continue
        return int(v)

def input_alpha(prompt):
    while True:
        v = input(prompt).strip()
        if not v.replace("_", "").isalpha():
            print("Only alphabets or underscore allowed.")
            continue
        return v

def input_gender(prompt):
    while True:
        v = input(prompt).strip().lower()
        if v not in ["m", "f"]:
            print("Enter m or f only.")
            continue
        return v

# ---------------------- USER MANAGEMENT -------------------------

def register_user():
    conn = get_connection()
    cur = conn.cursor()

    user_id = input_int("User ID (6 digits): ", 6)
    user_name = input_alpha("User Name (use _ instead of space): ")
    user_age = input_int("Age: ")
    user_gender = input_gender("Gender (m/f): ")
    user_mobile = input_int("Mobile No (10 digits): ", 10)
    password = input_int("Password (4 digits): ", 4)

    cur.execute("SELECT * FROM user_info WHERE user_id=%s", (user_id,))
    if cur.fetchone():
        print("User already exists.")
        conn.close()
        return

    cur.execute("""
        INSERT INTO user_info VALUES(%s,%s,%s,%s,%s,%s,%s)
    """, (user_id, user_name, user_age, user_gender, str(user_mobile), str(password), "user"))

    conn.commit()
    conn.close()
    print("User registered successfully.")

def login_user():
    user_id = input_int("User ID: ")
    password = input("Password: ").strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_info WHERE user_id=%s AND password=%s", (user_id, password))
    user = cur.fetchone()
    conn.close()

    if not user:
        print("Invalid credentials.")
        return None

    return user

# ---------------------- TRAIN MANAGEMENT ------------------------

def add_train():
    conn = get_connection()
    cur = conn.cursor()

    train_id = input_int("Train ID (5 digits): ", 5)
    train_name = input_alpha("Train Name: ")
    source = input_alpha("Source: ")
    destination = input_alpha("Destination: ")
    interstations = input("Interstations (comma separated): ")
    fare = input("Fare segments (comma separated): ")

    cur.execute("SELECT * FROM trains_info WHERE train_id=%s", (train_id,))
    if cur.fetchone():
        print("Train already exists.")
        conn.close()
        return

    cur.execute("""
        INSERT INTO trains_info VALUES(%s,%s,%s,%s,%s,%s)
    """, (train_id, train_name, source, destination, interstations, fare))

    conn.commit()
    conn.close()
    print("Train added successfully.")

def list_trains():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trains_info")
    rows = cur.fetchall()
    conn.close()

    print("\n--- TRAINS LIST ---")
    for r in rows:
        print(r)

# ---------------------- BOOKING -------------------------------

def next_booking_id(cur):
    cur.execute("SELECT MAX(booking_id) FROM booking_info")
    r = cur.fetchone()[0]
    return 1 if r is None else r + 1

def book_ticket(user):
    conn = get_connection()
    cur = conn.cursor()

    list_trains()
    train_id = input_int("Enter Train ID: ")

    cur.execute("SELECT * FROM trains_info WHERE train_id=%s", (train_id,))
    train = cur.fetchone()
    if not train:
        print("Invalid train.")
        conn.close()
        return

    date = input("Date of journey (YYYY-MM-DD): ")
    fare_total = sum(int(x) for x in train[5].split(",") if x.strip().isdigit())

    booking_id = next_booking_id(cur)

    cur.execute("""
        INSERT INTO booking_info VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
    """, (booking_id, train_id, user[0], date, fare_total, train[2], train[3], "active"))

    conn.commit()
    conn.close()

    print("Ticket booked successfully.")
    print("Booking ID:", booking_id)

def view_bookings(user):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM booking_info WHERE user_id=%s", (user[0],))
    rows = cur.fetchall()
    conn.close()

    print("\n--- YOUR BOOKINGS ---")
    for r in rows:
        print(r)

# ---------------------- ADMIN PANEL ----------------------------

def admin_panel():
    while True:
        print("\nADMIN PANEL")
        print("1. Add Train")
        print("2. List Trains")
        print("3. Exit")

        ch = input("Choice: ").strip()
        if ch == "1":
            add_train()
        elif ch == "2":
            list_trains()
        elif ch == "3":
            break
        else:
            print("Invalid choice.")

# ---------------------- USER PANEL -----------------------------

def user_panel(user):
    while True:
        print("\nUSER PANEL")
        print("1. Book Ticket")
        print("2. View My Bookings")
        print("3. Exit")

        ch = input("Choice: ").strip()
        if ch == "1":
            book_ticket(user)
        elif ch == "2":
            view_bookings(user)
        elif ch == "3":
            break
        else:
            print("Invalid choice.")

# ---------------------- MAIN MENU ------------------------------

def main_menu():
    init_database()

    while True:
        print("\n==============================================")
        print(" Railway Management System")
        print(" Delhi Public School, Panipat Refinery")
        print(" Created by Ayush Samanta & Sanshubh Kanaujia (XII A)")
        print("==============================================")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        ch = input("Choice: ").strip()

        if ch == "1":
            register_user()
        elif ch == "2":
            user = login_user()
            if user:
                if user[6] == "admin":
                    admin_panel()
                else:
                    user_panel(user)
        elif ch == "3":
            print("Exiting system.")
            break
        else:
            print("Invalid choice.")

# ---------------------- ENTRY POINT ----------------------------

if __name__ == "__main__":
    main_menu()
