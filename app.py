from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key")
DB_NAME = "/tmp/users.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # password stored as TEXT (plain)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                        (username, password))   # storing plain text
            conn.commit()
            conn.close()
            flash("Registered. Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()

        # plain text compare
        if user and user["password"] == password:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
init_db()
if __name__ == "__main__":
   
    app.run(debug=True)


