# Hotel Management System (School Final Project)
# Hotel Name: Mafwbh Inn
# Authors: Ayush Samanta, Sanshubh Kanaujia
# Class XII Section A, DPS Panipat Refinery
# Technology: Python 3 + MySQL (mysql.connector only)

import mysql.connector
from mysql.connector import errorcode

# ======================================================
# Database Configuration
# ======================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "mafwbh_inn_db"
}

# ======================================================
# Utility Functions (Safe Input)
# ======================================================

def safe_input(msg):
    try:
        return input(msg)
    except Exception:
        print("Input error")
        return ""


def safe_int(msg):
    while True:
        try:
            return int(safe_input(msg))
        except Exception:
            print("Enter valid integer")


def safe_float(msg):
    while True:
        try:
            return float(safe_input(msg))
        except Exception:
            print("Enter valid number")

# ======================================================
# Database Engine
# ======================================================

class Database:
    def __init__(self, config):
        self.config = config

    def connect(self):
        try:
            return mysql.connector.connect(**self.config)
        except mysql.connector.Error as e:
            if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise RuntimeError("Access denied")
            elif e.errno == errorcode.ER_BAD_DB_ERROR:
                raise RuntimeError("Database not found")
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
            print("Database error:", e)
            return None

DB = Database(DB_CONFIG)

# ======================================================
# Database Schema
# ======================================================

SCHEMA = [
    "CREATE TABLE IF NOT EXISTS rooms (id INT AUTO_INCREMENT PRIMARY KEY, room_no VARCHAR(10), room_type VARCHAR(50), price FLOAT, status VARCHAR(20))",
    "CREATE TABLE IF NOT EXISTS customers (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), phone VARCHAR(30), email VARCHAR(100))",
    "CREATE TABLE IF NOT EXISTS bookings (id INT AUTO_INCREMENT PRIMARY KEY, customer_id INT, room_id INT, check_in DATETIME, check_out DATETIME, status VARCHAR(20), total FLOAT)",
    "CREATE TABLE IF NOT EXISTS employees (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), role VARCHAR(50), phone VARCHAR(30), salary FLOAT, status VARCHAR(20))",
    "CREATE TABLE IF NOT EXISTS attendance (id INT AUTO_INCREMENT PRIMARY KEY, employee_id INT, date DATE, clock_in TIME, clock_out TIME)",
    "CREATE TABLE IF NOT EXISTS payroll (id INT AUTO_INCREMENT PRIMARY KEY, employee_id INT, month INT, year INT, amount FLOAT)",
    "CREATE TABLE IF NOT EXISTS services (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), price FLOAT)",
    "CREATE TABLE IF NOT EXISTS inventory (id INT AUTO_INCREMENT PRIMARY KEY, item VARCHAR(100), quantity INT)",
    "CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50), password VARCHAR(50), role VARCHAR(20) DEFAULT 'admin')"
]

# ======================================================
# Database Initialization
# ======================================================

def initialize_database():
    try:
        base = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'])
        cur = base.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS " + DB_CONFIG['database'])
        base.commit()
        cur.close()
        base.close()

        for stmt in SCHEMA:
            DB.execute(stmt, commit=True)

        # core tables created above; now ensure all auxiliary tables also exist
        init_billing_tables()
        init_service_orders_table()
        init_cancellation_table()
        init_logs_table()
        init_maintenance_table()
        init_inventory_usage_table()
        init_vendor_tables()
        init_tax_table()

        # default admin user
        DB.execute(
            "INSERT IGNORE INTO users (username,password,role) VALUES ('admin','admin','admin')",
            commit=True,
        )
        print("Database initialized")
    except Exception as e:
        print("Initialization error:", e)

# ======================================================
# Authentication System
# ======================================================

current_user = None


def login():
    global current_user
    username = safe_input("Username: ")
    password = safe_input("Password: ")
    user = DB.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password), fetchone=True)
    if user:
        current_user = user
        return True
    print("Invalid credentials")
    return False


def logout():
    global current_user
    current_user = None

# ======================================================
# Room Management
# ======================================================

def add_room():
    room_no = safe_input("Room number: ")
    room_type = safe_input("Room type: ")
    price = safe_float("Price: ")
    DB.execute("INSERT INTO rooms (room_no, room_type, price, status) VALUES (%s,%s,%s,%s)", (room_no, room_type, price, 'available'), commit=True)
    print("Room added")


