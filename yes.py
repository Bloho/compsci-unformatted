"""
Mafwbh Inn — Hotel Management System
Authors: Ayush Samanta and Sanshubh Kanaujia
Class XII Section A, DPS Panipat Refinery

Purpose:
A terminal-based, menu-driven hotel management system written in Python.
Interfaces with MySQL using mysql.connector (no extra third-party modules other than mysql-connector-python).
Designed for a school project — robust exception handling, many features, and comprehensive comments
so the code can be printed to PDF (long output).

How to use:
1. Install mysql-connector-python: pip install mysql-connector-python
2. Create a MySQL user and database or allow the script to create the schema if credentials permit.
3. Edit the DB configuration block below to match your MySQL credentials.
4. Run: python Mafwbh_Inn_Hotel_Management_System.py

Note: This script is intentionally verbose, commented, and feature-rich for demonstration and printing.
"""

# Standard library imports (allowed)
import sys
import os
import time
from datetime import datetime, timedelta
from getpass import getpass

# External: mysql-connector only (user must install mysql-connector-python)
import mysql.connector
from mysql.connector import errorcode

# ----------------------------- Database Configuration -----------------------------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # set your password or leave blank if none
    'database': 'mafwbh_inn_db'
}

# Optionally allow overriding via environment variables for convenience
DB_CONFIG['host'] = os.getenv('MIA_DB_HOST', DB_CONFIG['host'])
DB_CONFIG['user'] = os.getenv('MIA_DB_USER', DB_CONFIG['user'])
DB_CONFIG['password'] = os.getenv('MIA_DB_PASS', DB_CONFIG['password'])
DB_CONFIG['database'] = os.getenv('MIA_DB_NAME', DB_CONFIG['database'])

# ----------------------------- Utility Helpers -----------------------------

def safe_input(prompt):
    """A wrapper around input() that will not crash on KeyboardInterrupt.

    Returns empty string on interrupt instead of exiting — allows menu to continue.
    """
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print('\n[Interrupted] Returning to menu...')
        return ''


def confirm(prompt='Confirm (y/n): '):
    ans = safe_input(prompt).strip().lower()
    return ans in ('y', 'yes')


def pause(msg='Press Enter to continue...'):
    try:
        input(msg)
    except KeyboardInterrupt:
        print()


def format_currency(amount):
    try:
        return f"\u20B9{float(amount):,.2f}"
    except Exception:
        return str(amount)


# ----------------------------- Database Layer -----------------------------

class Database:
    """Handles MySQL connection and basic queries with exception handling.

    Use Database.get_connection() to acquire a connection (caller is responsible to close it).
    All queries are executed inside helper methods which print user-friendly errors.
    """

    def __init__(self, config):
        self.config = config

    def get_connection(self):
        """Return a live connection to MySQL or raise a descriptive error.

        Many small errors (ConnectionError, InterfaceError) are caught and re-raised as RuntimeError
        with user-friendly messages. This helps the menu remain responsive and informative.
        """
        try:
            conn = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            return conn
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                raise RuntimeError('Database not found. Run the initialization option to create schema.')
            elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise RuntimeError('Access denied. Check MySQL username/password in DB_CONFIG.')
            else:
                raise RuntimeError(f'MySQL error: {err}')

    def execute(self, query, params=None, commit=False, fetchone=False, fetchall=False):
        """Execute a single query safely and return results if requested.

        Parameters are optional. This method closes its cursor and connection safely.
        """
        conn = None
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = None
            if fetchone:
                result = cursor.fetchone()
            if fetchall:
                result = cursor.fetchall()
            if commit:
                conn.commit()
            cursor.close()
            conn.close()
            return result
        except mysql.connector.Error as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise RuntimeError(f'Database operation failed: {e}')
        except Exception as ex:
            raise RuntimeError(f'Unexpected database error: {ex}')
        finally:
            try:
                if conn and conn.is_connected():
                    conn.close()
            except Exception:
                pass


DB = Database(DB_CONFIG)

# ----------------------------- Schema & Initialization -----------------------------

