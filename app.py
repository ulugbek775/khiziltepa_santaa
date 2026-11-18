from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os

app = Flask(__name__)
app.secret_key = "santa_secret_key_2026"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "santa2026"

users_db = [
    {"id": 1, "name": "Ali Valiyev", "login": "ali", "password": "ali123", "wish": "Kitob", "assignedTo": None, "match2": None},
    {"id": 2, "name": "Madina Karimova", "login": "madina", "password": "madina77", "wish": "Shokolad", "assignedTo": None, "match2": None},
    {"id": 3, "name": "Jasur Toshmatov", "login": "jasur", "password": "jasur2026", "wish": "Krujka", "assignedTo": None, "match2": None},
    {"id": 4, "name": "Nigora Sobirova", "login": "nigora", "password": "nigora99", "wish": "Bloknot", "assignedTo": None, "match2": None}
]

messages_db = []

@app.route("/")
def index():
    current_user_id = session.get("user_id")
    music_url = session.get("site_music", "https://upload.wikimedia.org/wikipedia/commons/e/e4/Jingle_Bells_%28Kevin_MacLeod%29_%28ISRC_USUAN1100187%29.mp3")
    
    if not current_user_id:
        return redirect(url_for("login_view"))
    
    current_user = next((u for u in users_db if u["id"] == current_user_id), None)
    return render_template("index.html", users=users_db, current_user=current_user, music_url=music_url)

@app.route("/login", methods=["GET", "POST"])
def login_view():
    music_url = session.get("site_music", "https://upload.wikimedia.org/wikipedia/commons/e/e4/Jingle_Bells_%28Kevin_MacLeod%29_%28ISRC_USUAN1100187%29.mp3")
    
    if request.method == "POST":
        login_val = request.form.get("login")
        pass_val = request.form.get("password")
        
        user = next((u for u in users_db if u["login"] == login_val and u["password"] == pass_val), None)
        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
            
        return render_template("login.html", error="Login yoki parol xato!", music_url=music_url)
        
    return render_template("login.html", error=None, music_url=music_url)

@app.route("/register", methods=["GET", "POST"])
def register_view():
    music_url = session.get("site_music", "https://upload.wikimedia.org/wikipedia/commons/e/e4/Jingle_Bells_%28Kevin_MacLeod%29_%28ISRC_USUAN1100187%29.mp3")
    
    if request.method == "POST":
        name = request.form.get("name")
        login = request.form.get("login")
        password = request.form.get("password")
        wish = request.form.get("wish", "Yangi yil sovg'asi")

        if any(u["login"].lower() == login.lower() for u in users_db):
            return render_template("register.html", error="Bu login allaqachon band!", music_url=music_url)

        new_id = max([u["id"] for u in users_db], default=0) + 1
        new_user = {"id": new_id, "name": name, "login": login, "password": password, "wish": wish, "assignedTo": None, "match2": None}
        users_db.append(new_user)
        session["user_id"] = new_id
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
    for u in users_db:
        if u["id"] == current_user_id:
            u["wish"] = wish
            break
    flash("Sovg'a istagingiz muvaffaqiyatli saqlandi! ✨", "success")
    return redirect(url_for("index"))

# --- CHAT QISMI ---
@app.route("/chat", methods=["GET"])
def chat_view():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return redirect(url_for("login_view"))
    
    current_user = next((u for u in users_db if u["id"] == current_user_id), None)
    receiver_login = request.args.get("with_user")
    receiver_user = next((u for u in users_db if u["login"] == receiver_login), None)
    
    chat_messages = []
    if current_user and receiver_user:
        chat_messages = [
            m for m in messages_db 
            if (m['sender'] == current_user['login'] and m['receiver'] == receiver_user['login']) or
               (m['sender'] == receiver_user['login'] and m['receiver'] == current_user['login'])
        ]
        
    music_url = session.get("site_music", "https://upload.wikimedia.org/wikipedia/commons/e/e4/Jingle_Bells_%28Kevin_MacLeod%29_%28ISRC_USUAN1100187%29.mp3")
    return render_template("chat.html", users=users_db, current_user=current_user, receiver=receiver_user, messages=chat_messages, music_url=music_url)

