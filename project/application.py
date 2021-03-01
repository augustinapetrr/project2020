import os
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import csv
import random

from helpers import apology, login_required, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATESAUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///storage.db")

person_id = 0
topic = "Knygos"

@app.route("/", methods=["GET", "POST"])
@login_required
def board():
    """Show board with all posts"""
    if request.method == "GET":
        file = open('skelbimai.csv', 'r')
        reader = csv.DictReader(file)
        file.close
        return render_template("board.html", reader=reader)
    else:
        """Links to other person's account page"""
        user = db.execute("SELECT * FROM users WHERE name=:name", name=request.form.get("user"))
        information = db.execute("SELECT * FROM information WHERE id=:ID", ID=user[0]['id'])
        global person_id
        person_id = user[0]['id']
        return render_template("profile.html", user=user[0], information=information[0])

@app.route("/add_board", methods=["GET", "POST"])
@login_required
def add_board():
    """Show form to make a new post"""
    if request.method == "POST":

        title = "" + request.form.get("title")
        text = "" + request.form.get("text")
        user = db.execute("SELECT * FROM users WHERE id = :ID", ID = session['user_id'])[0]['name'] + str(db.execute("SELECT * FROM users WHERE id = :ID", ID = session['user_id'])[0]['id'])
        name = db.execute("SELECT * FROM users WHERE id = :ID", ID = session['user_id'])[0]['name']
        fieldnames = ['title', 'text', 'user', 'name']
        # read header automatically
        with open('skelbimai.csv', "r") as f:
            reader = csv.reader(f)
            for header in reader:
                break
        # add row to CSV file
        with open('skelbimai.csv', "a", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writerow({'title': title, 'text': text, 'user' : user, 'name' : name})
        return redirect("/")
    else:
        return render_template("add_board.html")

@app.route("/account")
@login_required
def acc():
    """Your account page with a link to make changes"""
    user = db.execute("SELECT * FROM users WHERE id=:ID", ID=session["user_id"])
    information = db.execute("SELECT * FROM information WHERE id=:ID", ID=session["user_id"])
    return render_template("account.html", user=user[0], information=information[0])


@app.route("/changes", methods=["GET", "POST"])
@login_required
def changes():
    if request.method == "GET":
        #display form
        return render_template("changes.html")
    else:
        #check for changes
        if request.form.get("dog_name"):
            db.execute("UPDATE information SET dog_name = :dog_name WHERE id = :ID", dog_name = request.form.get("dog_name"), ID = session["user_id"])
        if request.form.get("dog_age"):
            db.execute("UPDATE information SET dog_age = :dog_age WHERE id = :ID", dog_age = request.form.get("dog_age"), ID = session["user_id"])
        if request.form.get("dog_breed"):
            db.execute("UPDATE information SET breed = :breed WHERE id = :ID", breed = request.form.get("dog_breed"), ID = session["user_id"])
        if request.form.get("gender"):
            if request.form.get("gender") == 'male':
                db.execute("UPDATE information SET dog_gender = 'Berniukas' WHERE id = :ID", ID = session["user_id"])
            else:
                db.execute("UPDATE information SET dog_gender = 'Mergaitė' WHERE id = :ID", ID = session["user_id"])
        if request.form.get("about_me"):
            db.execute("UPDATE information SET about_me = :ab WHERE id = :ID", ab = request.form.get("about_me"), ID=session["user_id"])
        if request.form.get("about_dog"):
            db.execute("UPDATE information SET about_dog = :abd WHERE id = :ID", abd = request.form.get("about_dog"), ID=session["user_id"])
        return redirect("/account")

@app.route("/add_topic", methods=["GET", "POST"])
@login_required
def add_topic():
    """add new discussion to forum"""
    if request.method == "POST":
        title = request.form.get("topic")
        db.execute(f"CREATE TABLE IF NOT EXISTS '{title}' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'writer_id' INTEGER NOT NULL, 'name' TEXT NOT NULL, 'post' TEXT NOT NULL)")
        db.execute(f"INSERT INTO '{title}' (writer_id, name, post) VALUES (:ID, :name, :post)",
                    ID=session["user_id"], name=db.execute("SELECT * FROM users WHERE id=:ID", ID=session["user_id"])[0]['name'], post=request.form.get("post"))
        if not db.execute("SELECT id FROM topics_forum WHERE topic = :topic", topic=title):
            db.execute("INSERT INTO topics_forum (topic) VALUES (:topic)", topic=title)
        return redirect("/forum")
    else:
        return render_template("add_forum.html")

@app.route("/link", methods=["GET", "POST"])
@login_required
def link_profile():
    if request.method == "POST":
        """Links to other person's account page"""
        user = db.execute("SELECT * FROM users WHERE id=:ID", ID=request.form.get("writer_id"))
        information = db.execute("SELECT * FROM information WHERE id=:ID", ID=user[0]['id'])
        global person_id
        person_id = user[0]['id']
        return render_template("profile.html", user=user[0], information=information[0])

@app.route("/post", methods=["GET", "POST"])
@login_required
def add_post():
    """add your post to forum"""
    topics = db.execute("SELECT topic FROM topics_forum ORDER BY id DESC")
    if request.method == "POST":
        name = db.execute("SELECT name FROM users WHERE id=:ID", ID=session["user_id"])
        global topic
        db.execute(f"INSERT INTO '{topic}'(writer_id, name, post) VALUES (:writer_id, :name, :post)",
                    writer_id=session["user_id"], name=name[0]['name'], post=request.form.get("post"))
        posts = db.execute(f"SELECT * FROM '{topic}' ORDER BY id DESC")
        return render_template("forum.html", topics=topics, posts=posts)

@app.route("/forum", methods=["GET", "POST"])
@login_required
def forum():
    """forum links to discussion"""
    topics = db.execute("SELECT topic FROM topics_forum ORDER BY id DESC")
    global topic
    if request.method == "POST":
        topic = request.form.get("topic")
        posts = db.execute(f"SELECT * FROM '{topic}' ORDER BY id DESC")
        return render_template("forum.html", topics=topics, posts=posts, title=topic)
    else:
        topic = topics[0]['topic']
        posts = db.execute(f"SELECT * FROM '{topic}' ORDER BY id DESC")
        return render_template("forum.html", topics=topics, posts=posts)

@app.route("/stories", methods=["GET", "POST"])
@login_required
def info():
    """display the stories"""
    if request.method == "GET":
        file = open('stories.csv', 'r')
        reader = csv.DictReader(file)
        file.close
        return render_template("stories.html", reader=reader)
    else:
        """Links to other person's account page"""
        user = db.execute("SELECT * FROM users WHERE name=:name", name=request.form.get("user"))
        information = db.execute("SELECT * FROM information WHERE id=:ID", ID=user[0]['id'])
        global person_id
        person_id = user[0]['id']
        return render_template("profile.html", user=user[0], information=information[0])

@app.route("/add_stories", methods=["GET", "POST"])
@login_required
def add_story():
    """Show form to make a new post"""
    if request.method == "POST":
        title = "" + request.form.get("title")
        text = "" + request.form.get("text")
        name = db.execute("SELECT * FROM users WHERE id = :ID", ID = session['user_id'])[0]['name']
        # read header automatically
        with open('stories.csv', "r") as f:
            reader = csv.reader(f)
            for header in reader:
                break
        # add row to CSV file
        with open('stories.csv', "a", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writerow({'title': title, 'text': text, 'name' : name})
        return redirect("/stories")
    else:
        return render_template("add_stories.html")

@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    """display the list of the chats with other users"""
    if request.method == "POST":
        global person_id
        person_id = request.form.get("id")
        return redirect("/messages")
    else:
        title = str(db.execute("SELECT name FROM users WHERE id = :ID", ID=session["user_id"])[0]['name']) + str(session["user_id"])
        users = db.execute(f"SELECT * FROM users WHERE id IN (SELECT talk_with FROM '{title}')")
        return render_template("chat.html", users=users)


"""function that creates table's name"""
def get_title(a, b):
    sep = ':'
    if (int(a) < int(b)):
        return str(a) + sep + str(b)
    else:
        return str(b) + sep + str(a)

@app.route("/messages", methods=["GET", "POST"])
@login_required
def messages():
    """display private messages and tinder matches"""
    global person_id
    title = get_title(session["user_id"], person_id)
    if request.method == "POST":
        db.execute(f"INSERT INTO '{title}' (sent_from, message) VALUES (:sent_from, :message)", sent_from=session["user_id"], message=request.form.get("message"))
    else:
        db.execute(f"CREATE TABLE IF NOT EXISTS '{title}' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'sent_from' INTEGER NOT NULL, 'message' TEXT NOT NULL)")
        title2 = str(db.execute("SELECT name FROM users WHERE id = :ID", ID=session["user_id"])[0]['name']) + str(session["user_id"])
        if not db.execute(f"SELECT id FROM '{title2}' WHERE talk_with = :person_id", person_id=person_id):
            db.execute(f"INSERT INTO '{title2}' (talk_with) VALUES (:person_id)", person_id=person_id)
    messages = db.execute(f"SELECT * FROM '{title}'")
    return render_template("messages.html", messages=messages, my_id=session["user_id"], title=db.execute("SELECT name FROM users WHERE id = :ID", ID=person_id)[0]['name'])

@app.route("/date", methods=["GET", "POST"])
@login_required
def date():
    """Dogs date randomizer"""
    global person_id
    if request.method == "POST":
        if request.form.get("heart") == "H": # add person to chats
            title = get_title(session["user_id"], person_id)
            db.execute(f"CREATE TABLE IF NOT EXISTS '{title}' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'sent_from' INTEGER NOT NULL, 'message' TEXT NOT NULL)")
            title2 = str(db.execute("SELECT name FROM users WHERE id = :ID", ID=session["user_id"])[0]['name']) + str(session["user_id"])
            if not db.execute(f"SELECT id FROM '{title2}' WHERE talk_with = :person_id", person_id=person_id):
                db.execute(f"INSERT INTO '{title2}' (talk_with) VALUES (:person_id)", person_id=person_id)
            return redirect("/date")
        if request.form.get("cross") == "C":
            return redirect("/date")
    else:
        MAX = len(db.execute("SELECT * FROM users"))
        num = random.randint(1, MAX)
        while num == session['user_id']:
            num = random.randint(1, MAX)
        information = db.execute("SELECT * FROM information WHERE id=:ID", ID = num)
        while information[0]['about_dog'] == None:
            while num == session['user_id']:
                num = random.randint(1, MAX)
            information = db.execute("SELECT * FROM information WHERE id=:ID", ID = num)
        person_id = num
        return render_template("date.html", information=information[0])

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("mail"):
            return apology("must provide mail", 403)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE mail = :mail",
                          mail=request.form.get("mail"))
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid mail and/or password", 403)
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Redirect user to homepage
        return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")



@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        #display registration form
        return render_template("register.html")
    else:
        # Check if passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 403)
        # Update the table and hash the password
        id = db.execute("INSERT INTO users (mail, name, hash) VALUES(:mail, :name, :hash)", mail=request.form.get("mail"), name=request.form.get("name"), hash=generate_password_hash(request.form.get("password")))
        # Ensure mail is not used yet
        if not id:
            return apology("mail is not available", 403)
        db.execute("INSERT INTO information (id) VALUES(:ID)", ID=int(db.execute("SELECT * FROM users WHERE mail=:mail", mail=request.form.get("mail"))[0]['id']))
        title = request.form.get("name") + str(db.execute("SELECT * FROM users WHERE mail=:mail", mail=request.form.get("mail"))[0]['id'])
        db.execute(f"CREATE TABLE '{title}' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'talk_with' INTEGER NOT NULL)")
        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