def list_rooms():
    rows = DB.execute("SELECT * FROM rooms", fetchall=True)
    for r in rows or []:
        print(r['id'], r['room_no'], r['room_type'], r['price'], r['status'])

# ======================================================
# Customer Management
# ======================================================

def add_customer():
    name = safe_input("Name: ")
    phone = safe_input("Phone: ")
    email = safe_input("Email: ")
    DB.execute("INSERT INTO customers (name, phone, email) VALUES (%s,%s,%s)", (name, phone, email), commit=True)
    print("Customer added")


def list_customers():
    rows = DB.execute("SELECT * FROM customers", fetchall=True)
    for c in rows or []:
        print(c['id'], c['name'], c['phone'])

# ======================================================
# Booking Management
# ======================================================

def create_booking():
    list_customers()
    cid = safe_int("Customer ID: ")
    rows = DB.execute("SELECT * FROM rooms WHERE status='available'", fetchall=True)
    for r in rows or []:
        print(r['id'], r['room_no'], r['price'])
    rid = safe_int("Room ID: ")
    DB.execute("INSERT INTO bookings VALUES (NULL,%s,%s,NOW(),NULL,'reserved',0)", (cid, rid), commit=True)
    DB.execute("UPDATE rooms SET status='reserved' WHERE id=%s", (rid,), commit=True)
    print("Booking created")


def list_bookings():
    rows = DB.execute("SELECT * FROM bookings", fetchall=True)
    for b in rows or []:
        print(b['id'], b['customer_id'], b['room_id'], b['status'])


def check_in():
    list_bookings()
    bid = safe_int("Booking ID: ")
    DB.execute("UPDATE bookings SET status='checked_in', check_in=NOW() WHERE id=%s", (bid,), commit=True)
    print("Checked in")


def check_out():
    list_bookings()
    bid = safe_int("Booking ID: ")
    booking = DB.execute("SELECT * FROM bookings WHERE id=%s", (bid,), fetchone=True)
    room = DB.execute("SELECT * FROM rooms WHERE id=%s", (booking['room_id'],), fetchone=True)
    total = float(room['price'])
    DB.execute("UPDATE bookings SET status='checked_out', check_out=NOW(), total=%s WHERE id=%s", (total, bid), commit=True)
    DB.execute("UPDATE rooms SET status='available' WHERE id=%s", (room['id'],), commit=True)
    print("Checked out. Bill:", total)

# ======================================================
# Employee Management
# ======================================================

def add_employee():
    name = safe_input("Name: ")
    role = safe_input("Role: ")
    phone = safe_input("Phone: ")
    salary = safe_float("Salary: ")
    DB.execute("INSERT INTO employees VALUES (NULL,%s,%s,%s,%s,'active')", (name, role, phone, salary), commit=True)
    print("Employee added")


def list_employees():
    rows = DB.execute("SELECT * FROM employees", fetchall=True)
    for e in rows or []:
        print(e['id'], e['name'], e['role'], e['salary'])

# ======================================================
# Attendance & Payroll
# ======================================================

def mark_attendance():
    list_employees()
    eid = safe_int("Employee ID: ")
    DB.execute("INSERT INTO attendance VALUES (NULL,%s,CURDATE(),CURTIME(),NULL)", (eid,), commit=True)
    print("Clock in recorded")


def mark_departure():
    eid = safe_int("Employee ID: ")
    DB.execute("UPDATE attendance SET clock_out=CURTIME() WHERE employee_id=%s AND date=CURDATE()", (eid,), commit=True)
    print("Clock out recorded")


def generate_payroll():
    month = safe_int("Month: ")
    year = safe_int("Year: ")
    rows = DB.execute("SELECT * FROM employees WHERE status='active'", fetchall=True)
    for e in rows or []:
        DB.execute("INSERT INTO payroll VALUES (NULL,%s,%s,%s,%s)", (e['id'], month, year, e['salary']), commit=True)
    print("Payroll generated")


def list_payroll():
    rows = DB.execute("SELECT * FROM payroll", fetchall=True)
    for p in rows or []:
        print(p['employee_id'], p['month'], p['year'], p['amount'])

# ======================================================
# Services & Inventory
# ======================================================

