from flask import Flask, render_template, request, redirect, flash, abort
import pymysql
from dynaconf import Dynaconf
import flask_login

app = Flask(__name__)

conf = Dynaconf(
    settings_file = ["settings.toml"]
)

 
app.secret_key = conf.secret_key

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/sign_in'

class User:
    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, user_id, username, email, first_name, last_name):
        self.id = user_id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    def get_id(self): 
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `User` WHERE id ={user_id};")

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result is not None:
        return User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])
    
def connect_db():
    conn = pymysql.connect(
        host = "db.steamcenter.tech",
        database = "hand_in_hand",
        user = conf.user,
        password = conf.password,
        autocommit = True,
        cursorclass = pymysql.cursors.DictCursor
    )

    return conn

@app.route("/")
def index():
    return render_template("homepage.html.jinja")

@app.route("/sign_up", methods =["POST", "GET"])
def sign_up_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    else:
        if request.method == 'POST':

            first_name = request.form["first_name"]
            last_name = request.form["last_name"]

            email = request.form["email"]
            address = request.form["address"]

            username = request.form["user_name"]
            password = request.form["password"]
            age = request.form["age"]

            phone_number = request.form["phone_number"]

            if request.form["roll"] == "Yes":
                role = "Caretaker"
            else: 
                role = "Need Of Assistance"

            if request.form["with_parent"] == "Yes":
                with_parent = "Yes"
            else:
                with_parent = "No"

            comfirm_password = request.form["verify_password"]

            conn = connect_db()

            cursor = conn.cursor()

            if comfirm_password != password:
                flash("Sorry, those passwords do not match")
            elif len(password) < 12:
                flash("Sorry, that password is too short")
            elif (age <= 18 and with_parent == "No"):
                flash("Must have a parent or gaurdian present")
            else:
                try:
                    cursor.execute(f""" 
                        INSERT INTO `User`
                            (`first_name`, `last_name`, `username`, `password`, `email`, `address`, `age`, `phone_number`, `role`, `with_parent` )
                        VALUES
                            ( '{first_name}', '{last_name}', '{username}', '{password}', '{email}', '{address}', '{age}', '{phone_number}', '{role}', '{with_parent}' );
                    """)
                except pymysql.err.IntegrityError:
                    flash("Sorry, that username/email is already in use")
                else:
                    return redirect("/sign_in") 
                finally:
                    cursor.close()
                    conn.close()


        return render_template("sign_up.html.jinja")


@app.route("/sign_in", methods =["POST", "GET"])
def sign_in_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    else:
        if request.method == "POST":
            username = request.form['username'].strip()
            password = request.form['password']

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM `User` WHERE `username` = '{username}';")

            result = cursor.fetchone()

            if result is None:
                flash("Your username/password is incorrect")
            elif password != result["password"]:
                flash("Your username/password is incorrect")
            else:
                user = User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])
                flask_login.login_user(user)

                return redirect("/")


        return render_template("sign_in.html.jinja")


@app.route('/sign_out')
def sign_out():
    flask_login.logout_user()
    return redirect('/')


@app.route("/maps")
def maps():
    return render_template("maps.html.jinja")


@app.route("/reviews")
def reviews():
    return render_template("reviews.html.jinja")


@app.route("/updates")
def updates():
    return render_template("updates.html.jinja")


@app.route("/hiring")
def hiring():
    return render_template("hiring.html.jinja")
    
