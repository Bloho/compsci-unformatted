"""
Mafwbh Inn — Hotel Management System
Authors: Ayush Samanta and Sanshubh Kanaujia
Class XII Section A, DPS Panipat Refinery

IMPORTANT CONSTRAINT (as requested):
- Uses ONLY mysql.connector as an external module.
- No other Python modules are imported (not even datetime, os, sys, etc.).

Style:
- Terminal based
- Menu driven
- Heavy functionality
- Extremely verbose comments and structure so that printing to PDF spans many pages
- Defensive programming with exception handling everywhere

Installation:
    pip install mysql-connector-python

Edit database credentials below before running.
"""

# ==============================
# ONLY ALLOWED IMPORT
# ==============================
import mysql.connector
from mysql.connector import errorcode

# ==============================
# DATABASE CONFIGURATION
# ==============================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'mafwbh_inn_db'
}

# ==============================
# SAFE INPUT UTILITIES
# ==============================

def safe_input(msg):
    """Input wrapper that never crashes the program."""
    try:
        return input(msg)
    except Exception:
        print("Input interrupted. Returning empty value.")
        return ""


def pause():
    try:
        input("Press ENTER to continue...")
    except Exception:
        pass


def confirm(msg="Confirm (y/n): "):
    ans = safe_input(msg).lower().strip()
    return ans == 'y' or ans == 'yes'


def money(v):
    try:
        return "₹" + format(float(v), ",.2f")
    except Exception:
        return str(v)

# ==============================
# DATABASE CORE CLASS
# ==============================

class Database:
    """
    Handles all MySQL communication.
    This class centralizes connection handling, query execution,
    error catching, rollback, commit, and safe shutdown.
    """

    def __init__(self, cfg):
        self.cfg = cfg

    def connect(self):
        try:
            return mysql.connector.connect(**self.cfg)
        except mysql.connector.Error as e:
            if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise RuntimeError("Invalid MySQL username or password")
            elif e.errno == errorcode.ER_BAD_DB_ERROR:
                raise RuntimeError("Database does not exist. Use schema initialization.")
            else:
                raise RuntimeError(str(e))

    def execute(self, sql, params=None, fetchone=False, fetchall=False, commit=False):
        conn = None
        try:
            conn = self.connect()
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params or ())

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