SCHEMA_SQL = [
    # hotels metadata (single row)
    """
    CREATE TABLE IF NOT EXISTS hotels (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        address TEXT,
        phone VARCHAR(50),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB
    """,

    # rooms
    """
    CREATE TABLE IF NOT EXISTS rooms (
        id INT PRIMARY KEY AUTO_INCREMENT,
        room_number VARCHAR(20) UNIQUE NOT NULL,
        room_type VARCHAR(50),
        price DECIMAL(10,2) NOT NULL DEFAULT 0,
        status VARCHAR(20) NOT NULL DEFAULT 'available',
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB
    """,

    # customers
    """
    CREATE TABLE IF NOT EXISTS customers (
        id INT PRIMARY KEY AUTO_INCREMENT,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        phone VARCHAR(50),
        email VARCHAR(255),
        address TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB
    """,

    # bookings
    """
    CREATE TABLE IF NOT EXISTS bookings (
        id INT PRIMARY KEY AUTO_INCREMENT,
        customer_id INT NOT NULL,
        room_id INT NOT NULL,
        checkin DATETIME,
        checkout DATETIME,
        status VARCHAR(30) DEFAULT 'reserved',
        total DECIMAL(12,2) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
    ) ENGINE=InnoDB
    """,

    # services (room service, laundry, etc.)
    """
    CREATE TABLE IF NOT EXISTS services (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(200) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB
    """,

    # booking_services (many-to-many)
    """
    CREATE TABLE IF NOT EXISTS booking_services (
        id INT PRIMARY KEY AUTO_INCREMENT,
        booking_id INT NOT NULL,
        service_id INT NOT NULL,
        quantity INT DEFAULT 1,
        subtotal DECIMAL(12,2) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
        FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
    ) ENGINE=InnoDB
    """,

    # invoices/payments
    """
    CREATE TABLE IF NOT EXISTS invoices (
        id INT PRIMARY KEY AUTO_INCREMENT,
        booking_id INT NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        paid DECIMAL(12,2) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'unpaid',
        issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
    ) ENGINE=InnoDB
    """,

    """
    CREATE TABLE IF NOT EXISTS payments (
        id INT PRIMARY KEY AUTO_INCREMENT,
        invoice_id INT NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        method VARCHAR(50),
        paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        note TEXT,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    ) ENGINE=InnoDB
    """,

    # staff
    """
    CREATE TABLE IF NOT EXISTS staff (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(200),
        role VARCHAR(100),
        phone VARCHAR(50),
        email VARCHAR(255),
        hire_date DATE,
        active TINYINT(1) DEFAULT 1
    ) ENGINE=InnoDB
    """,

    # inventory
    """
    CREATE TABLE IF NOT EXISTS inventory (
        id INT PRIMARY KEY AUTO_INCREMENT,
        item VARCHAR(200),
        quantity INT DEFAULT 0,
        unit VARCHAR(50),
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB
    """,

    # audit logs
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        type VARCHAR(50),
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB
    """
]


def initialize_schema():
    """Create the database (if allowed) and schema tables. This function is verbose and safe.

    It will attempt to connect to MySQL and create the database if it does not exist. If the
    DB user does not have CREATE DATABASE privileges, the function will report a clear error.
    """
    # Attempt to connect without database to create one if missing
    host = DB_CONFIG['host']
    user = DB_CONFIG['user']
    password = DB_CONFIG['password']
    dbname = DB_CONFIG['database']

    try:
        conn = mysql.connector.connect(host=host, user=user, password=password)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` DEFAULT CHARACTER SET 'utf8' ")
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Unable to create or access database: {e}")

    # Now run schema statements using DB.execute to get uniform error handling
    for sql in SCHEMA_SQL:
        try:
            DB.execute(sql, commit=True)
        except RuntimeError as e:
            print(f"[Warning] Could not run schema SQL: {e}")

    # Insert hotel metadata if not present
    try:
        existing = DB.execute("SELECT COUNT(*) AS c FROM hotels", fetchone=True)
        if existing and existing.get('c', 0) == 0:
            DB.execute(
                "INSERT INTO hotels (name, address, phone) VALUES (%s, %s, %s)",
                params=("Mafwbh Inn", "DPS Panipat Refinery, Panipat", "+91-XXXXXXXXXX"),
                commit=True
            )
    except Exception:
        # Non-fatal; schema exists but hotels table may be empty or inaccessible
        pass

    print('Schema initialization complete.')

# ----------------------------- Core Business Logic -----------------------------

# Each of the following functions provide a specific feature. They all use DB.execute and
# include exception handling so small input mistakes or DB errors do not kill the program.

# ------- Rooms Management -------

def add_room():
    try:
        number = safe_input('Room number (e.g., 101A): ').strip()
        if not number:
            print('Cancelled: empty room number.')
            return
        rtype = safe_input('Room type (single/double/deluxe/suite): ').strip() or 'standard'
        price_raw = safe_input('Price per night: ').strip()
        try:
            price = float(price_raw)
        except ValueError:
            print('Invalid price. Operation cancelled.')
            return
        desc = safe_input('Description (optional): ')
        DB.execute(
            'INSERT INTO rooms (room_number, room_type, price, description) VALUES (%s,%s,%s,%s)',
            params=(number, rtype, price, desc),
            commit=True
        )
        DB.execute("INSERT INTO audit_logs (type, message) VALUES (%s,%s)", commit=True,
                   params=('room_add', f'Added room {number}'))
        print('Room added successfully.')
    except RuntimeError as e:
        print('Error adding room:', e)
    except Exception as e:
        print('Unexpected error while adding room:', e)


def list_rooms(verbose=True):
    try:
        rows = DB.execute('SELECT * FROM rooms ORDER BY room_number', fetchall=True)
        if not rows:
            print('No rooms defined yet.')
            return []
        if verbose:
            print('\nRooms:')
            for r in rows:
                print(f"ID:{r['id']} No:{r['room_number']} Type:{r['room_type']} Price:{format_currency(r['price'])} Status:{r['status']}")
        return rows
    except RuntimeError as e:
        print('Error listing rooms:', e)
        return []


def update_room():
    try:
        rows = list_rooms()
        if not rows:
            return
        rid_raw = safe_input('Enter room ID to update: ').strip()
        try:
            rid = int(rid_raw)
        except ValueError:
            print('Invalid ID.')
            return
        room = DB.execute('SELECT * FROM rooms WHERE id=%s', params=(rid,), fetchone=True)
        if not room:
            print('Room not found.')
            return
        new_number = safe_input(f"Room number [{room['room_number']}]: ") or room['room_number']
        new_type = safe_input(f"Room type [{room['room_type']}]: ") or room['room_type']
        new_price_raw = safe_input(f"Price [{room['price']}]: ") or str(room['price'])
        try:
            new_price = float(new_price_raw)
        except ValueError:
            print('Invalid price. Aborting update.')
            return
        new_status = safe_input(f"Status [{room['status']}]: ") or room['status']
        new_desc = safe_input('Description (leave empty to keep existing): ') or room['description']
        DB.execute(
            'UPDATE rooms SET room_number=%s, room_type=%s, price=%s, status=%s, description=%s WHERE id=%s',
            params=(new_number, new_type, new_price, new_status, new_desc, rid),
            commit=True
        )
        print('Room updated.')
    except RuntimeError as e:
        print('Error updating room:', e)
    except Exception as e:
        print('Unexpected error while updating room:', e)


def remove_room():
    try:
        rows = list_rooms()
        if not rows:
            return
        rid_raw = safe_input('Enter room ID to delete: ').strip()
        try:
            rid = int(rid_raw)
        except ValueError:
            print('Invalid ID.')
            return
        if not confirm('This will permanently delete the room. Continue? (y/n): '):
            print('Deletion cancelled.')
            return
        DB.execute('DELETE FROM rooms WHERE id=%s', params=(rid,), commit=True)
        print('Room deleted.')
    except RuntimeError as e:
        print('Error deleting room:', e)
    except Exception as e:
        print('Unexpected error while deleting room:', e)

# ------- Customer Management -------


def create_customer_interactive():
    try:
        fname = safe_input('First name: ').strip()
        if not fname:
            print('First name required.')
            return
        lname = safe_input('Last name: ').strip()
        phone = safe_input('Phone: ').strip()
        email = safe_input('Email: ').strip()
        addr = safe_input('Address: ').strip()
        DB.execute(
            'INSERT INTO customers (first_name, last_name, phone, email, address) VALUES (%s,%s,%s,%s,%s)',
            params=(fname, lname, phone, email, addr),
            commit=True
        )
        print('Customer created.')
    except RuntimeError as e:
        print('Error creating customer:', e)
    except Exception as e:
        print('Unexpected error while creating customer:', e)


def list_customers():
    try:
        rows = DB.execute('SELECT * FROM customers ORDER BY created_at DESC', fetchall=True)
        if not rows:
            print('No customers found.')
            return []
        print('\nCustomers:')
        for c in rows:
            print(f"ID:{c['id']} {c['first_name']} {c['last_name']} Phone:{c['phone']} Email:{c['email']}")
        return rows
    except RuntimeError as e:
        print('Error listing customers:', e)
        return []

# ------- Bookings & Check-in/out -------


def create_booking_interactive():
    try:
        # Select or create customer
        print('\nSelect customer or create new:')
        customers = list_customers()
        customer_id = None
        if customers:
            sel = safe_input('Enter customer ID to use or press Enter to create new: ').strip()
            if sel:
                try:
                    customer_id = int(sel)
                except ValueError:
                    print('Invalid ID. Aborting booking.')
                    return
        if not customer_id:
            create_customer_interactive()
            # get last inserted customer
            latest = DB.execute('SELECT id FROM customers ORDER BY id DESC LIMIT 1', fetchone=True)
            if not latest:
                print('Failed to create customer.')
                return
            customer_id = latest['id']

        # Choose room
        available_rooms = DB.execute("SELECT * FROM rooms WHERE status='available' ORDER BY room_number", fetchall=True)
        if not available_rooms:
            print('No available rooms. Please add rooms or change status.')
            return
        print('\nAvailable rooms:')
        for r in available_rooms:
            print(f"ID:{r['id']} No:{r['room_number']} Type:{r['room_type']} Price:{format_currency(r['price'])}")
        rid_raw = safe_input('Enter room ID to book: ').strip()
        try:
            rid = int(rid_raw)
        except ValueError:
            print('Invalid room ID')
            return
        room = DB.execute('SELECT * FROM rooms WHERE id=%s', params=(rid,), fetchone=True)
        if not room or room['status'] != 'available':
            print('Selected room not available.')
            return

        # Dates
        checkin_raw = safe_input('Check-in date & time (YYYY-MM-DD HH:MM) or leave blank for now: ').strip()
        checkout_raw = safe_input('Check-out date & time (YYYY-MM-DD HH:MM) or leave blank for now: ').strip()
        checkin = None
        checkout = None
        try:
            if checkin_raw:
                checkin = datetime.strptime(checkin_raw, '%Y-%m-%d %H:%M')
            if checkout_raw:
                checkout = datetime.strptime(checkout_raw, '%Y-%m-%d %H:%M')
        except ValueError:
            print('Invalid date format. Use YYYY-MM-DD HH:MM')
            return

        # Calculate a base total if dates provided
        total = 0
        if checkin and checkout:
            nights = (checkout - checkin).days or 1
            total = float(room['price']) * nights
        else:
            total = float(room['price'])

        DB.execute(
            'INSERT INTO bookings (customer_id, room_id, checkin, checkout, total, status) VALUES (%s,%s,%s,%s,%s,%s)',
            params=(customer_id, rid, checkin, checkout, total, 'reserved'),
            commit=True
        )
        # Mark room as reserved
        DB.execute('UPDATE rooms SET status=%s WHERE id=%s', params=('reserved', rid), commit=True)
        print('Booking created successfully.')
    except RuntimeError as e:
        print('Error creating booking:', e)
    except Exception as e:
        print('Unexpected error while creating booking:', e)


def list_bookings():
    try:
        rows = DB.execute('''
            SELECT b.*, c.first_name, c.last_name, r.room_number FROM bookings b
            JOIN customers c ON c.id=b.customer_id
            JOIN rooms r ON r.id=b.room_id
            ORDER BY b.created_at DESC
        ''', fetchall=True)
        if not rows:
            print('No bookings found.')
            return []
        print('\nBookings:')
        for b in rows:
            ci = b['checkin'].strftime('%Y-%m-%d %H:%M') if b['checkin'] else 'N/A'
            co = b['checkout'].strftime('%Y-%m-%d %H:%M') if b['checkout'] else 'N/A'
            print(f"ID:{b['id']} Guest:{b['first_name']} {b['last_name']} Room:{b['room_number']} Check-in:{ci} Check-out:{co} Status:{b['status']} Total:{format_currency(b['total'])}")
        return rows
    except RuntimeError as e:
        print('Error listing bookings:', e)
        return []
    except Exception as e:
        print('Unexpected error while listing bookings:', e)
        return []


def check_in():
    try:
        rows = DB.execute("SELECT b.*, c.first_name, c.last_name, r.room_number, r.price FROM bookings b JOIN customers c ON c.id=b.customer_id JOIN rooms r ON r.id=b.room_id WHERE b.status IN ('reserved') ORDER BY b.created_at", fetchall=True)
        if not rows:
            print('No reservations ready for check-in.')
            return
        print('Reservations ready for check-in:')
        for b in rows:
            print(f"ID:{b['id']} Guest:{b['first_name']} {b['last_name']} Room:{b['room_number']}")
        bid_raw = safe_input('Enter booking ID to check in: ').strip()
        try:
            bid = int(bid_raw)
        except ValueError:
            print('Invalid booking ID')
            return
        booking = DB.execute('SELECT * FROM bookings WHERE id=%s', params=(bid,), fetchone=True)
        if not booking:
            print('Booking not found.')
            return
        # Update status and maybe set checkin time
        now = datetime.now()
        DB.execute('UPDATE bookings SET status=%s, checkin=%s WHERE id=%s', params=('checked_in', now, bid), commit=True)
        DB.execute('UPDATE rooms SET status=%s WHERE id=%s', params=('occupied', booking['room_id']), commit=True)
        print('Checked in successfully.')
    except RuntimeError as e:
        print('Error during check-in:', e)
    except Exception as e:
        print('Unexpected error during check-in:', e)


def check_out():
    try:
        rows = DB.execute("SELECT b.*, c.first_name, c.last_name, r.room_number, r.price FROM bookings b JOIN customers c ON c.id=b.customer_id JOIN rooms r ON r.id=b.room_id WHERE b.status IN ('checked_in') ORDER BY b.created_at", fetchall=True)
        if not rows:
            print('No checked-in guests found.')
            return
        print('Checked-in bookings:')
        for b in rows:
            print(f"ID:{b['id']} Guest:{b['first_name']} {b['last_name']} Room:{b['room_number']}")
        bid_raw = safe_input('Enter booking ID to check out: ').strip()
        try:
            bid = int(bid_raw)
        except ValueError:
            print('Invalid booking ID')
            return
        booking = DB.execute('SELECT b.*, r.price FROM bookings b JOIN rooms r ON r.id=b.room_id WHERE b.id=%s', params=(bid,), fetchone=True)
        if not booking:
            print('Booking not found.')
            return
        # Determine checkout time and total
        now = datetime.now()
        checkin = booking['checkin'] or now
        # Very simple billing: days stayed * price + services
        nights = max(1, (now.date() - checkin.date()).days)
        base_total = float(booking['price']) * nights if booking.get('price') else float(booking['total'] or 0)
        # Sum services
        services = DB.execute('SELECT SUM(subtotal) AS s FROM booking_services WHERE booking_id=%s', params=(bid,), fetchone=True)
        service_total = float(services['s']) if services and services.get('s') else 0
        final_total = base_total + service_total
        # Create invoice
        DB.execute('INSERT INTO invoices (booking_id, amount, paid, status) VALUES (%s,%s,%s,%s)', params=(bid, final_total, 0, 'unpaid'), commit=True)
        # Update booking
        DB.execute('UPDATE bookings SET status=%s, checkout=%s, total=%s WHERE id=%s', params=('checked_out', now, final_total, bid), commit=True)
        DB.execute('UPDATE rooms SET status=%s WHERE id=%s', params=('available', booking['room_id']), commit=True)
        print(f'Checked out. Total due: {format_currency(final_total)}')
    except RuntimeError as e:
        print('Error during check-out:', e)
    except Exception as e:
        print('Unexpected error during check-out:', e)


# ------- Services & Add-ons -------


def add_service():
    try:
        name = safe_input('Service name (e.g., Laundry): ').strip()
        if not name:
            print('Service name required.')
            return
        price_raw = safe_input('Price: ').strip()
        try:
            price = float(price_raw)
        except ValueError:
            print('Invalid price.')
            return
        DB.execute('INSERT INTO services (name, price) VALUES (%s,%s)', params=(name, price), commit=True)
        print('Service added.')
    except RuntimeError as e:
        print('Error adding service:', e)
    except Exception as e:
        print('Unexpected error:', e)


def list_services():
    try:
        rows = DB.execute('SELECT * FROM services ORDER BY name', fetchall=True)
        if not rows:
            print('No services defined.')
            return []
        for s in rows:
            print(f"ID:{s['id']} {s['name']} Price:{format_currency(s['price'])}")
        return rows
    except RuntimeError as e:
        print('Error listing services:', e)
        return []


def attach_service_to_booking():
    try:
        bookings = list_bookings()
        if not bookings:
            return
        bid_raw = safe_input('Booking ID to attach service to: ').strip()
        try:
            bid = int(bid_raw)
        except ValueError:
            print('Invalid booking ID.')
            return
        services = list_services()
        if not services:
            return
        sid_raw = safe_input('Service ID: ').strip()
        try:
            sid = int(sid_raw)
        except ValueError:
            print('Invalid service ID.')
            return
        qty_raw = safe_input('Quantity: ').strip()
        try:
            qty = int(qty_raw)
        except ValueError:
            print('Invalid quantity. Using 1')
            qty = 1
        service = DB.execute('SELECT * FROM services WHERE id=%s', params=(sid,), fetchone=True)
        if not service:
            print('Service not found.')
            return
        subtotal = float(service['price']) * qty
        DB.execute('INSERT INTO booking_services (booking_id, service_id, quantity, subtotal) VALUES (%s,%s,%s,%s)', params=(bid, sid, qty, subtotal), commit=True)
        print('Service attached to booking.')
    except RuntimeError as e:
        print('Error attaching service:', e)
    except Exception as e:
        print('Unexpected error attaching service:', e)

# ------- Finance: Invoice & Payments -------


def list_invoices():
    try:
        rows = DB.execute('''
            SELECT inv.*, b.id AS booking_ref, c.first_name, c.last_name FROM invoices inv
            JOIN bookings b ON b.id=inv.booking_id
            JOIN customers c ON c.id=b.customer_id
            ORDER BY inv.issued_at DESC
        ''', fetchall=True)
        if not rows:
            print('No invoices found.')
            return []
        for inv in rows:
            print(f"ID:{inv['id']} Booking:{inv['booking_ref']} Amount:{format_currency(inv['amount'])} Paid:{format_currency(inv['paid'])} Status:{inv['status']}")
        return rows
    except RuntimeError as e:
        print('Error listing invoices:', e)
        return []


def record_payment_interactive():
    try:
        invoices = list_invoices()
        if not invoices:
            return
        iid_raw = safe_input('Enter invoice ID to pay against: ').strip()
        try:
            iid = int(iid_raw)
        except ValueError:
            print('Invalid ID.')
            return
        invoice = DB.execute('SELECT * FROM invoices WHERE id=%s', params=(iid,), fetchone=True)
        if not invoice:
            print('Invoice not found.')
            return
        due = float(invoice['amount']) - float(invoice['paid'])
        print(f'Amount due: {format_currency(due)}')
        amt_raw = safe_input('Payment amount: ').strip()
        try:
            amt = float(amt_raw)
        except ValueError:
            print('Invalid amount.')
            return
        if amt <= 0:
            print('Payment must be positive.')
            return
        method = safe_input('Payment method (cash/card/upi): ').strip() or 'cash'
        note = safe_input('Note (optional): ')
        DB.execute('INSERT INTO payments (invoice_id, amount, method, note) VALUES (%s,%s,%s,%s)', params=(iid, amt, method, note), commit=True)
        # Update invoice paid amount and status
        new_paid = float(invoice['paid']) + amt
        new_status = 'paid' if new_paid >= float(invoice['amount']) else 'partially_paid'
        DB.execute('UPDATE invoices SET paid=%s, status=%s WHERE id=%s', params=(new_paid, new_status, iid), commit=True)
        print('Payment recorded.')
    except RuntimeError as e:
        print('Error recording payment:', e)
    except Exception as e:
        print('Unexpected error while recording payment:', e)

# ------- Inventory & Staff -------


def add_inventory_item():
    try:
        item = safe_input('Item name: ').strip()
        if not item:
            print('Item name required.')
            return
        qty_raw = safe_input('Quantity: ').strip()
        try:
            qty = int(qty_raw)
        except ValueError:
            print('Invalid quantity. Use integer.')
            return
        unit = safe_input('Unit (pcs/kg/ltrs): ').strip() or 'pcs'
        DB.execute('INSERT INTO inventory (item, quantity, unit) VALUES (%s,%s,%s)', params=(item, qty, unit), commit=True)
        print('Inventory item added.')
    except RuntimeError as e:
        print('Error adding inventory:', e)
    except Exception as e:
        print('Unexpected error adding inventory:', e)


def list_inventory():
    try:
        rows = DB.execute('SELECT * FROM inventory ORDER BY item', fetchall=True)
        if not rows:
            print('Inventory is empty.')
            return []
        for it in rows:
            print(f"ID:{it['id']} Item:{it['item']} Qty:{it['quantity']} {it['unit']}")
        return rows
    except RuntimeError as e:
        print('Error listing inventory:', e)
        return []


def add_staff():
    try:
        name = safe_input('Staff name: ').strip()
        role = safe_input('Role: ').strip()
        phone = safe_input('Phone: ').strip()
        email = safe_input('Email: ').strip()
        hire_date_raw = safe_input('Hire date (YYYY-MM-DD): ').strip()
        hire_date = None
        if hire_date_raw:
            try:
                hire_date = datetime.strptime(hire_date_raw, '%Y-%m-%d').date()
            except ValueError:
                print('Invalid date. Leaving blank.')
                hire_date = None
        DB.execute('INSERT INTO staff (name, role, phone, email, hire_date) VALUES (%s,%s,%s,%s,%s)', params=(name, role, phone, email, hire_date), commit=True)
        print('Staff added.')
    except RuntimeError as e:
        print('Error adding staff:', e)
    except Exception as e:
        print('Unexpected error adding staff:', e)


def list_staff():
    try:
        rows = DB.execute('SELECT * FROM staff ORDER BY active DESC, name', fetchall=True)
        if not rows:
            print('No staff records.')
            return []
        for s in rows:
            print(f"ID:{s['id']} {s['name']} Role:{s['role']} Active:{bool(s['active'])}")
        return rows
    except RuntimeError as e:
        print('Error listing staff:', e)
        return []

# ------- Reports & Analytics -------


def occupancy_report():
    try:
        total_rooms = DB.execute('SELECT COUNT(*) AS c FROM rooms', fetchone=True)['c']
        occupied = DB.execute("SELECT COUNT(*) AS c FROM rooms WHERE status='occupied'", fetchone=True)['c']
        reserved = DB.execute("SELECT COUNT(*) AS c FROM rooms WHERE status='reserved'", fetchone=True)['c']
        available = DB.execute("SELECT COUNT(*) AS c FROM rooms WHERE status='available'", fetchone=True)['c']
        print(f"Rooms total: {total_rooms} Occupied: {occupied} Reserved: {reserved} Available: {available}")
    except Exception as e:
        print('Error generating occupancy report:', e)


def revenue_report():
    try:
        # Revenue by day for last 30 days
        end = datetime.now().date()
        start = end - timedelta(days=30)
        rows = DB.execute(
            "SELECT DATE(p.paid_at) AS dt, SUM(p.amount) AS revenue FROM payments p WHERE p.paid_at BETWEEN %s AND %s GROUP BY DATE(p.paid_at) ORDER BY dt",
            params=(start, end), fetchall=True)
        if not rows:
            print('No payments in last 30 days.')
            return
        print('\nRevenue (last 30 days):')
        for r in rows:
            print(f"{r['dt']}: {format_currency(r['revenue'])}")
    except Exception as e:
        print('Error generating revenue report:', e)


def booking_summary_report():
    try:
        rows = DB.execute('SELECT status, COUNT(*) AS c FROM bookings GROUP BY status', fetchall=True)
        if not rows:
            print('No bookings to report.')
            return
        print('\nBooking summary:')
        for r in rows:
            print(f"{r['status']}: {r['c']}")
    except Exception as e:
        print('Error generating booking summary report:', e)

# ------- Backup & Restore (SQL dump) -------


def backup_database_to_file(filepath=None):
    """Simple SQL SELECT dump. Not a full mysqldump replacement but suitable for classroom projects.

    The function writes INSERT statements for main tables. If mysqldump is available, the user is
    advised to use it for production backups.
    """
    try:
        if not filepath:
            filepath = f"mafwbh_inn_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('-- Mafwbh Inn backup\n')
            f.write('-- Generated: %s\n\n' % datetime.now().isoformat())
            # Export tables in order
            tables = ['hotels','rooms','customers','bookings','services','booking_services','invoices','payments','staff','inventory','audit_logs']
            for t in tables:
                rows = DB.execute(f'SELECT * FROM {t}', fetchall=True)
                if not rows:
                    continue
                # Create simple INSERTs
                for row in rows:
                    cols = ', '.join([f'`{k}`' for k in row.keys()])
                    vals = ', '.join([DB_format_value(v) for v in row.values()])
                    f.write(f'INSERT INTO `{t}` ({cols}) VALUES ({vals});\n')
            print(f'Backup written to {filepath}')
    except Exception as e:
        print('Error creating backup:', e)


def DB_format_value(v):
    if v is None:
        return 'NULL'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, datetime):
        return f"'{v.strftime('%Y-%m-%d %H:%M:%S')}'"
    # Escape single quotes
    s = str(v).replace("'", "''")
    return f"'{s}'"


def restore_from_backup(filepath):
    try:
        if not os.path.exists(filepath):
            print('File not found.')
            return
        sql = open(filepath, 'r', encoding='utf-8').read()
        # Naive splitting; okay for this simple dump format
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        for stmt in statements:
            try:
                DB.execute(stmt, commit=True)
            except Exception as e:
                print(f'Warning: failed to run statement: {e}')
        print('Restore attempted. Review warnings above for failed statements.')
    except Exception as e:
        print('Error during restore:', e)

# ------- Helper / Utility Functions for reports and testing -------


def import_sample_data():
    """Populate the database with sample rooms, services and a few customers/bookings for demo.

    This helps when printing the project to show populated reports and features.
    """
    try:
        sample_rooms = [
            ('101', 'single', 1500.00, 'Cozy single bed'),
            ('102', 'double', 2500.00, 'Double bed with city view'),
            ('201', 'deluxe', 4000.00, 'Deluxe room with AC'),
            ('301', 'suite', 8000.00, 'Executive suite with living area')
        ]
        for r in sample_rooms:
            try:
                DB.execute('INSERT INTO rooms (room_number, room_type, price, description) VALUES (%s,%s,%s,%s)', params=r, commit=True)
            except Exception:
                pass
        sample_services = [('Laundry', 150.00), ('Breakfast', 250.00), ('Airport Pickup', 800.00)]
        for s in sample_services:
            try:
                DB.execute('INSERT INTO services (name, price) VALUES (%s,%s)', params=s, commit=True)
            except Exception:
                pass
        # sample customers
        try:
            DB.execute("INSERT INTO customers (first_name, last_name, phone, email, address) VALUES ('Test', 'Guest', '9999999999', 'test@example.com', 'NA')", commit=True)
        except Exception:
            pass
        print('Sample data import attempted. Some items may already exist; duplicate inserts skipped.')
    except Exception as e:
        print('Error importing sample data:', e)

# ----------------------------- Menu System -----------------------------

MENU_HEADER = 'Mafwbh Inn - Hotel Management System (Authors: Ayush Samanta & Sanshubh Kanaujia)'


def rooms_menu():
    while True:
        print('\n--- Rooms Management ---')
        print('1. List rooms')
        print('2. Add room')
        print('3. Update room')
        print('4. Remove room')
        print('5. Back')
        choice = safe_input('Choice: ').strip()
        try:
            if choice == '1':
                list_rooms()
            elif choice == '2':
                add_room()
            elif choice == '3':
                update_room()
            elif choice == '4':
                remove_room()
            elif choice == '5' or choice.lower() in ('b','back'):
                break
            else:
                print('Invalid choice.')
        except Exception as e:
            print('Error in rooms menu:', e)


def customers_menu():
    while True:
        print('\n--- Customer Management ---')
        print('1. List customers')
        print('2. Create customer')
        print('3. Back')
        choice = safe_input('Choice: ').strip()
        try:
            if choice == '1':
                list_customers()
            elif choice == '2':
                create_customer_interactive()
            elif choice in ('3','b','back'):
                break
            else:
                print('Invalid choice.')
        except Exception as e:
            print('Error in customers menu:', e)


def bookings_menu():
    while True:
        print('\n--- Bookings & Front Desk ---')
        print('1. List bookings')
        print('2. Create booking')
        print('3. Check-in')
        print('4. Check-out')
        print('5. Attach service to booking')
        print('6. Back')
        choice = safe_input('Choice: ').strip()
        try:
            if choice == '1':
                list_bookings()
            elif choice == '2':
                create_booking_interactive()
            elif choice == '3':
                check_in()
            elif choice == '4':
                check_out()
            elif choice == '5':
                attach_service_to_booking()
            elif choice in ('6','b','back'):
                break
            else:
                print('Invalid choice.')
        except Exception as e:
            print('Error in bookings menu:', e)


def services_menu():
    while True:
        print('\n--- Services & Add-ons ---')
        print('1. List services')
        print('2. Add service')
        print('3. Attach service to booking')
        print('4. Back')
        c = safe_input('Choice: ').strip()
        try:
            if c == '1':
                list_services()
            elif c == '2':
                add_service()
            elif c == '3':
                attach_service_to_booking()
            elif c in ('4','b','back'):
                break
            else:
                print('Invalid choice.')
        except Exception as e:
            print('Error in services menu:', e)


def finance_menu():
    while True:
        print('\n--- Finance ---')
        print('1. List invoices')
        print('2. Record payment')
        print('3. Back')
        c = safe_input('Choice: ').strip()
        try:
            if c == '1':
                list_invoices()
            elif c == '2':
                record_payment_interactive()
            elif c in ('3','b','back'):
                break
            else:
                print('Invalid choice.')
        except Exception as e:
            print('Error in finance menu:', e)


def operations_menu():
    while True:
        print('\n--- Operations & Reports ---')
        print('1. Occupancy report')
        print('2. Revenue report')
        print('3. Booking summary')
        print('4. Backup database')
        print('5. Restore database from file')
        print('6. Import sample data')
        print('7. Back')
        c = safe_input('Choice: ').strip()
        try:
            if c == '1':
                occupancy_report()
            elif c == '2':
                revenue_report()
            elif c == '3':
                booking_summary_report()
            elif c == '4':
                path = safe_input('Enter file path for backup or Leave blank for default: ').strip() or None
                backup_database_to_file(path)
            elif c == '5':
                p = safe_input('Filepath to restore from: ').strip()
                restore_from_backup(p)
            elif c == '6':
                import_sample_data()
            elif c in ('7','b','back'):
                break
            else:
                print('Invalid choice.')
        except Exception as e:
            print('Error in operations menu:', e)


def staff_inventory_menu():
    while True:
        print('\n--- Staff & Inventory ---')
        print('1. List staff')
        print('2. Add staff')
        print('3. List inventory')
        print('4. Add inventory item')
        print('5. Back')
        c = safe_input('Choice: ').strip()
        try:
            if c == '1':
                list_staff()
            elif c == '2':
                add_staff()
            elif c == '3':
                list_inventory()
            elif c == '4':
                add_inventory_item()
            elif c in ('5','b','back'):
                break
            else:
                print('Invalid choice.')
        except Exception as e:
            print('Error in staff/inventory menu:', e)

# ----------------------------- Main Program Loop -----------------------------


def main_menu():
    while True:
        print('\n' + '='*80)
        print(MENU_HEADER)
        print('='*80)
        print('1. Rooms Management')
        print('2. Customer Management')
        print('3. Bookings & Front Desk')
        print('4. Services & Add-ons')
        print('5. Finance')
        print('6. Staff & Inventory')
        print('7. Operations & Reports')
        print('8. Initialize / Create Schema')
        print('9. Exit')
        choice = safe_input('Select option: ').strip()
        try:
            if choice == '1':
                rooms_menu()
            elif choice == '2':
                customers_menu()
            elif choice == '3':
                bookings_menu()
            elif choice == '4':
                services_menu()
            elif choice == '5':
                finance_menu()
            elif choice == '6':
                staff_inventory_menu()
            elif choice == '7':
                operations_menu()
            elif choice == '8':
                try:
                    initialize_schema()
                except Exception as e:
                    print('Initialization error:', e)
            elif choice == '9' or choice.lower() in ('q','quit','exit'):
                print('Exiting.')
                break
            else:
                print('Invalid selection.')
        except Exception as e:
            print('Unexpected error in main menu:', e)


if __name__ == '__main__':
    # The program will run in the terminal. Minimal startup logic here.
    try:
        print(MENU_HEADER)
        print('Note: you may need to configure DB credentials at top of file before first run.')
        main_menu()
    except Exception as e:
        print('Fatal error:', e)
        sys.exit(1)