def add_service():
    name = safe_input("Service name: ")
    price = safe_float("Price: ")
    DB.execute("INSERT INTO services VALUES (NULL,%s,%s)", (name, price), commit=True)
    print("Service added")


def list_services():
    rows = DB.execute("SELECT * FROM services", fetchall=True)
    for s in rows or []:
        print(s['id'], s['name'], s['price'])


def add_inventory():
    item = safe_input("Item: ")
    qty = safe_int("Quantity: ")
    DB.execute("INSERT INTO inventory VALUES (NULL,%s,%s)", (item, qty), commit=True)
    print("Inventory item added")


def list_inventory():
    rows = DB.execute("SELECT * FROM inventory", fetchall=True)
    for i in rows or []:
        print(i['id'], i['item'], i['quantity'])

# ======================================================
# Reports
# ======================================================

def report_occupancy():
    total = DB.execute("SELECT COUNT(*) AS c FROM rooms", fetchone=True)['c']
    occ = DB.execute("SELECT COUNT(*) AS c FROM rooms WHERE status!='available'", fetchone=True)['c']
    print("Occupancy:", (occ / total * 100) if total else 0)


def report_revenue():
    rev = DB.execute("SELECT SUM(total) AS r FROM bookings WHERE status='checked_out'", fetchone=True)['r']
    print("Total revenue:", rev)

# ======================================================
# Menus
# ======================================================

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


def report_menu():
    while True:
        print("1.Occupancy 2.Revenue 3.Back")
        c = safe_input("Choice: ")
        if c == '1': report_occupancy()
        elif c == '2': report_revenue()
        elif c == '3': break

# ======================================================
# Billing & Payments System
# ======================================================

# Invoices table extension (safe to call multiple times)
def init_billing_tables():
    try:
        DB.execute("CREATE TABLE IF NOT EXISTS invoices (id INT AUTO_INCREMENT PRIMARY KEY, booking_id INT, amount FLOAT, paid FLOAT, status VARCHAR(20))", commit=True)
        DB.execute("CREATE TABLE IF NOT EXISTS payments (id INT AUTO_INCREMENT PRIMARY KEY, invoice_id INT, amount FLOAT, pay_time DATETIME)", commit=True)
    except Exception as e:
        print("Billing table error:", e)


def create_invoice():
    try:
        list_bookings()
        bid = safe_int("Booking ID: ")
        booking = DB.execute("SELECT * FROM bookings WHERE id=%s", (bid,), fetchone=True)
        if not booking:
            print("Invalid booking")
            return
        amt = booking['total'] if booking['total'] else 0
        DB.execute("INSERT INTO invoices VALUES (NULL,%s,%s,0,'unpaid')", (bid, amt), commit=True)
        print("Invoice created")
    except Exception as e:
        print("Invoice error:", e)


def list_invoices():
    rows = DB.execute("SELECT * FROM invoices", fetchall=True)
    for i in rows or []:
        print(i['id'], i['booking_id'], i['amount'], i['paid'], i['status'])


def pay_invoice():
    try:
        list_invoices()
        iid = safe_int("Invoice ID: ")
        amt = safe_float("Pay amount: ")
        inv = DB.execute("SELECT * FROM invoices WHERE id=%s", (iid,), fetchone=True)
        if not inv:
            print("Invalid invoice")
            return
        new_paid = inv['paid'] + amt
        status = 'paid' if new_paid >= inv['amount'] else 'partial'
        DB.execute("UPDATE invoices SET paid=%s,status=%s WHERE id=%s", (new_paid, status, iid), commit=True)
        DB.execute("INSERT INTO payments VALUES (NULL,%s,%s,NOW())", (iid, amt), commit=True)
        print("Payment recorded")
    except Exception as e:
        print("Payment error:", e)

# ======================================================
# Service Orders (per Booking)
# ======================================================

def init_service_orders_table():
    try:
        DB.execute("CREATE TABLE IF NOT EXISTS service_orders (id INT AUTO_INCREMENT PRIMARY KEY, booking_id INT, service_id INT, quantity INT, total FLOAT)", commit=True)
    except Exception as e:
        print("Service order table error:", e)


