# Global Hotel Management System (GHMS) - Rebuilt Version
# Hotel Name (Default Branch): Mafwbh Inn
# Authors: Ayush Samanta, Sanshubh Kanaujia
# Class XII Section A, DPS Panipat Refinery
# Technology: Python + MySQL (mysql.connector only)

import mysql.connector
from mysql.connector import errorcode

# ==============================================================
# Database Configuration
# ==============================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "global_hotel_system"
}

# ==============================================================
# Safe Input Utilities
# ==============================================================

def safe_input(msg):
    try:
        return input(msg)
    except Exception:
        print("Input error.")
        return ""


def safe_int(msg):
    while True:
        try:
            return int(safe_input(msg))
        except Exception:
            print("Enter a valid integer.")


def safe_float(msg):
    while True:
        try:
            return float(safe_input(msg))
        except Exception:
            print("Enter a valid number.")

# ==============================================================
# Database Engine
# ==============================================================

class Database:
    def __init__(self, config):
        self.config = config

    def connect(self):
        try:
            return mysql.connector.connect(**self.config)
        except mysql.connector.Error as e:
            if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise RuntimeError("Invalid MySQL credentials")
            elif e.errno == errorcode.ER_BAD_DB_ERROR:
                raise RuntimeError("Database does not exist")
            else:
                raise RuntimeError(str(e))

    def execute(self, query, params=None, fetchone=False, fetchall=False, commit=False):
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor(dictionary=True)
            cur.execute(query, params or ())
            result = None
            if fetchone:
                result = cur.fetchone()
            if fetchall:
                result = cur.fetchall()
            if commit:
                conn.commit()
            cur.close()
            conn.close()
            return result
        except Exception as e:
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            raise RuntimeError("Database error: " + str(e))

DB = Database(DB_CONFIG)

# ==============================================================
# Core Schema
# ==============================================================

CORE_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS branches (id INT AUTO_INCREMENT PRIMARY KEY, country VARCHAR(100), city VARCHAR(100), address TEXT, phone VARCHAR(30))",
    "CREATE TABLE IF NOT EXISTS hotels (id INT AUTO_INCREMENT PRIMARY KEY, branch_id INT, name VARCHAR(200), rating FLOAT)",
    "CREATE TABLE IF NOT EXISTS rooms (id INT AUTO_INCREMENT PRIMARY KEY, hotel_id INT, room_number VARCHAR(20), room_type VARCHAR(50), price FLOAT, status VARCHAR(30))",
    "CREATE TABLE IF NOT EXISTS customers (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(200), phone VARCHAR(50), email VARCHAR(100), country VARCHAR(100))",
    "CREATE TABLE IF NOT EXISTS bookings (id INT AUTO_INCREMENT PRIMARY KEY, customer_id INT, room_id INT, check_in DATETIME, check_out DATETIME, status VARCHAR(30), total_amount FLOAT)",
    "CREATE TABLE IF NOT EXISTS employees (id INT AUTO_INCREMENT PRIMARY KEY, hotel_id INT, name VARCHAR(200), role VARCHAR(100), phone VARCHAR(50), email VARCHAR(100), salary FLOAT, status VARCHAR(30))",
    "CREATE TABLE IF NOT EXISTS attendance (id INT AUTO_INCREMENT PRIMARY KEY, employee_id INT, date DATE, clock_in TIME, clock_out TIME)",
    "CREATE TABLE IF NOT EXISTS payroll (id INT AUTO_INCREMENT PRIMARY KEY, employee_id INT, month INT, year INT, paid_amount FLOAT)",
    "CREATE TABLE IF NOT EXISTS services (id INT AUTO_INCREMENT PRIMARY KEY, hotel_id INT, name VARCHAR(200), price FLOAT)",
    "CREATE TABLE IF NOT EXISTS inventory (id INT AUTO_INCREMENT PRIMARY KEY, hotel_id INT, item VARCHAR(200), quantity INT)",
    "CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) UNIQUE, password VARCHAR(50), role VARCHAR(50))",
    "CREATE TABLE IF NOT EXISTS invoices (id INT AUTO_INCREMENT PRIMARY KEY, booking_id INT, amount FLOAT, paid FLOAT, status VARCHAR(20))",
    "CREATE TABLE IF NOT EXISTS shifts (id INT AUTO_INCREMENT PRIMARY KEY, employee_id INT, work_date DATE, start_time TIME, end_time TIME)",
    "CREATE TABLE IF NOT EXISTS taxes (id INT AUTO_INCREMENT PRIMARY KEY, country VARCHAR(100), rate FLOAT)",
    "CREATE TABLE IF NOT EXISTS currencies (id INT AUTO_INCREMENT PRIMARY KEY, code VARCHAR(10), rate_to_usd FLOAT)",
    "CREATE TABLE IF NOT EXISTS cancellations (id INT AUTO_INCREMENT PRIMARY KEY, booking_id INT, reason TEXT, refund_amount FLOAT)",
    "CREATE TABLE IF NOT EXISTS audit_logs (id INT AUTO_INCREMENT PRIMARY KEY, action VARCHAR(200), user VARCHAR(50), log_time DATETIME DEFAULT NOW())"
]

