
# ================================================================
# Railway Management System - Enterprise Edition
# Created by Ayush Samanta and Sanshubh Kanaujia of XII A
# Delhi Public School, Panipat Refinery
#
# Dependency: mysql.connector ONLY
# ================================================================

import mysql.connector as myc

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "student",
    "database": "railway_ticketing_software"
}

# ======================= DATABASE ===============================

def get_conn():
    return myc.connect(**DB_CONFIG)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS user_info(
        user_id INT PRIMARY KEY,
        user_name VARCHAR(50),
        user_age INT,
        user_gender VARCHAR(1),
        user_mobile_no VARCHAR(15),
        password VARCHAR(10),
        role VARCHAR(10)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS trains_info(
        train_id INT PRIMARY KEY,
        train_name VARCHAR(100),
        source VARCHAR(50),
        destination VARCHAR(50),
        interstations TEXT,
        fare TEXT,
        seats INT,
        status VARCHAR(20)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS booking_info(
        booking_id INT PRIMARY KEY,
        train_id INT,
        user_id INT,
        date_of_journey DATE,
        fare INT,
        source VARCHAR(50),
        destination VARCHAR(50),
        status VARCHAR(20)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS audit_logs(
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        action VARCHAR(255),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()

# ======================= UTILITIES ==============================

def log_action(text):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO audit_logs(action) VALUES(%s)", (text,))
    conn.commit()
    conn.close()

def num_input(msg, length=None):
    while True:
        v = input(msg).strip()
        if not v.isdigit():
            print("Numeric input only.")
            continue
        if length and len(v) != length:
            print(f"Must be {length} digits.")
            continue
        return int(v)

def text_input(msg):
    while True:
        v = input(msg).strip()
        if not v.replace("_","").isalpha():
            print("Alphabet/underscore only.")
            continue
        return v

def gender_input():
    while True:
        g = input("Gender (m/f): ").lower()
        if g in ["m","f"]:
            return g
        print("Invalid gender.")

# ======================= USER SYSTEM ============================

def register_user():
    conn = get_conn()
    c = conn.cursor()

    uid = num_input("User ID (6 digits): ",6)
    uname = text_input("Username: ")
    age = num_input("Age: ")
    gen = gender_input()
    mob = num_input("Mobile (10 digits): ",10)
    pwd = num_input("Password (4 digits): ",4)

    c.execute("SELECT * FROM user_info WHERE user_id=%s",(uid,))
    if c.fetchone():
        print("User exists.")
        conn.close()
        return

    c.execute("INSERT INTO user_info VALUES(%s,%s,%s,%s,%s,%s,%s)",
              (uid,uname,age,gen,str(mob),str(pwd),"user"))
    conn.commit()
    conn.close()
    log_action(f"User registered {uid}")
    print("Registration successful.")

def login():
    uid = num_input("User ID: ")
    pwd = input("Password: ")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM user_info WHERE user_id=%s AND password=%s",(uid,pwd))
    u = c.fetchone()
    conn.close()
    if not u:
        print("Login failed.")
        return None
    log_action(f"Login {uid}")
    return u

# ======================= TRAIN SYSTEM ===========================

def add_train():
    conn = get_conn()
    c = conn.cursor()

    tid = num_input("Train ID (5 digits): ",5)
    name = text_input("Train name: ")
    src = text_input("Source: ")
    dest = text_input("Destination: ")
    inter = input("Interstations (comma separated): ")
    fare = input("Fare segments (comma separated): ")
    seats = num_input("Total seats: ")

    c.execute("SELECT * FROM trains_info WHERE train_id=%s",(tid,))
    if c.fetchone():
        print("Train exists.")
        conn.close()
        return

    c.execute("""INSERT INTO trains_info VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
              (tid,name,src,dest,inter,fare,seats,"active"))
    conn.commit()
    conn.close()
    log_action(f"Train added {tid}")
    print("Train added.")

def list_trains():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM trains_info")
    rows = c.fetchall()
    conn.close()
    print("\n--- TRAINS ---")
    for r in rows:
        print(r)

def disable_train():
    tid = num_input("Train ID: ")
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE trains_info SET status='inactive' WHERE train_id=%s",(tid,))
    conn.commit()
    conn.close()
    log_action(f"Train disabled {tid}")
    print("Train disabled.")

def update_train_name():
    tid = num_input("Train ID: ")
    new = text_input("New name: ")
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE trains_info SET train_name=%s WHERE train_id=%s",(new,tid))
    conn.commit()
    conn.close()
    log_action(f"Train name updated {tid}")
    print("Updated.")

def update_seats():
    tid = num_input("Train ID: ")
    seats = num_input("New seat count: ")
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE trains_info SET seats=%s WHERE train_id=%s",(seats,tid))
    conn.commit()
    conn.close()
    log_action(f"Seats updated {tid}")
    print("Seats updated.")

# ======================= BOOKINGS ===============================

def next_booking_id(c):
    c.execute("SELECT MAX(booking_id) FROM booking_info")
    r = c.fetchone()[0]
    return 1 if r is None else r+1

def book_ticket(user):
    list_trains()
    tid = num_input("Train ID: ")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM trains_info WHERE train_id=%s AND status='active'",(tid,))
    tr = c.fetchone()

    if not tr:
        print("Invalid train.")
        conn.close()
        return

    date = input("Date (YYYY-MM-DD): ")
    fare = sum(int(x) for x in tr[5].split(",") if x.isdigit())

    bid = next_booking_id(c)
    c.execute("""INSERT INTO booking_info VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
              (bid,tid,user[0],date,fare,tr[2],tr[3],"active"))
    conn.commit()
    conn.close()
    log_action(f"Ticket booked {bid}")
    print("Booked. Booking ID:",bid)

def cancel_ticket():
    bid = num_input("Booking ID: ")
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE booking_info SET status='cancelled' WHERE booking_id=%s",(bid,))
    conn.commit()
    conn.close()
    log_action(f"Ticket cancelled {bid}")
    print("Cancelled.")

def view_user_bookings(user):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM booking_info WHERE user_id=%s",(user[0],))
    rows = c.fetchall()
    conn.close()
    for r in rows:
        print(r)

def view_all_bookings():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM booking_info")
    rows = c.fetchall()
    conn.close()
    for r in rows:
        print(r)

# ======================= USER ADMIN TOOLS =======================

def promote_user():
    uid = num_input("User ID: ")
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE user_info SET role='admin' WHERE user_id=%s",(uid,))
    conn.commit()
    conn.close()
    log_action(f"User promoted {uid}")
    print("Promoted to admin.")

def delete_user():
    uid = num_input("User ID: ")
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM user_info WHERE user_id=%s",(uid,))
    conn.commit()
    conn.close()
    log_action(f"User deleted {uid}")
    print("Deleted user.")

def list_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM user_info")
    rows = c.fetchall()
    conn.close()
    for r in rows:
        print(r)

# ======================= REPORTING ==============================

def system_stats():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM user_info")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM trains_info")
    trains = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM booking_info")
    bookings = c.fetchone()[0]
    conn.close()

    print("Users:",users)
    print("Trains:",trains)
    print("Bookings:",bookings)

def view_logs():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    for r in rows:
        print(r)

# ======================= MENUS =================================

def admin_menu():
    while True:
        print("\n--- ADMIN PANEL ---")
        print("1 Add Train")
        print("2 List Trains")
        print("3 Disable Train")
        print("4 Update Train Name")
        print("5 Update Seats")
        print("6 View All Bookings")
        print("7 Cancel Booking")
        print("8 Promote User")
        print("9 Delete User")
        print("10 List Users")
        print("11 System Stats")
        print("12 View Logs")
        print("13 Logout")

        ch = input("Choice: ")
        if ch=="1": add_train()
        elif ch=="2": list_trains()
        elif ch=="3": disable_train()
        elif ch=="4": update_train_name()
        elif ch=="5": update_seats()
        elif ch=="6": view_all_bookings()
        elif ch=="7": cancel_ticket()
        elif ch=="8": promote_user()
        elif ch=="9": delete_user()
        elif ch=="10": list_users()
        elif ch=="11": system_stats()
        elif ch=="12": view_logs()
        elif ch=="13": break
        else: print("Invalid.")

def user_menu(user):
    while True:
        print("\n--- USER PANEL ---")
        print("1 Book Ticket")
        print("2 View My Bookings")
        print("3 Logout")

        ch = input("Choice: ")
        if ch=="1": book_ticket(user)
        elif ch=="2": view_user_bookings(user)
        elif ch=="3": break
        else: print("Invalid.")

# ======================= MAIN ==================================

def main():
    init_db()
    while True:
        print("\nRailway Management System - DPS Panipat Refinery")
        print("Created by Ayush Samanta & Sanshubh Kanaujia (XII A)")
        print("1 Register")
        print("2 Login")
        print("3 Exit")

        ch = input("Choice: ")
        if ch=="1": register_user()
        elif ch=="2":
            u = login()
            if u:
                if u[6]=="admin":
                    admin_menu()
                else:
                    user_menu(u)
        elif ch=="3":
            break
        else:
            print("Invalid.")

if __name__=="__main__":
    main()