def order_service():
    try:
        list_bookings()
        bid = safe_int("Booking ID: ")
        list_services()
        sid = safe_int("Service ID: ")
        qty = safe_int("Quantity: ")
        service = DB.execute("SELECT * FROM services WHERE id=%s", (sid,), fetchone=True)
        if not service:
            print("Invalid service")
            return
        total = service['price'] * qty
        DB.execute("INSERT INTO service_orders VALUES (NULL,%s,%s,%s,%s)", (bid, sid, qty, total), commit=True)
        print("Service ordered. Cost:", total)
    except Exception as e:
        print("Service order error:", e)


def list_service_orders():
    rows = DB.execute("SELECT * FROM service_orders", fetchall=True)
    for o in rows or []:
        print(o['booking_id'], o['service_id'], o['quantity'], o['total'])

# ======================================================
# Booking Cancellation & Refunds
# ======================================================

def init_cancellation_table():
    try:
        DB.execute("CREATE TABLE IF NOT EXISTS cancellations (id INT AUTO_INCREMENT PRIMARY KEY, booking_id INT, reason TEXT, refund FLOAT)", commit=True)
    except Exception as e:
        print("Cancellation table error:", e)


def cancel_booking_advanced():
    try:
        list_bookings()
        bid = safe_int("Booking ID: ")
        reason = safe_input("Reason: ")
        booking = DB.execute("SELECT * FROM bookings WHERE id=%s", (bid,), fetchone=True)
        if not booking:
            print("Invalid booking")
            return
        refund = (booking['total'] or 0) * 0.8
        DB.execute("INSERT INTO cancellations VALUES (NULL,%s,%s,%s)", (bid, reason, refund), commit=True)
        DB.execute("UPDATE bookings SET status='cancelled' WHERE id=%s", (bid,), commit=True)
        print("Booking cancelled. Refund:", refund)
    except Exception as e:
        print("Cancellation error:", e)

# ======================================================
# User Management (Admin)
# ======================================================

def add_user():
    try:
        u = safe_input("Username: ")
        p = safe_input("Password: ")
        print("Available roles:", ", ".join(ROLE_PERMISSIONS.keys()))
        r = safe_input("Role: ").strip().lower()
        if r not in ROLE_PERMISSIONS:
            print("Invalid role, defaulting to 'staff'")
            r = "staff"
        DB.execute("INSERT INTO users (username,password,role) VALUES (%s,%s,%s)", (u, p, r), commit=True)
        print("User added with role:", r)
    except Exception as e:
        print("User error:", e)


def list_users():
    rows = DB.execute("SELECT * FROM users", fetchall=True)
    for u in rows or []:
        print(u['id'], u['username'])

# ======================================================
# Activity Logs (Simple)
# ======================================================

def init_logs_table():
    try:
        DB.execute("CREATE TABLE IF NOT EXISTS logs (id INT AUTO_INCREMENT PRIMARY KEY, message TEXT, log_time DATETIME)", commit=True)
    except Exception as e:
        print("Log table error:", e)


def log_event(msg):
    try:
        DB.execute("INSERT INTO logs VALUES (NULL,%s,NOW())", (msg,), commit=True)
    except Exception:
        pass


def list_logs():
    rows = DB.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50", fetchall=True)
    for l in rows or []:
        print(l['log_time'], l['message'])

# ======================================================
# Extended Menus
# ======================================================

def billing_menu():
    while True:
        print("1.Create Invoice 2.List Invoices 3.Pay Invoice 4.Back")
        c = safe_input("Choice: ")
        if c == '1': create_invoice()
        elif c == '2': list_invoices()
        elif c == '3': pay_invoice()
        elif c == '4': break


def service_order_menu():
    while True:
        print("1.Order Service 2.List Orders 3.Back")
        c = safe_input("Choice: ")
        if c == '1': order_service()
        elif c == '2': list_service_orders()
        elif c == '3': break


def admin_menu():
    while True:
        print("1.Add User 2.List Users 3.View Logs 4.Back")
        c = safe_input("Choice: ")
        if c == '1': add_user()
        elif c == '2': list_users()
        elif c == '3': list_logs()
        elif c == '4': break

# ======================================================
# Room Maintenance System
# ======================================================

def init_maintenance_table():
    try:
        DB.execute("CREATE TABLE IF NOT EXISTS maintenance (id INT AUTO_INCREMENT PRIMARY KEY, room_id INT, issue TEXT, status VARCHAR(20))", commit=True)
    except Exception as e:
        print("Maintenance table error:", e)


