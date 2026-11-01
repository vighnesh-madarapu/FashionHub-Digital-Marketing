
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db_connection, init_db
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "fashionhub-demo-secret-change-before-deployment"

# Initialize database
init_db()


# LOGIN PROTECTION
def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper


# HOME PAGE
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# SIGN UP PAGE
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password or not confirm_password:
            flash("Please fill in all fields.", "danger")
            return render_template("signup.html")

        if len(username) < 3:
            flash("Username must contain at least 3 characters.", "danger")
            return render_template("signup.html")

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return render_template("signup.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("signup.html")

        connection = get_db_connection()

        try:
            connection.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """,
                (username, generate_password_hash(password))
            )
            connection.commit()

            flash("Account created successfully! Please sign in.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Username already exists. Choose another one.", "danger")

        finally:
            connection.close()

    return render_template("signup.html")


# LOGIN PAGE
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = get_db_connection()
        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        connection.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    connection = get_db_connection()

    products = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    customers = connection.execute(
        "SELECT COUNT(*) FROM customers"
    ).fetchone()[0]

    campaigns = connection.execute(
        "SELECT COUNT(*) FROM campaigns"
    ).fetchone()[0]

    revenue = connection.execute(
        "SELECT COALESCE(SUM(total_amount), 0) FROM sales"
    ).fetchone()[0]

    recent_sales = connection.execute("""
        SELECT sales.*, products.name AS product_name
        FROM sales
        LEFT JOIN products ON sales.product_id = products.id
        ORDER BY sales.id DESC
        LIMIT 5
    """).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        products=products,
        customers=customers,
        campaigns=campaigns,
        revenue=revenue,
        recent_sales=recent_sales
    )


# PRODUCTS - VIEW
@app.route("/products")
@login_required
def products():
    connection = get_db_connection()

    data = connection.execute(
        "SELECT * FROM products ORDER BY id ASC"
    ).fetchall()

    connection.close()

    return render_template("products.html", products=data)


# PRODUCTS - ADD
@app.route("/products/add", methods=["POST"])
@login_required
def add_product():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "").strip()
    stock = request.form.get("stock", "").strip()

    if not name or not category or not price or not stock:
        flash("Please fill in all product details.", "warning")
        return redirect(url_for("products"))

    try:
        price = float(price)
        stock = int(stock)

        if price < 0 or stock < 0:
            raise ValueError

        connection = get_db_connection()
        connection.execute("""
            INSERT INTO products (name, category, price, stock)
            VALUES (?, ?, ?, ?)
        """, (name, category, price, stock))

        connection.commit()
        connection.close()

        flash("Product added successfully!", "success")

    except ValueError:
        flash("Enter a valid price and stock quantity.", "danger")

    return redirect(url_for("products"))


# CUSTOMERS - VIEW
@app.route("/customers")
@login_required
def customers():
    connection = get_db_connection()

    data = connection.execute(
        "SELECT * FROM customers ORDER BY id ASC"
    ).fetchall()

    connection.close()

    return render_template("customers.html", customers=data)


# CUSTOMERS - ADD
@app.route("/customers/add", methods=["POST"])
@login_required
def add_customer():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    city = request.form.get("city", "").strip()

    if not name or not email or not city:
        flash("Please fill in all customer details.", "warning")
        return redirect(url_for("customers"))

    connection = get_db_connection()

    try:
        connection.execute("""
            INSERT INTO customers (name, email, city)
            VALUES (?, ?, ?)
        """, (name, email, city))

        connection.commit()
        flash("Customer added successfully!", "success")

    except Exception:
        flash("This email may already exist. Please use another email.", "danger")

    finally:
        connection.close()

    return redirect(url_for("customers"))


# CUSTOMERS - EDIT
@app.route("/customers/edit/<int:customer_id>", methods=["POST"])
@login_required
def edit_customer(customer_id):
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    city = request.form.get("city", "").strip()

    if not name or not email or not city:
        flash("Please fill in all customer details.", "warning")
        return redirect(url_for("customers"))

    connection = get_db_connection()

    try:
        cursor = connection.execute("""
            UPDATE customers
            SET name = ?, email = ?, city = ?
            WHERE id = ?
        """, (name, email, city, customer_id))

        connection.commit()

        if cursor.rowcount == 0:
            flash("Customer not found.", "warning")
        else:
            flash("Customer updated successfully!", "success")

    except Exception:
        flash("This email may already be used by another customer.", "danger")

    finally:
        connection.close()

    return redirect(url_for("customers"))


# CUSTOMERS - DELETE
@app.route("/customers/delete/<int:customer_id>", methods=["POST"])
@login_required
def delete_customer(customer_id):
    connection = get_db_connection()

    sales = connection.execute(
        "SELECT COUNT(*) FROM sales WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]

    if sales > 0:
        connection.close()
        flash("This customer has sales records and cannot be deleted.", "warning")
        return redirect(url_for("customers"))

    connection.execute(
        "DELETE FROM customers WHERE id = ?",
        (customer_id,)
    )

    connection.commit()
    connection.close()

    flash("Customer deleted successfully!", "success")
    return redirect(url_for("customers"))


# MARKETING CAMPAIGNS
@app.route("/campaigns")
@login_required
def campaigns():
    connection = get_db_connection()

    data = connection.execute(
        "SELECT * FROM campaigns ORDER BY id ASC"
    ).fetchall()

    connection.close()

    return render_template("campaigns.html", campaigns=data)


# ANALYTICS AND MARKETING INSIGHTS
@app.route("/analytics")
@login_required
def analytics():
    connection = get_db_connection()

    campaign_data = connection.execute("""
        SELECT name, channel, budget, impressions, clicks,
               conversions, revenue, status
        FROM campaigns
        ORDER BY id ASC
    """).fetchall()

    sales_data = connection.execute("""
        SELECT sale_date, SUM(total_amount) AS revenue
        FROM sales
        GROUP BY sale_date
        ORDER BY sale_date ASC
    """).fetchall()

    connection.close()

    total_impressions = sum(c["impressions"] or 0 for c in campaign_data)
    total_clicks = sum(c["clicks"] or 0 for c in campaign_data)
    total_conversions = sum(c["conversions"] or 0 for c in campaign_data)
    total_revenue = sum(c["revenue"] or 0 for c in campaign_data)
    total_budget = sum(c["budget"] or 0 for c in campaign_data)

    ctr = (
        (total_clicks / total_impressions) * 100
        if total_impressions > 0 else 0
    )

    conversion_rate = (
        (total_conversions / total_clicks) * 100
        if total_clicks > 0 else 0
    )

    roas = (
        total_revenue / total_budget
        if total_budget > 0 else 0
    )

    best_campaign = max(
        campaign_data,
        key=lambda c: c["revenue"] or 0,
        default=None
    )

    recommendations = []

    if ctr < 2:
        recommendations.append(
            "Improve advertisement creatives and headlines to attract more clicks."
        )
    else:
        recommendations.append(
            "Your click-through rate is performing well. Continue testing creative variations."
        )

    if conversion_rate < 5:
        recommendations.append(
            "Improve product landing pages and simplify the checkout experience."
        )
    else:
        recommendations.append(
            "Your conversion rate is encouraging. Continue optimizing the customer journey."
        )

    if roas < 2:
        recommendations.append(
            "Review campaign budgets and focus on campaigns that generate better revenue."
        )
    else:
        recommendations.append(
            "Your advertising return is positive. Monitor campaign costs while scaling successful campaigns."
        )

    if best_campaign:
        recommendations.append(
            "Focus on learning from your best-performing campaign: "
            + best_campaign["name"] + "."
        )

    insights = {
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "total_revenue": total_revenue,
        "total_budget": total_budget,
        "ctr": round(ctr, 2),
        "conversion_rate": round(conversion_rate, 2),
        "roas": round(roas, 2),
        "best_campaign": best_campaign,
        "recommendations": recommendations
    }

    return render_template(
        "analytics.html",
        campaign_data=campaign_data,
        sales_data=sales_data,
        insights=insights
    )


# RUN APPLICATION
if __name__ == "__main__":
    app.run(debug=True)