# ==============================================================
# Initialization
# ==============================================================

def initialize_database():
    try:
        base = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'])
        cur = base.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS " + DB_CONFIG['database'])
        base.commit()
        cur.close()
        base.close()

        for stmt in CORE_SCHEMA:
            DB.execute(stmt, commit=True)

        DB.execute("INSERT IGNORE INTO users (username,password,role) VALUES ('admin','admin','administrator')", commit=True)
        print("Database initialized.")
    except Exception as e:
        print("Initialization failed:", e)

# ==============================================================
# Authentication
# ==============================================================

current_user = None


def login():
    global current_user
    try:
        u = safe_input("Username: ")
        p = safe_input("Password: ")
        user = DB.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p), fetchone=True)
        if user:
            current_user = user
            log_action("Login")
            return True
        else:
            print("Invalid credentials")
            return False
    except Exception as e:
        print("Login error:", e)
        return False


def logout():
    global current_user
    if current_user:
        log_action("Logout")
    current_user = None


def add_user():
    try:
        u = safe_input("Username: ")
        p = safe_input("Password: ")
        r = safe_input("Role: ")
        DB.execute("INSERT INTO users VALUES (NULL,%s,%s,%s)", (u, p, r), commit=True)
        print("User created.")
    except Exception as e:
        print("User creation error:", e)


def list_users():
    rows = DB.execute("SELECT id,username,role FROM users", fetchall=True)
    for r in rows or []:
        print(r['id'], r['username'], r['role'])


def auth_menu():
    while True:
        print("\nUser Management")
        print("1. Add User")
        print("2. List Users")
        print("3. Back")
        c = safe_input("Choice: ")
        if c == '1': add_user()
        elif c == '2': list_users()
        elif c == '3': break

# ==============================================================
# Audit Logs
# ==============================================================

def log_action(action):
    try:
        user = current_user['username'] if current_user else 'system'
        DB.execute("INSERT INTO audit_logs (action,user) VALUES (%s,%s)", (action, user), commit=True)
    except Exception:
        pass


def list_audit_logs():
    rows = DB.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50", fetchall=True)
    for r in rows or []:
        print(r['log_time'], r['user'], r['action'])

# ==============================================================
# Branch, Hotel, Room, Customer (CRUD)
# ==============================================================

def add_branch():
    DB.execute("INSERT INTO branches VALUES (NULL,%s,%s,%s,%s)", (safe_input("Country: "), safe_input("City: "), safe_input("Address: "), safe_input("Phone: ")), commit=True)


def list_branches():
    for r in DB.execute("SELECT * FROM branches", fetchall=True) or []:
        print(r['id'], r['country'], r['city'])


def add_hotel():
    list_branches()
    DB.execute("INSERT INTO hotels VALUES (NULL,%s,%s,%s)", (safe_int("Branch ID: "), safe_input("Name: "), safe_float("Rating: ")), commit=True)