def report_maintenance():
    try:
        list_rooms()
        rid = safe_int("Room ID: ")
        issue = safe_input("Issue description: ")
        DB.execute("INSERT INTO maintenance VALUES (NULL,%s,%s,'open')", (rid, issue), commit=True)
        DB.execute("UPDATE rooms SET status='maintenance' WHERE id=%s", (rid,), commit=True)
        print("Maintenance reported")
    except Exception as e:
        print("Maintenance error:", e)


def resolve_maintenance():
    try:
        rows = DB.execute("SELECT * FROM maintenance WHERE status='open'", fetchall=True)
        for r in rows or []:
            print(r['id'], r['room_id'], r['issue'])
        mid = safe_int("Maintenance ID to close: ")
        m = DB.execute("SELECT * FROM maintenance WHERE id=%s", (mid,), fetchone=True)
        if not m:
            print("Invalid ID")
            return
        DB.execute("UPDATE maintenance SET status='closed' WHERE id=%s", (mid,), commit=True)
        DB.execute("UPDATE rooms SET status='available' WHERE id=%s", (m['room_id'],), commit=True)
        print("Maintenance closed")
    except Exception as e:
        print("Resolve error:", e)

# ======================================================
# Inventory Consumption Tracking
# ======================================================

def init_inventory_usage_table():
    try:
        DB.execute("CREATE TABLE IF NOT EXISTS inventory_usage (id INT AUTO_INCREMENT PRIMARY KEY, item_id INT, quantity INT, used_on DATETIME)", commit=True)
    except Exception as e:
        print("Inventory usage table error:", e)


def consume_inventory():
    try:
        list_inventory()
        iid = safe_int("Inventory ID: ")
        qty = safe_int("Quantity to use: ")
        item = DB.execute("SELECT * FROM inventory WHERE id=%s", (iid,), fetchone=True)
        if not item or item['quantity'] < qty:
            print("Insufficient stock")
            return
        new_qty = item['quantity'] - qty
        DB.execute("UPDATE inventory SET quantity=%s WHERE id=%s", (new_qty, iid), commit=True)
        DB.execute("INSERT INTO inventory_usage VALUES (NULL,%s,%s,NOW())", (iid, qty), commit=True)
        print("Inventory consumed. Remaining:", new_qty)
    except Exception as e:
        print("Consumption error:", e)


def low_stock_report(threshold=5):
    rows = DB.execute("SELECT * FROM inventory WHERE quantity<=%s", (threshold,), fetchall=True)
    for r in rows or []:
        print("LOW STOCK:", r['item'], r['quantity'])

# ======================================================
# Dynamic Pricing (Weekend / Season)
# ======================================================

def calculate_dynamic_price(base_price, is_weekend, season_factor):
    price = base_price
    if is_weekend:
        price *= 1.2
    price *= season_factor
    return round(price, 2)


def preview_room_price():
    list_rooms()
    rid = safe_int("Room ID: ")
    room = DB.execute("SELECT * FROM rooms WHERE id=%s", (rid,), fetchone=True)
    if not room:
        print("Invalid room")
        return
    weekend = safe_input("Weekend? (y/n): ").lower() == 'y'
    factor = safe_float("Season factor (e.g. 1.0 normal, 1.5 peak): ")
    price = calculate_dynamic_price(room['price'], weekend, factor)
    print("Dynamic price:", price)

# ======================================================
# Extended Reports
# ======================================================

def report_employee_cost():
    rows = DB.execute("SELECT SUM(salary) AS total FROM employees WHERE status='active'", fetchone=True)
    print("Total monthly employee cost:", rows['total'])


def report_service_revenue():
    rows = DB.execute("SELECT SUM(total) AS rev FROM service_orders", fetchone=True)
    print("Service revenue:", rows['rev'])


def report_inventory_usage():
    rows = DB.execute("SELECT * FROM inventory_usage", fetchall=True)
    for r in rows or []:
        print(r['item_id'], r['quantity'], r['used_on'])

# ======================================================
# Extended Menus for New Systems
# ======================================================

def maintenance_menu():
    while True:
        print("1.Report Issue 2.Resolve Issue 3.Back")
        c = safe_input("Choice: ")
        if c == '1': report_maintenance()
        elif c == '2': resolve_maintenance()
        elif c == '3': break


