from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os
import sqlite3

app = Flask(__name__)
app.secret_key = "santa_secret_key_2026"

UPLOAD_FOLDER = 'static/uploads'
DB_PATH = 'santa_secret.db'
DEFAULT_MUSIC = "https://upload.wikimedia.org/wikipedia/commons/e/e4/Jingle_Bells_%28Kevin_MacLeod%29_%28ISRC_USUAN1100187%29.mp3"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "santa2026"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                login TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                wish TEXT DEFAULT 'Yangi yil sovg''asi',
                assignedTo INTEGER,
                match2 INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Boshlang'ich foydalanuvchilar (faqat baza bo'sh bo'lsa qo'shiladi)
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            initial_users = [
                ("Ali Valiyev", "ali", "ali123", "Kitob", None, None),
                ("Madina Karimova", "madina", "madina77", "Shokolad", None, None),
                ("Jasur Toshmatov", "jasur", "jasur2026", "Krujka", None, None),
                ("Nigora Sobirova", "nigora", "nigora99", "Bloknot", None, None),
            ]
            conn.executemany(
                "INSERT INTO users (name, login, password, wish, assignedTo, match2) VALUES (?, ?, ?, ?, ?, ?)",
                initial_users
            )

        # Boshlang'ich musiqa sozlamasi
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("site_music", DEFAULT_MUSIC)
        )
        conn.commit()


def get_all_users():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
        return [dict(row) for row in rows]


def get_user_by_id(user_id):
    if not user_id:
        return None
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_user_by_login(login_val):
    if not login_val:
        return None
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE login = ?", (login_val,)).fetchone()
        return dict(row) if row else None


def get_music_url():
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = 'site_music'").fetchone()
        return row["value"] if row and row["value"] else DEFAULT_MUSIC


init_db()


@app.route("/")
def index():
    current_user_id = session.get("user_id")
    music_url = get_music_url()

    if not current_user_id:
        return redirect(url_for("login_view"))

    current_user = get_user_by_id(current_user_id)
    if not current_user:
        session.pop("user_id", None)
        return redirect(url_for("login_view"))

    return render_template("index.html", users=get_all_users(), current_user=current_user, music_url=music_url)


@app.route("/login", methods=["GET", "POST"])
def login_view():
    music_url = get_music_url()

    if request.method == "POST":
        login_val = request.form.get("login")
        pass_val = request.form.get("password")

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE login = ? AND password = ?",
                (login_val, pass_val)
            ).fetchone()

        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("index"))

        return render_template("login.html", error="Login yoki parol xato!", music_url=music_url)

    return render_template("login.html", error=None, music_url=music_url)


@app.route("/register", methods=["GET", "POST"])
def register_view():
    music_url = get_music_url()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "").strip()
        wish = request.form.get("wish", "Yangi yil sovg'asi").strip() or "Yangi yil sovg'asi"

        with get_db() as conn:
            existing = conn.execute(
                "SELECT id FROM users WHERE LOWER(login) = LOWER(?)",
                (login,)
            ).fetchone()
            if existing:
                return render_template("register.html", error="Bu login allaqachon band!", music_url=music_url)

            cursor = conn.execute(
                "INSERT INTO users (name, login, password, wish, assignedTo, match2) VALUES (?, ?, ?, ?, NULL, NULL)",
                (name, login, password, wish)
            )
            conn.commit()
            session["user_id"] = cursor.lastrowid

        return redirect(url_for("index"))

    return render_template("register.html", error=None, music_url=music_url)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login_view"))


@app.route("/update_wish", methods=["POST"])
def update_wish():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return redirect(url_for("login_view"))

    wish = request.form.get("wish")
    with get_db() as conn:
        conn.execute("UPDATE users SET wish = ? WHERE id = ?", (wish, current_user_id))
        conn.commit()

    flash("Sovg'a istagingiz muvaffaqiyatli saqlandi! ✨", "success")
    return redirect(url_for("index"))