def list_hotels():
    for r in DB.execute("SELECT * FROM hotels", fetchall=True) or []:
        print(r['id'], r['name'], r['rating'])


def add_room():
    list_hotels()
    DB.execute("INSERT INTO rooms VALUES (NULL,%s,%s,%s,%s,'available')", (safe_int("Hotel ID: "), safe_input("Room No: "), safe_input("Type: "), safe_float("Price: ")), commit=True)


def list_rooms():
    for r in DB.execute("SELECT * FROM rooms", fetchall=True) or []:
        print(r['id'], r['room_number'], r['room_type'], r['price'], r['status'])


def add_customer():
    DB.execute("INSERT INTO customers VALUES (NULL,%s,%s,%s,%s)", (safe_input("Name: "), safe_input("Phone: "), safe_input("Email: "), safe_input("Country: ")), commit=True)


def list_customers():
    for r in DB.execute("SELECT * FROM customers", fetchall=True) or []:
        print(r['id'], r['name'], r['phone'])

# ==============================================================
# Booking Engine
# ==============================================================

def create_booking():
    list_customers()
    cid = safe_int("Customer ID: ")
    rows = DB.execute("SELECT * FROM rooms WHERE status='available'", fetchall=True)
    for r in rows or []:
        print(r['id'], r['room_number'], r['price'])
    rid = safe_int("Room ID: ")
    DB.execute("INSERT INTO bookings VALUES (NULL,%s,%s,NOW(),NULL,'reserved',0)", (cid, rid), commit=True)
    DB.execute("UPDATE rooms SET status='reserved' WHERE id=%s", (rid,), commit=True)
    log_action("Booking created")


def list_bookings():
    for r in DB.execute("SELECT * FROM bookings", fetchall=True) or []:
        print(r['id'], r['customer_id'], r['room_id'], r['status'], r['total_amount'])


def check_in():
    list_bookings()
    bid = safe_int("Booking ID: ")
    DB.execute("UPDATE bookings SET status='checked_in', check_in=NOW() WHERE id=%s", (bid,), commit=True)
    log_action("Check-in")


def check_out():
    list_bookings()
    bid = safe_int("Booking ID: ")
    booking = DB.execute("SELECT * FROM bookings WHERE id=%s", (bid,), fetchone=True)
    room = DB.execute("SELECT * FROM rooms WHERE id=%s", (booking['room_id'],), fetchone=True)
    total = float(room['price'])
    DB.execute("UPDATE bookings SET status='checked_out', check_out=NOW(), total_amount=%s WHERE id=%s", (total, bid), commit=True)
    DB.execute("UPDATE rooms SET status='available' WHERE id=%s", (room['id'],), commit=True)
    log_action("Check-out")

# ==============================================================
# Employee, Attendance, Payroll
# ==============================================================

def add_employee():
    list_hotels()
    DB.execute("INSERT INTO employees VALUES (NULL,%s,%s,%s,%s,%s,%s,'active')", (safe_int("Hotel ID: "), safe_input("Name: "), safe_input("Role: "), safe_input("Phone: "), safe_input("Email: "), safe_float("Salary: ")), commit=True)


def list_employees():
    for r in DB.execute("SELECT * FROM employees", fetchall=True) or []:
        print(r['id'], r['name'], r['role'], r['salary'])


def mark_attendance():
    list_employees()
    eid = safe_int("Employee ID: ")
    DB.execute("INSERT INTO attendance VALUES (NULL,%s,CURDATE(),CURTIME(),NULL)", (eid,), commit=True)


def mark_departure():
    eid = safe_int("Employee ID: ")
    DB.execute("UPDATE attendance SET clock_out=CURTIME() WHERE employee_id=%s AND date=CURDATE()", (eid,), commit=True)


def generate_payroll():
    m = safe_int("Month: ")
    y = safe_int("Year: ")
    for r in DB.execute("SELECT * FROM employees WHERE status='active'", fetchall=True) or []:
        DB.execute("INSERT INTO payroll VALUES (NULL,%s,%s,%s,%s)", (r['id'], m, y, r['salary']), commit=True)