def inventory_usage_menu():
    while True:
        print("1.Consume Inventory 2.Low Stock Report 3.Usage Report 4.Back")
        c = safe_input("Choice: ")
        if c == '1': consume_inventory()
        elif c == '2': low_stock_report()
        elif c == '3': report_inventory_usage()
        elif c == '4': break


def pricing_menu():
    while True:
        print("1.Preview Room Price 2.Back")
        c = safe_input("Choice: ")
        if c == '1': preview_room_price()
        elif c == '2': break


def extended_reports_menu():
    while True:
        print("1.Employee Cost 2.Service Revenue 3.Back")
        c = safe_input("Choice: ")
        if c == '1': report_employee_cost()
        elif c == '2': report_service_revenue()
        elif c == '3': break

# ======================================================
# Role-Based Permissions System
# ======================================================

ROLE_PERMISSIONS = {
    'admin': ['all'],
    'manager': ['rooms','customers','bookings','employees','services','inventory','reports'],
    'receptionist': ['rooms','customers','bookings','services'],
    'accountant': ['billing','reports'],
    'staff': ['services']
}


def has_permission(section):
    try:
        if not current_user:
            return False
        role = current_user.get('role', 'admin') if isinstance(current_user, dict) else 'admin'
        perms = ROLE_PERMISSIONS.get(role, [])
        return 'all' in perms or section in perms
    except Exception:
        return False

# ======================================================
# Booking Date Validation & Conflict Detection
# ======================================================

def is_room_available(room_id, start_date, end_date):
    try:
        sql = "SELECT * FROM bookings WHERE room_id=%s AND status IN ('reserved','checked_in') AND (check_in <= %s AND (check_out IS NULL OR check_out >= %s))"
        conflict = DB.execute(sql, (room_id, end_date, start_date), fetchone=True)
        return conflict is None
    except Exception:
        return False


def create_booking_with_dates():
    try:
        list_customers()
        cid = safe_int("Customer ID: ")
        list_rooms()
        rid = safe_int("Room ID: ")
        start = safe_input("Check-in (YYYY-MM-DD): ")
        end = safe_input("Check-out (YYYY-MM-DD): ")
        if not is_room_available(rid, start, end):
            print("Room not available for selected dates")
            return
        DB.execute("INSERT INTO bookings VALUES (NULL,%s,%s,%s,%s,'reserved',0)", (cid, rid, start, end), commit=True)
        DB.execute("UPDATE rooms SET status='reserved' WHERE id=%s", (rid,), commit=True)
        print("Booking created with dates")
    except Exception as e:
        print("Booking date error:", e)

# ======================================================
# Vendor & Supplier Management
# ======================================================

def init_vendor_tables():
    try:
        DB.execute("CREATE TABLE IF NOT EXISTS vendors (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), phone VARCHAR(50), email VARCHAR(100))", commit=True)
        DB.execute("CREATE TABLE IF NOT EXISTS purchase_orders (id INT AUTO_INCREMENT PRIMARY KEY, vendor_id INT, item VARCHAR(100), quantity INT, price FLOAT, status VARCHAR(20))", commit=True)
    except Exception as e:
        print("Vendor table error:", e)


def add_vendor():
    try:
        name = safe_input("Vendor name: ")
        phone = safe_input("Phone: ")
        email = safe_input("Email: ")
        DB.execute("INSERT INTO vendors VALUES (NULL,%s,%s,%s)", (name, phone, email), commit=True)
        print("Vendor added")
    except Exception as e:
        print("Vendor error:", e)


def list_vendors():
    rows = DB.execute("SELECT * FROM vendors", fetchall=True)
    for v in rows or []:
        print(v['id'], v['name'], v['phone'])


def create_purchase_order():
    try:
        list_vendors()
        vid = safe_int("Vendor ID: ")
        item = safe_input("Item: ")
        qty = safe_int("Quantity: ")
        price = safe_float("Total price: ")
        DB.execute("INSERT INTO purchase_orders VALUES (NULL,%s,%s,%s,%s,'ordered')", (vid, item, qty, price), commit=True)
        print("Purchase order created")
    except Exception as e:
        print("Purchase order error:", e)


def list_purchase_orders():
    rows = DB.execute("SELECT * FROM purchase_orders", fetchall=True)
    for p in rows or []:
        print(p['id'], p['vendor_id'], p['item'], p['quantity'], p['price'], p['status'])