# --- CHAT QISMI ---
@app.route("/chat", methods=["GET"])
def chat_view():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return redirect(url_for("login_view"))

    current_user = get_user_by_id(current_user_id)
    if not current_user:
        session.pop("user_id", None)
        return redirect(url_for("login_view"))

    receiver_login = request.args.get("with_user")
    receiver_user = get_user_by_login(receiver_login)

    chat_messages = []
    if current_user and receiver_user:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT sender, receiver, message
                FROM messages
                WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
                ORDER BY id ASC
            """, (current_user["login"], receiver_user["login"], receiver_user["login"], current_user["login"])).fetchall()
            chat_messages = [dict(r) for r in rows]

    return render_template(
        "chat.html",
        users=get_all_users(),
        current_user=current_user,
        receiver=receiver_user,
        messages=chat_messages,
        music_url=get_music_url()
    )


@app.route("/send_message", methods=["POST"])
def send_message():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return redirect(url_for("login_view"))

    current_user = get_user_by_id(current_user_id)
    receiver_login = request.form.get("receiver_login")
    message_text = request.form.get("message", "").strip()

    if current_user and receiver_login and message_text:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
                (current_user["login"], receiver_login, message_text)
            )
            conn.commit()

    return redirect(url_for("chat_view", with_user=receiver_login))


# --- ADMIN QISMI ---
@app.route("/admin/login", methods=["POST"])
def admin_login():
    login_val = request.form.get("login")
    password_val = request.form.get("password")

    if login_val == ADMIN_LOGIN and password_val == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("admin_panel"))

    return render_template("login.html", error="Admin login yoki paroli xato!", music_url=get_music_url())


@app.route("/admin/panel")
def admin_panel():
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))
    return render_template("admin.html", users=get_all_users())


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("login_view"))


@app.route("/admin/upload_music", methods=["POST"])
def upload_music():
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))

    if 'music_file' in request.files:
        file = request.files['music_file']
        if file.filename != '':
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            new_music_url = url_for('static', filename=f'uploads/{file.filename}')
            with get_db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES ('site_music', ?)",
                    (new_music_url,)
                )
                conn.commit()
            flash("Yangi fon musiqasi muvaffaqiyatli yuklandi va doimiy saqlandi! 🎵", "success")

    return redirect(url_for("admin_panel"))


@app.route("/admin/run_raffle_1", methods=["POST"])
def run_raffle_1():
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))

    selected_logins = request.form.getlist("logins")
    all_users = get_all_users()
    active_users = [u for u in all_users if u["login"] in selected_logins]

    if len(active_users) < 2:
        flash("Qur'a tashlash uchun kamida 2 ta ishtirokchi tanlang!", "error")
        return redirect(url_for("admin_panel"))

    receivers = list(active_users)
    valid, attempts = False, 0
    while not valid and attempts < 500:
        attempts += 1
        random.shuffle(receivers)
        valid = all(giver["id"] != receivers[i]["id"] for i, giver in enumerate(active_users))

    with get_db() as conn:
        for i, giver in enumerate(active_users):
            conn.execute("UPDATE users SET assignedTo = ? WHERE id = ?", (receivers[i]["id"], giver["id"]))
        conn.commit()

    flash("1-Qur'a tashlash muvaffaqiyatli va bazaga doimiy saqlandi! 🎁", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/edit_raffle_1", methods=["POST"])
def edit_raffle_1():
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))

    all_users = get_all_users()
    valid_ids = {u["id"] for u in all_users}
    updated_assignments = {}

    for giver in all_users:
        field_name = f"receiver_{giver['id']}"
        selected_val = request.form.get(field_name, "").strip()

        if selected_val == "":
            updated_assignments[giver["id"]] = None
            continue

        try:
            receiver_id = int(selected_val)
        except ValueError:
            flash("Noto'g'ri foydalanuvchi ID kiritildi!", "error")
            return redirect(url_for("admin_panel"))

        if receiver_id == giver["id"]:
            flash(f"{giver['name']} o'ziga-o'zi Secret Santa bo'la olmaydi!", "error")
            return redirect(url_for("admin_panel"))

        if receiver_id not in valid_ids:
            flash("Tanlangan sovg'a oluvchi foydalanuvchi bazada topilmadi!", "error")
            return redirect(url_for("admin_panel"))

        updated_assignments[giver["id"]] = receiver_id

    with get_db() as conn:
        for giver_id, receiver_id in updated_assignments.items():
            conn.execute("UPDATE users SET assignedTo = ? WHERE id = ?", (receiver_id, giver_id))
        conn.commit()

    flash("1-Qur'a juftliklari muvaffaqiyatli tahrirlandi va bazaga saqlandi! ✏️🎁", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/run_raffle_2", methods=["POST"])
def run_raffle_2():
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))

    selected_logins = request.form.getlist("logins")
    all_users = get_all_users()
    active_users = [u for u in all_users if u["login"] in selected_logins]

    if len(active_users) < 2:
        flash("Qur'a tashlash uchun kamida 2 ta ishtirokchi tanlang!", "error")
        return redirect(url_for("admin_panel"))

    receivers = list(active_users)
    valid, attempts = False, 0
    while not valid and attempts < 500:
        attempts += 1
        random.shuffle(receivers)
        valid = all(giver["id"] != receivers[i]["id"] for i, giver in enumerate(active_users))

    with get_db() as conn:
        for i, giver in enumerate(active_users):
            conn.execute("UPDATE users SET match2 = ? WHERE id = ?", (receivers[i]["id"], giver["id"]))
        conn.commit()

    flash("2-Qur'a tashlash muvaffaqiyatli va bazaga saqlandi! 🚀", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/add_user", methods=["POST"])
def admin_add_user():
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))

    name = request.form.get("name", "").strip()
    login = request.form.get("login", "").strip()
    password = request.form.get("password", "").strip()

    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE LOWER(login) = LOWER(?)", (login,)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO users (name, login, password, wish, assignedTo, match2) VALUES (?, ?, ?, 'Sovg''a', NULL, NULL)",
                (name, login, password)
            )
            conn.commit()
            flash(f"{name} tizimga doimiy qo'shildi! 👤", "success")
        else:
            flash("Bu login allaqachon mavjud!", "error")

    return redirect(url_for("admin_panel"))


@app.route("/admin/delete_user/<int:user_id>")
def admin_delete_user(user_id):
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))

    with get_db() as conn:
        # O'chirilgan foydalanuvchiga biriktirilgan qur'a natijalarini ham tozalash
        conn.execute("UPDATE users SET assignedTo = NULL WHERE assignedTo = ?", (user_id,))
        conn.execute("UPDATE users SET match2 = NULL WHERE match2 = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

    flash("Foydalanuvchi bazadan o'chirildi.", "success")
    return redirect(url_for("admin_panel"))


if __name__ == "__main__":
    app.run(debug=True)