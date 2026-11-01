import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DATABASE = Path(__file__).with_name("fashionhub.db")


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # PRODUCTS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)

    # CUSTOMERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            city TEXT
        )
    """)

    # CAMPAIGNS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            channel TEXT,
            budget REAL DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            revenue REAL DEFAULT 0,
            status TEXT DEFAULT 'Active'
        )
    """)

    # SALES TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            customer_id INTEGER,
            quantity INTEGER,
            total_amount REAL,
            sale_date TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    """)

    # DEFAULT ADMIN LOGIN
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password_hash)
        VALUES (?, ?)
    """, (
        "admin",
        generate_password_hash("admin123")
    ))

    # SAMPLE PRODUCTS
    products = [
        ("Classic Cotton T-Shirt", "Men", 799, 45),
        ("Floral Summer Dress", "Women", 1499, 30),
        ("Denim Jacket", "Unisex", 1999, 20),
        ("Casual Hoodie", "Men", 1299, 35),
        ("Designer Kurti", "Women", 999, 25),
        ("Premium Jeans", "Men", 1799, 40),
        ("Traditional Saree", "Women", 2499, 15),
        ("Sports Wear", "Unisex", 1199, 28)
    ]

    for product in products:
        cursor.execute("""
            INSERT INTO products (name, category, price, stock)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM products WHERE name = ?
            )
        """, (*product, product[0]))

    # SAMPLE CUSTOMERS
    customers = [
        ("Rahul Sharma", "rahul@example.com", "Hyderabad"),
        ("Priya Reddy", "priya@example.com", "Vijayawada"),
        ("Arjun Kumar", "arjun@example.com", "Bengaluru"),
        ("Sneha Rao", "sneha@example.com", "Chennai"),
        ("Kiran Varma", "kiran@example.com", "Hyderabad"),
        ("Ananya Singh", "ananya@example.com", "Mumbai"),
        ("Rohit Das", "rohit@example.com", "Kolkata"),
        ("Meghana Rao", "meghana@example.com", "Vizag")
    ]

    for customer in customers:
        cursor.execute("""
            INSERT OR IGNORE INTO customers (name, email, city)
            VALUES (?, ?, ?)
        """, customer)

    # SAMPLE MARKETING CAMPAIGNS
    campaigns = [
        ("Summer Fashion Sale", "Instagram", 10000, 25000, 3200, 180, 45000, "Active"),
        ("Festive Collection", "Facebook", 15000, 40000, 5000, 250, 65000, "Active"),
        ("Winter Style Campaign", "Google Ads", 12000, 30000, 2800, 140, 38000, "Completed"),
        ("New Arrivals Promotion", "Instagram", 8000, 18000, 2100, 120, 29000, "Active"),
        ("Monsoon Fashion Offer", "YouTube", 9000, 22000, 2600, 150, 35000, "Active")
    ]

    for campaign in campaigns:
        cursor.execute("""
            INSERT INTO campaigns
            (name, channel, budget, impressions, clicks,
             conversions, revenue, status)
            SELECT ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM campaigns WHERE name = ?
            )
        """, (*campaign, campaign[0]))

    # SAMPLE SALES
    sample_sales = [
        (1, 1, 2, 1598, "2026-10-20"),
        (2, 2, 1, 1499, "2026-10-21"),
        (3, 3, 1, 1999, "2026-10-22"),
        (4, 4, 2, 2598, "2026-10-23"),
        (5, 5, 1, 999, "2026-10-24"),
        (6, 6, 2, 3598, "2026-10-25"),
        (7, 7, 1, 2499, "2026-10-26"),
        (8, 8, 1, 1199, "2026-10-27")
    ]

    for sale in sample_sales:
        cursor.execute("""
            INSERT INTO sales
            (product_id, customer_id, quantity, total_amount, sale_date)
            SELECT ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM sales WHERE sale_date = ?
            )
        """, (*sale, sale[4]))

    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_db()
    print("FashionHub database initialized successfully!")