# ======================================================
# Data Backup & Restore (SQL Table Copy)
# ======================================================

def backup_table(table_name):
    try:
        backup_table = table_name + "_backup"
        DB.execute(f"CREATE TABLE IF NOT EXISTS {backup_table} AS SELECT * FROM {table_name}", commit=True)
        print("Backup created for", table_name)
    except Exception as e:
        print("Backup error:", e)


def restore_table(table_name):
    try:
        backup_table = table_name + "_backup"
        DB.execute(f"DELETE FROM {table_name}", commit=True)
        DB.execute(f"INSERT INTO {table_name} SELECT * FROM {backup_table}", commit=True)
        print("Table restored from backup")
    except Exception as e:
        print("Restore error:", e)

# ======================================================
# Search & Filter Utilities
# ======================================================

def search_customer_by_name():
    name = safe_input("Customer name keyword: ")
    rows = DB.execute("SELECT * FROM customers WHERE name LIKE %s", ("%"+name+"%",), fetchall=True)
    for r in rows or []:
        print(r['id'], r['name'], r['phone'])


def search_room_by_type():
    rtype = safe_input("Room type: ")
    rows = DB.execute("SELECT * FROM rooms WHERE room_type=%s", (rtype,), fetchall=True)
    for r in rows or []:
        print(r['id'], r['room_no'], r['price'], r['status'])

# ======================================================
# Vendor Menu
# ======================================================

def vendor_menu():
    while True:
        print("1.Add Vendor 2.List Vendors 3.Create Purchase Order 4.List Orders 5.Back")
        c = safe_input("Choice: ")
        if c == '1': add_vendor()
        elif c == '2': list_vendors()
        elif c == '3': create_purchase_order()
        elif c == '4': list_purchase_orders()
        elif c == '5': break

# ======================================================
# Backup Menu
# ======================================================

def backup_menu():
    while True:
        print("1.Backup Table 2.Restore Table 3.Back")
        c = safe_input("Choice: ")
        if c == '1': backup_table(safe_input("Table name: "))
        elif c == '2': restore_table(safe_input("Table name: "))
        elif c == '3': break

# ======================================================
# Search Menu
# ======================================================

def search_menu():
    while True:
        print("1.Search Customer 2.Search Room 3.Back")
        c = safe_input("Choice: ")
        if c == '1': search_customer_by_name()
        elif c == '2': search_room_by_type()
        elif c == '3': break

# ======================================================
# Attendance-based Salary Calculation
# ======================================================

def calculate_salary_from_attendance(employee_id, month, year):
    try:
        sql = "SELECT COUNT(*) AS days FROM attendance WHERE employee_id=%s AND MONTH(date)=%s AND YEAR(date)=%s"
        row = DB.execute(sql, (employee_id, month, year), fetchone=True)
        days = row['days'] if row else 0
        emp = DB.execute("SELECT salary FROM employees WHERE id=%s", (employee_id,), fetchone=True)
        if not emp:
            return 0
        daily = emp['salary'] / 30
        return round(days * daily, 2)
    except Exception:
        return 0


def generate_payroll_from_attendance():
    try:
        month = safe_int("Month: ")
        year = safe_int("Year: ")
        employees = DB.execute("SELECT * FROM employees WHERE status='active'", fetchall=True)
        for e in employees or []:
            amount = calculate_salary_from_attendance(e['id'], month, year)
            DB.execute("INSERT INTO payroll VALUES (NULL,%s,%s,%s,%s)", (e['id'], month, year, amount), commit=True)
        print("Attendance-based payroll generated")
    except Exception as e:
        print("Payroll error:", e)

# ======================================================
# Tax System on Invoices
# ======================================================

def init_tax_table():
    try:
        DB.execute("CREATE TABLE IF NOT EXISTS tax_rates (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), rate FLOAT)", commit=True)
    except Exception as e:
        print("Tax table error:", e)


def add_tax_rate():
    name = safe_input("Tax name: ")
    rate = safe_float("Rate (%): ")
    DB.execute("INSERT INTO tax_rates VALUES (NULL,%s,%s)", (name, rate), commit=True)
    print("Tax rate added")


