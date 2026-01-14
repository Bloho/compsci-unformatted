import mysql.connector

# ================== DATABASE CONNECTION ==================

def get_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="YOUR_PASSWORD",
            database="railway_db"
        )
    except mysql.connector.Error as e:
        print("Database connection failed:", e)
        return None

# ================== DATABASE INITIALIZATION ==================

def initialize_database():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="YOUR_PASSWORD"
        )
        cursor = db.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS railway_db")
        cursor.close()
        db.close()
    except:
        print("Database initialization error")

def create_tables():
    db = get_connection()
    if db is None:
        return
    cursor = db.cursor()

    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS passengers (
            passenger_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            age INT,
            gender VARCHAR(10),
            phone VARCHAR(15)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trains (
            train_no INT PRIMARY KEY,
            train_name VARCHAR(100),
            source VARCHAR(50),
            destination VARCHAR(50)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INT AUTO_INCREMENT PRIMARY KEY,
            passenger_id INT,
            train_no INT,
            class VARCHAR(5),
            seat_no INT,
            status VARCHAR(20),
            FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS waiting_list (
            wait_id INT AUTO_INCREMENT PRIMARY KEY,
            passenger_id INT,
            train_no INT,
            class VARCHAR(5),
            wait_position INT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50),
            password VARCHAR(50)
        )
        """)

        db.commit()
    except:
        print("Error creating tables")

    cursor.close()
    db.close()

# ================== PASSENGER MODULE ==================

def add_passenger():
    try:
        name = input("Enter passenger name: ")
        age = int(input("Enter age: "))
        gender = input("Enter gender: ")
        phone = input("Enter phone: ")

        db = get_connection()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO passengers (name, age, gender, phone) VALUES (%s,%s,%s,%s)",
            (name, age, gender, phone)
        )
        db.commit()
        print("Passenger added successfully")

        cursor.close()
        db.close()
    except ValueError:
        print("Invalid age entered")
    except:
        print("Passenger insertion failed")

# ================== TRAIN MODULE ==================

def add_train():
    try:
        train_no = int(input("Train number: "))
        name = input("Train name: ")
        src = input("Source: ")
        dest = input("Destination: ")

        db = get_connection()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO trains VALUES (%s,%s,%s,%s)",
            (train_no, name, src, dest)
        )
        db.commit()
        print("Train added")

        cursor.close()
        db.close()
    except ValueError:
        print("Invalid train number")
    except:
        print("Train insertion failed")

# ================== TICKET BOOKING ==================

def book_ticket():
    try:
        pid = int(input("Passenger ID: "))
        train = int(input("Train No: "))
        cls = input("Class (SL/3A/2A/1A): ")

        seat = int(input("Seat number: "))

        db = get_connection()
        cursor = db.cursor()

        cursor.execute("""
        INSERT INTO tickets (passenger_id, train_no, class, seat_no, status)
        VALUES (%s,%s,%s,%s,'CONFIRMED')
        """, (pid, train, cls, seat))

        db.commit()
        print("Ticket booked")

        cursor.close()
        db.close()
    except ValueError:
        print("Invalid numeric input")
    except:
        print("Ticket booking failed")

# ================== MENUS ==================

def passenger_menu():
    while True:
        print("\nPassenger Menu")
        print("1. Add Passenger")
        print("2. Back")

        ch = input("Choice: ")
        if ch == '1':
            add_passenger()
        elif ch == '2':
            break
        else:
            print("Invalid choice")

def admin_menu():
    while True:
        print("\nAdmin Menu")
        print("1. Add Train")
        print("2. Book Ticket")
        print("3. Back")

        ch = input("Choice: ")
        if ch == '1':
            add_train()
        elif ch == '2':
            book_ticket()
        elif ch == '3':
            break
        else:
            print("Invalid choice")

# ================== MAIN ==================

def main_menu():
    initialize_database()
    create_tables()

    while True:
        print("\nRAILWAY MANAGEMENT SYSTEM")
        print("DPS Panipat Refinery")
        print("1. Passenger Section")
        print("2. Admin Section")
        print("3. Exit")

        choice = input("Enter choice: ")

        if choice == '1':
            passenger_menu()
        elif choice == '2':
            admin_menu()
        elif choice == '3':
            print("System terminated")
            break
        else:
            print("Invalid input")

main_menu()