@app.route("/send_message", methods=["POST"])
def send_message():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return redirect(url_for("login_view"))
        
    current_user = next((u for u in users_db if u["id"] == current_user_id), None)
    receiver_login = request.form.get("receiver_login")
    message_text = request.form.get("message")
    
    if current_user and receiver_login and message_text:
        messages_db.append({
            'sender': current_user['login'],
            'receiver': receiver_login,
            'message': message_text
        })
        
    return redirect(url_for('chat_view', with_user=receiver_login))

# --- ADMIN QISMI ---
@app.route("/admin/login", methods=["POST"])
def admin_login():
    login_val = request.form.get("login")
    password_val = request.form.get("password")
    
    if login_val == ADMIN_LOGIN and password_val == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("admin_panel"))
    
    music_url = session.get("site_music", "https://upload.wikimedia.org/wikipedia/commons/e/e4/Jingle_Bells_%28Kevin_MacLeod%29_%28ISRC_USUAN1100187%29.mp3")
    return render_template("login.html", error="Admin login yoki paroli xato!", music_url=music_url)

@app.route("/admin/panel")
def admin_panel():
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))
    return render_template("admin.html", users=users_db)

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
            session["site_music"] = url_for('static', filename=f'uploads/{file.filename}')
            flash("Yangi fon musiqasi muvaffaqiyatli yuklandi! 🎵", "success")
            
    return redirect(url_for("admin_panel"))

@app.route("/admin/run_raffle_1", methods=["POST"])
def run_raffle_1():
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))
    selected_logins = request.form.getlist("logins")
    active_users = [u for u in users_db if u["login"] in selected_logins]
    if len(active_users) < 2:
        flash("Qur'a tashlash uchun kamida 2 ta ishtirokchi tanlang!", "error")
        return redirect(url_for("admin_panel"))
    
    receivers = list(active_users)
    valid, attempts = False, 0
    while not valid and attempts < 500:
        attempts += 1
        random.shuffle(receivers)
        valid = all(giver["id"] != receivers[i]["id"] for i, giver in enumerate(active_users))
        
    for i, giver in enumerate(active_users):
        giver["assignedTo"] = receivers[i]["id"]
        
    flash("1-Qur'a tashlash muvaffaqiyatli va profilga yuborildi! 🎁", "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/run_raffle_2", methods=["POST"])
def run_raffle_2():
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))
    selected_logins = request.form.getlist("logins")
    active_users = [u for u in users_db if u["login"] in selected_logins]
    if len(active_users) < 2:
        flash("Qur'a tashlash uchun kamida 2 ta ishtirokchi tanlang!", "error")
        return redirect(url_for("admin_panel"))
        
    receivers = list(active_users)
    valid, attempts = False, 0
    while not valid and attempts < 500:
        attempts += 1
        random.shuffle(receivers)
        valid = all(giver["id"] != receivers[i]["id"] for i, giver in enumerate(active_users))

    for i, giver in enumerate(active_users):
        giver["match2"] = receivers[i]["id"]
        
    flash("2-Qur'a tashlash muvaffaqiyatli va profilga yuborildi! 🚀", "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/add_user", methods=["POST"])
def admin_add_user():
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))
    name, login, password = request.form.get("name"), request.form.get("login"), request.form.get("password")
    if not any(u["login"].lower() == login.lower() for u in users_db):
        new_id = max([u["id"] for u in users_db], default=0) + 1
        users_db.append({"id": new_id, "name": name, "login": login, "password": password, "wish": "Sovg'a", "assignedTo": None, "match2": None})
        flash(f"{name} tizimga qo'shildi! 👤", "success")
    else:
        flash("Bu login allaqachon mavjud!", "error")
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_user/<int:user_id>")
def admin_delete_user(user_id):
    if not session.get("is_admin"):
        return redirect(url_for("login_view"))
    global users_db
    users_db = [u for u in users_db if u["id"] != user_id]
    flash("Foydalanuvchi o'chirildi.", "success")
    return redirect(url_for("admin_panel"))

if __name__ == "__main__":
    app.run(debug=True)