def list_tax_rates():
    rows = DB.execute("SELECT * FROM tax_rates", fetchall=True)
    for t in rows or []:
        print(t['id'], t['name'], t['rate'])


def apply_tax_to_invoice():
    try:
        list_invoices()
        iid = safe_int("Invoice ID: ")
        list_tax_rates()
        tid = safe_int("Tax ID: ")
        tax = DB.execute("SELECT * FROM tax_rates WHERE id=%s", (tid,), fetchone=True)
        inv = DB.execute("SELECT * FROM invoices WHERE id=%s", (iid,), fetchone=True)
        if not tax or not inv:
            print("Invalid selection")
            return
        tax_amt = inv['amount'] * tax['rate'] / 100
        new_amt = inv['amount'] + tax_amt
        DB.execute("UPDATE invoices SET amount=%s WHERE id=%s", (new_amt, iid), commit=True)
        print("Tax applied. New amount:", new_amt)
    except Exception as e:
        print("Tax apply error:", e)

# ======================================================
# Room Availability Calendar (text view)
# ======================================================

def room_availability_calendar():
    try:
        list_rooms()
        rid = safe_int("Room ID: ")
        rows = DB.execute("SELECT check_in, check_out, status FROM bookings WHERE room_id=%s", (rid,), fetchall=True)
        print("Bookings for room:")
        for r in rows or []:
            print(r['check_in'], "to", r['check_out'], r['status'])
    except Exception as e:
        print("Calendar error:", e)

# ======================================================
# Automatic Inventory Deduction from Services
# ======================================================

def deduct_inventory_for_service(service_id, qty):
    try:
        items = DB.execute("SELECT * FROM inventory", fetchall=True)
        for item in items or []:
            if item['quantity'] >= qty:
                new_qty = item['quantity'] - qty
                DB.execute("UPDATE inventory SET quantity=%s WHERE id=%s", (new_qty, item['id']), commit=True)
                break
    except Exception:
        pass

# override order_service to include deduction
old_order_service = order_service

def order_service():
    try:
        old_order_service()
        sid = safe_int("Service ID again for inventory deduction: ")
        qty = safe_int("Quantity again: ")
        deduct_inventory_for_service(sid, qty)
        print("Inventory updated for service usage")
    except Exception as e:
        print("Service order extended error:", e)

# ======================================================
# Final Extended Menus
# ======================================================

def tax_menu_extended():
    while True:
        print("1.Add Tax 2.List Taxes 3.Apply Tax 4.Back")
        c = safe_input("Choice: ")
        if c == '1': add_tax_rate()
        elif c == '2': list_tax_rates()
        elif c == '3': apply_tax_to_invoice()
        elif c == '4': break


def attendance_payroll_menu():
    while True:
        print("1.Generate Payroll (Attendance) 2.Back")
        c = safe_input("Choice: ")
        if c == '1': generate_payroll_from_attendance()
        elif c == '2': break


def calendar_menu():
    while True:
        print("1.View Room Calendar 2.Back")
        c = safe_input("Choice: ")
        if c == '1': room_availability_calendar()
        elif c == '2': break

# ======================================================
# Main Menu
# ======================================================

def main_menu():
    initialize_database()
    while True:
        if not current_user:
            if not login():
                continue
        print("\nMafwbh Inn - Hotel Management System")
        print("1.Room 2.Customer 3.Booking 4.Employee 5.Services 6.Inventory 7.Reports 8.Logout 9.Exit")
        c = safe_input("Choice: ")
        if c == '1':
            if has_permission('rooms'):
                add_room()
            else:
                print("Access denied for rooms")
        elif c == '2':
            if has_permission('customers'):
                add_customer()
            else:
                print("Access denied for customers")
        elif c == '3':
            if has_permission('bookings'):
                booking_menu()
            else:
                print("Access denied for bookings")
        elif c == '4':
            if has_permission('employees'):
                employee_menu()
            else:
                print("Access denied for employees")
        elif c == '5':
            if has_permission('services'):
                service_menu()
            else:
                print("Access denied for services")
        elif c == '6':
            if has_permission('inventory'):
                inventory_menu()
            else:
                print("Access denied for inventory")
        elif c == '7':
            if has_permission('reports'):
                report_menu()
            else:
                print("Access denied for reports")
        elif c == '8': logout()
        elif c == '9': break

if __name__ == '__main__':
    main_menu()