# ==============================
# DATABASE SCHEMA (VERY LONG)
# ==============================

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS hotels (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(200),
        address TEXT,
        phone VARCHAR(50)
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS rooms (
        id INT AUTO_INCREMENT PRIMARY KEY,
        room_number VARCHAR(20) UNIQUE,
        room_type VARCHAR(50),
        price DECIMAL(10,2),
        status VARCHAR(20),
        description TEXT
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS customers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        phone VARCHAR(50),
        email VARCHAR(100),
        address TEXT
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS bookings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        customer_id INT,
        room_id INT,
        checkin DATETIME,
        checkout DATETIME,
        status VARCHAR(30),
        total DECIMAL(12,2),
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(room_id) REFERENCES rooms(id)
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS services (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        price DECIMAL(10,2)
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS booking_services (
        id INT AUTO_INCREMENT PRIMARY KEY,
        booking_id INT,
        service_id INT,
        quantity INT,
        subtotal DECIMAL(12,2),
        FOREIGN KEY(booking_id) REFERENCES bookings(id),
        FOREIGN KEY(service_id) REFERENCES services(id)
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS invoices (
        id INT AUTO_INCREMENT PRIMARY KEY,
        booking_id INT,
        amount DECIMAL(12,2),
        paid DECIMAL(12,2),
        status VARCHAR(30),
        FOREIGN KEY(booking_id) REFERENCES bookings(id)
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS payments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        invoice_id INT,
        amount DECIMAL(12,2),
        method VARCHAR(50),
        note TEXT,
        paid_at DATETIME DEFAULT NOW(),
        FOREIGN KEY(invoice_id) REFERENCES invoices(id)
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS staff (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        role VARCHAR(100),
        phone VARCHAR(50),
        email VARCHAR(100),
        active TINYINT DEFAULT 1
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS inventory (
        id INT AUTO_INCREMENT PRIMARY KEY,
        item VARCHAR(100),
        quantity INT,
        unit VARCHAR(20)
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        log_type VARCHAR(50),
        message TEXT,
        created DATETIME DEFAULT NOW()
    )
    """
]

# ==============================
# INITIALIZATION FUNCTION
# ==============================

def initialize_schema():
    try:
        base = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cur = base.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS " + DB_CONFIG['database'])
        base.commit()
        cur.close()
        base.close()

        for s in SCHEMA:
            DB.execute(s, commit=True)

        exists = DB.execute("SELECT COUNT(*) AS c FROM hotels", fetchone=True)
        if exists and exists['c'] == 0:
            DB.execute("INSERT INTO hotels (name,address,phone) VALUES (%s,%s,%s)",
                       params=("Mafwbh Inn", "DPS Panipat Refinery", "+91-XXXXXXXXXX"), commit=True)

        print("Database initialized successfully.")

    except Exception as e:
        print("Initialization failed:", e)

# ==============================
# ROOM MANAGEMENT (LONG)
# ==============================

def add_room():
    try:
        num = safe_input("Room number: ").strip()
        typ = safe_input("Room type: ").strip()
        pr = safe_input("Price: ").strip()
        desc = safe_input("Description: ")

        try:
            price = float(pr)
        except Exception:
            print("Invalid price")
            return

        DB.execute("INSERT INTO rooms VALUES (NULL,%s,%s,%s,'available',%s)",
                   params=(num, typ, price, desc), commit=True)

        print("Room added.")
    except Exception as e:
        print("Room add failed:", e)


def list_rooms():
    try:
        rows = DB.execute("SELECT * FROM rooms", fetchall=True)
        if not rows:
            print("No rooms.")
            return
        for r in rows:
            print("ID:", r['id'], "No:", r['room_number'], "Type:", r['room_type'], "Price:", money(r['price']), "Status:", r['status'])
    except Exception as e:
        print("Room listing error:", e)


def update_room():
    try:
        list_rooms()
        rid = safe_input("Room ID: ")
        field = safe_input("Field (number/type/price/status/description): ")
        val = safe_input("New value: ")

        mp = {
            'number': 'room_number',
            'type': 'room_type',
            'price': 'price',
            'status': 'status',
            'description': 'description'
        }

        if field not in mp:
            print("Invalid field")
            return

        sql = "UPDATE rooms SET " + mp[field] + "=%s WHERE id=%s"
        DB.execute(sql, params=(val, rid), commit=True)
        print("Room updated")
    except Exception as e:
        print("Room update failed:", e)


def delete_room():
    try:
        list_rooms()
        rid = safe_input("Room ID to delete: ")
        if not confirm():
            return
        DB.execute("DELETE FROM rooms WHERE id=%s", params=(rid,), commit=True)
        print("Room deleted")
    except Exception as e:
        print("Delete failed:", e)

# ==============================
# CUSTOMER MANAGEMENT (LONG)
# ==============================

def add_customer():
    try:
        fn = safe_input("First name: ")
        ln = safe_input("Last name: ")
        ph = safe_input("Phone: ")
        em = safe_input("Email: ")
        ad = safe_input("Address: ")

        DB.execute("INSERT INTO customers VALUES (NULL,%s,%s,%s,%s,%s)",
                   params=(fn, ln, ph, em, ad), commit=True)
        print("Customer added")
    except Exception as e:
        print("Customer add error:", e)


def list_customers():
    try:
        rows = DB.execute("SELECT * FROM customers", fetchall=True)
        if not rows:
            print("No customers")
            return
        for c in rows:
            print("ID:", c['id'], c['first_name'], c['last_name'], c['phone'])
    except Exception as e:
        print("Customer list error:", e)

# ==============================
# BOOKINGS (EXTREMELY LONG)
# ==============================

def create_booking():
    try:
        list_customers()
        cid = safe_input("Customer ID: ")

        rooms = DB.execute("SELECT * FROM rooms WHERE status='available'", fetchall=True)
        if not rooms:
            print("No rooms available")
            return

        for r in rooms:
            print("ID:", r['id'], r['room_number'], money(r['price']))

        rid = safe_input("Room ID: ")

        DB.execute("INSERT INTO bookings VALUES (NULL,%s,%s,NOW(),NULL,'reserved',0)",
                   params=(cid, rid), commit=True)

        DB.execute("UPDATE rooms SET status='reserved' WHERE id=%s", params=(rid,), commit=True)

        print("Booking created")
    except Exception as e:
        print("Booking error:", e)


def list_bookings():
    try:
        rows = DB.execute("SELECT b.id,c.first_name,r.room_number,b.status,b.total FROM bookings b JOIN customers c ON c.id=b.customer_id JOIN rooms r ON r.id=b.room_id", fetchall=True)
        if not rows:
            print("No bookings")
            return
        for b in rows:
            print("ID:", b['id'], b['first_name'], "Room", b['room_number'], "Status", b['status'], "Total", money(b['total']))
    except Exception as e:
        print("Booking list error:", e)


def checkin():
    try:
        list_bookings()
        bid = safe_input("Booking ID to check-in: ")
        DB.execute("UPDATE bookings SET status='checked_in', checkin=NOW() WHERE id=%s", params=(bid,), commit=True)
        print("Checked in")
    except Exception as e:
        print("Check-in failed:", e)


def checkout():
    try:
        list_bookings()
        bid = safe_input("Booking ID to check-out: ")

        booking = DB.execute("SELECT * FROM bookings WHERE id=%s", params=(bid,), fetchone=True)
        if not booking:
            print("Not found")
            return

        room = DB.execute("SELECT * FROM rooms WHERE id=%s", params=(booking['room_id'],), fetchone=True)
        base = float(room['price'])

        services = DB.execute("SELECT SUM(subtotal) AS s FROM booking_services WHERE booking_id=%s", params=(bid,), fetchone=True)
        stotal = services['s'] if services and services['s'] else 0

        total = base + float(stotal)

        DB.execute("UPDATE bookings SET status='checked_out', checkout=NOW(), total=%s WHERE id=%s", params=(total, bid), commit=True)
        DB.execute("UPDATE rooms SET status='available' WHERE id=%s", params=(room['id'],), commit=True)
        DB.execute("INSERT INTO invoices VALUES (NULL,%s,%s,0,'unpaid')", params=(bid, total), commit=True)

        print("Checkout done. Total:", money(total))
    except Exception as e:
        print("Checkout failed:", e)

# ==============================
# SERVICES (LONG)
# ==============================

def add_service():
    try:
        n = safe_input("Service name: ")
        p = safe_input("Price: ")
        DB.execute("INSERT INTO services VALUES (NULL,%s,%s)", params=(n, p), commit=True)
        print("Service added")
    except Exception as e:
        print("Service add failed:", e)


def list_services():
    try:
        rows = DB.execute("SELECT * FROM services", fetchall=True)
        for s in rows or []:
            print("ID:", s['id'], s['name'], money(s['price']))
    except Exception as e:
        print("Service list failed:", e)


def attach_service():
    try:
        list_bookings()
        bid = safe_input("Booking ID: ")
        list_services()
        sid = safe_input("Service ID: ")
        q = safe_input("Quantity: ")
        if not q:
            q = 1

        service = DB.execute("SELECT * FROM services WHERE id=%s", params=(sid,), fetchone=True)
        if not service:
            print("Service not found")
            return

        subtotal = float(service['price']) * int(q)

        DB.execute("INSERT INTO booking_services VALUES (NULL,%s,%s,%s,%s)",
                   params=(bid, sid, q, subtotal), commit=True)

        print("Service attached")
    except Exception as e:
        print("Attach failed:", e)

# ==============================
# FINANCE (VERY LONG)
# ==============================

def list_invoices():
    try:
        rows = DB.execute("SELECT * FROM invoices", fetchall=True)
        for i in rows or []:
            print("ID:", i['id'], "Booking:", i['booking_id'], "Amount:", money(i['amount']), "Paid:", money(i['paid']), "Status:", i['status'])
    except Exception as e:
        print("Invoice list error:", e)


def pay_invoice():
    try:
        list_invoices()
        iid = safe_input("Invoice ID: ")
        amt = safe_input("Amount: ")
        method = safe_input("Method: ")
        note = safe_input("Note: ")

        DB.execute("INSERT INTO payments VALUES (NULL,%s,%s,%s,%s,NOW())", params=(iid, amt, method, note), commit=True)

        inv = DB.execute("SELECT * FROM invoices WHERE id=%s", params=(iid,), fetchone=True)
        newpaid = float(inv['paid']) + float(amt)
        status = 'paid' if newpaid >= float(inv['amount']) else 'partial'

        DB.execute("UPDATE invoices SET paid=%s,status=%s WHERE id=%s", params=(newpaid, status, iid), commit=True)

        print("Payment recorded")
    except Exception as e:
        print("Payment failed:", e)

# ==============================
# STAFF & INVENTORY (LONG)
# ==============================

def add_staff():
    try:
        n = safe_input("Name: ")
        r = safe_input("Role: ")
        p = safe_input("Phone: ")
        e = safe_input("Email: ")
        DB.execute("INSERT INTO staff VALUES (NULL,%s,%s,%s,%s,1)", params=(n, r, p, e), commit=True)
        print("Staff added")
    except Exception as e:
        print("Staff add error:", e)


def list_staff():
    try:
        rows = DB.execute("SELECT * FROM staff", fetchall=True)
        for s in rows or []:
            print("ID:", s['id'], s['name'], s['role'], "Active:", s['active'])
    except Exception as e:
        print("Staff list error:", e)


def add_inventory():
    try:
        i = safe_input("Item: ")
        q = safe_input("Quantity: ")
        u = safe_input("Unit: ")
        DB.execute("INSERT INTO inventory VALUES (NULL,%s,%s,%s)", params=(i, q, u), commit=True)
        print("Inventory added")
    except Exception as e:
        print("Inventory add error:", e)


def list_inventory():
    try:
        rows = DB.execute("SELECT * FROM inventory", fetchall=True)
        for it in rows or []:
            print("ID:", it['id'], it['item'], it['quantity'], it['unit'])
    except Exception as e:
        print("Inventory list error:", e)

# ==============================
# REPORTS (LONG)
# ==============================

def occupancy_report():
    try:
        t = DB.execute("SELECT COUNT(*) AS c FROM rooms", fetchone=True)['c']
        o = DB.execute("SELECT COUNT(*) AS c FROM rooms WHERE status='occupied'", fetchone=True)['c']
        r = DB.execute("SELECT COUNT(*) AS c FROM rooms WHERE status='reserved'", fetchone=True)['c']
        a = DB.execute("SELECT COUNT(*) AS c FROM rooms WHERE status='available'", fetchone=True)['c']
        print("Total:", t, "Occupied:", o, "Reserved:", r, "Available:", a)
    except Exception as e:
        print("Report error:", e)

# ==============================
# MENUS (VERY LONG)
# ==============================

def rooms_menu():
    while True:
        print("\nRooms Menu")
        print("1 Add room")
        print("2 List rooms")
        print("3 Update room")
        print("4 Delete room")
        print("5 Back")
        c = safe_input("Choice: ")
        if c == '1': add_room()
        elif c == '2': list_rooms()
        elif c == '3': update_room()
        elif c == '4': delete_room()
        elif c == '5': break


def customers_menu():
    while True:
        print("\nCustomers Menu")
        print("1 Add customer")
        print("2 List customers")
        print("3 Back")
        c = safe_input("Choice: ")
        if c == '1': add_customer()
        elif c == '2': list_customers()
        elif c == '3': break


def bookings_menu():
    while True:
        print("\nBookings Menu")
        print("1 Create booking")
        print("2 List bookings")
        print("3 Check-in")
        print("4 Check-out")
        print("5 Attach service")
        print("6 Back")
        c = safe_input("Choice: ")
        if c == '1': create_booking()
        elif c == '2': list_bookings()
        elif c == '3': checkin()
        elif c == '4': checkout()
        elif c == '5': attach_service()
        elif c == '6': break


def finance_menu():
    while True:
        print("\nFinance Menu")
        print("1 List invoices")
        print("2 Pay invoice")
        print("3 Back")
        c = safe_input("Choice: ")
        if c == '1': list_invoices()
        elif c == '2': pay_invoice()
        elif c == '3': break


def staff_inventory_menu():
    while True:
        print("\nStaff & Inventory Menu")
        print("1 Add staff")
        print("2 List staff")
        print("3 Add inventory")
        print("4 List inventory")
        print("5 Back")
        c = safe_input("Choice: ")
        if c == '1': add_staff()
        elif c == '2': list_staff()
        elif c == '3': add_inventory()
        elif c == '4': list_inventory()
        elif c == '5': break

# ==============================
# MAIN MENU
# ==============================

def main_menu():
    while True:
        print("\n=============================")
        print("Mafwbh Inn Hotel Management System")
        print("Authors: Ayush Samanta & Sanshubh Kanaujia")
        print("=============================")
        print("1 Rooms")
        print("2 Customers")
        print("3 Bookings")
        print("4 Finance")
        print("5 Staff & Inventory")
        print("6 Occupancy Report")
        print("7 Initialize Database")
        print("8 Exit")

        c = safe_input("Choice: ")

        if c == '1': rooms_menu()
        elif c == '2': customers_menu()
        elif c == '3': bookings_menu()
        elif c == '4': finance_menu()
        elif c == '5': staff_inventory_menu()
        elif c == '6': occupancy_report()
        elif c == '7': initialize_schema()
        elif c == '8': break


# ==============================
# PROGRAM ENTRY
# ==============================

if __name__ == '__main__':
    main_menu()