def list_payroll():
    for r in DB.execute("SELECT * FROM payroll", fetchall=True) or []:
        print(r['employee_id'], r['month'], r['year'], r['paid_amount'])

# ==============================================================
# Services & Inventory
# ==============================================================

def add_service():
    list_hotels()
    DB.execute("INSERT INTO services VALUES (NULL,%s,%s,%s)", (safe_int("Hotel ID: "), safe_input("Service: "), safe_float("Price: ")), commit=True)


def list_services():
    for r in DB.execute("SELECT * FROM services", fetchall=True) or []:
        print(r['hotel_id'], r['name'], r['price'])


def add_inventory():
    list_hotels()
    DB.execute("INSERT INTO inventory VALUES (NULL,%s,%s,%s)", (safe_int("Hotel ID: "), safe_input("Item: "), safe_int("Qty: ")), commit=True)


def list_inventory():
    for r in DB.execute("SELECT * FROM inventory", fetchall=True) or []:
        print(r['hotel_id'], r['item'], r['quantity'])

# ==============================================================
# Finance
# ==============================================================

def create_invoice():
    list_bookings()
    bid = safe_int("Booking ID: ")
    booking = DB.execute("SELECT * FROM bookings WHERE id=%s", (bid,), fetchone=True)
    DB.execute("INSERT INTO invoices VALUES (NULL,%s,%s,0,'unpaid')", (bid, booking['total_amount']), commit=True)


def list_invoices():
    for r in DB.execute("SELECT * FROM invoices", fetchall=True) or []:
        print(r['id'], r['booking_id'], r['amount'], r['paid'], r['status'])


def pay_invoice():
    list_invoices()
    iid = safe_int("Invoice ID: ")
    amt = safe_float("Pay amount: ")
    inv = DB.execute("SELECT * FROM invoices WHERE id=%s", (iid,), fetchone=True)
    new_paid = inv['paid'] + amt
    status = 'paid' if new_paid >= inv['amount'] else 'partial'
    DB.execute("UPDATE invoices SET paid=%s,status=%s WHERE id=%s", (new_paid, status, iid), commit=True)

# ==============================================================
# Shifts, Taxes, Currency, Cancellation
# ==============================================================

def add_shift():
    list_employees()
    DB.execute("INSERT INTO shifts VALUES (NULL,%s,%s,%s,%s)", (safe_int("Employee ID: "), safe_input("Date: "), safe_input("Start: "), safe_input("End: ")), commit=True)


def list_shifts():
    for r in DB.execute("SELECT * FROM shifts", fetchall=True) or []:
        print(r['employee_id'], r['work_date'], r['start_time'], r['end_time'])


def add_tax():
    DB.execute("INSERT INTO taxes VALUES (NULL,%s,%s)", (safe_input("Country: "), safe_float("Rate: ")), commit=True)


def list_taxes():
    for r in DB.execute("SELECT * FROM taxes", fetchall=True) or []:
        print(r['country'], r['rate'])


def add_currency():
    DB.execute("INSERT INTO currencies VALUES (NULL,%s,%s)", (safe_input("Code: "), safe_float("Rate to USD: ")), commit=True)


def list_currencies():
    for r in DB.execute("SELECT * FROM currencies", fetchall=True) or []:
        print(r['code'], r['rate_to_usd'])


def cancel_booking():
    list_bookings()
    bid = safe_int("Booking ID: ")
    reason = safe_input("Reason: ")
    booking = DB.execute("SELECT * FROM bookings WHERE id=%s", (bid,), fetchone=True)
    refund = booking['total_amount'] * 0.8
    DB.execute("INSERT INTO cancellations VALUES (NULL,%s,%s,%s)", (bid, reason, refund), commit=True)
    DB.execute("UPDATE bookings SET status='cancelled' WHERE id=%s", (bid,), commit=True)

# ==============================================================
# Reports
# ==============================================================

def report_revenue():
    rows = DB.execute("SELECT SUM(total_amount) AS revenue FROM bookings WHERE status='checked_out'", fetchone=True)
    print("Total revenue:", rows['revenue'])


def report_occupancy():
    total = DB.execute("SELECT COUNT(*) AS c FROM rooms", fetchone=True)['c']
    occ = DB.execute("SELECT COUNT(*) AS c FROM rooms WHERE status!='available'", fetchone=True)['c']
    print("Occupancy:", (occ / total * 100) if total else 0)

# ==============================================================
# Menus
# ==============================================================

def booking_menu():
    while True:
        print("1.Create 2.List 3.CheckIn 4.CheckOut 5.Back")
        c = safe_input("Choice: ")
        if c == '1': create_booking()
        elif c == '2': list_bookings()
        elif c == '3': check_in()
        elif c == '4': check_out()
        elif c == '5': break


def employee_menu():
    while True:
        print("1.Add 2.List 3.In 4.Out 5.PayrollGen 6.PayrollList 7.Back")
        c = safe_input("Choice: ")
        if c == '1': add_employee()
        elif c == '2': list_employees()
        elif c == '3': mark_attendance()
        elif c == '4': mark_departure()
        elif c == '5': generate_payroll()
        elif c == '6': list_payroll()
        elif c == '7': break


def service_menu():
    while True:
        print("1.Add 2.List 3.Back")
        c = safe_input("Choice: ")
        if c == '1': add_service()
        elif c == '2': list_services()
        elif c == '3': break


def inventory_menu():
    while True:
        print("1.Add 2.List 3.Back")
        c = safe_input("Choice: ")
        if c == '1': add_inventory()
        elif c == '2': list_inventory()
        elif c == '3': break


def finance_menu():
    while True:
        print("1.CreateInvoice 2.List 3.Pay 4.Back")
        c = safe_input("Choice: ")
        if c == '1': create_invoice()
        elif c == '2': list_invoices()
        elif c == '3': pay_invoice()
        elif c == '4': break


def shift_menu():
    while True:
        print("1.Add 2.List 3.Back")
        c = safe_input("Choice: ")
        if c == '1': add_shift()
        elif c == '2': list_shifts()
        elif c == '3': break


def tax_menu():
    while True:
        print("1.AddTax 2.ListTax 3.AddCurrency 4.ListCurrency 5.Back")
        c = safe_input("Choice: ")
        if c == '1': add_tax()
        elif c == '2': list_taxes()
        elif c == '3': add_currency()
        elif c == '4': list_currencies()
        elif c == '5': break


def cancellation_menu():
    while True:
        print("1.Cancel 2.Back")
        c = safe_input("Choice: ")
        if c == '1': cancel_booking()
        elif c == '2': break


def report_menu():
    while True:
        print("1.Revenue 2.Occupancy 3.Back")
        c = safe_input("Choice: ")
        if c == '1': report_revenue()
        elif c == '2': report_occupancy()
        elif c == '3': break

# ==============================================================
# Main Menu
# ==============================================================

def main_menu():
    initialize_database()
    while True:
        if not current_user:
            if not login():
                continue
        print("\nGHMS Main Menu")
        print("1.Branch 2.Hotel 3.Room 4.Customer 5.Booking 6.Employee 7.Services 8.Inventory 9.Finance 10.Shift 11.Tax 12.Cancel 13.Reports 14.Users 15.Audit 16.Logout 17.Exit")
        c = safe_input("Choice: ")
        if c == '1': add_branch()
        elif c == '2': add_hotel()
        elif c == '3': add_room()
        elif c == '4': add_customer()
        elif c == '5': booking_menu()
        elif c == '6': employee_menu()
        elif c == '7': service_menu()
        elif c == '8': inventory_menu()
        elif c == '9': finance_menu()
        elif c == '10': shift_menu()
        elif c == '11': tax_menu()
        elif c == '12': cancellation_menu()
        elif c == '13': report_menu()
        elif c == '14': auth_menu()
        elif c == '15': list_audit_logs()
        elif c == '16': logout()
        elif c == '17': break

if __name__ == '__main__':
    main_menu()
