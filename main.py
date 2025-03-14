from flask import Flask, render_template, request, redirect, flash, abort
import pymysql
from dynaconf import Dynaconf
import flask_login
from flask_socketio import SocketIO, send


app = Flask(__name__)

conf = Dynaconf(
    settings_file = ["settings.toml"]
)

socketio = SocketIO(app, cors_allowed_origins="*")
 
@socketio.on('message')
def handle_message(message):
    print("Received message: " + message)
    if message != "User connected!":
        send(message, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="Messages")



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
        user = conf.username,
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

            if request.form["role"] == "Yes":
                role = 1
            else: 
                role = 0

            if request.form["with_parent"] == "Yes":
                with_parent = 1
            else:
                with_parent = 0

            comfirm_password = request.form["verify_password"]

            conn = connect_db()

            cursor = conn.cursor()

            if comfirm_password != password:
                flash("Sorry, those passwords do not match")
            elif len(password) < 12:
                flash("Sorry, that password is too short")
            elif role == 0 and (int(age) < 18 and with_parent == 0):
                    flash("Must have a parent or gaurdian present")
            elif role == 1 and (int(age) < 18):
                    flash("Must be 18 and up to be a caretaker")
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
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Places`")

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("maps.html.jinja", coords = results)






@app.route("/updates")
@flask_login.login_required
def updates():

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"""SELECT
                        `user_id`,
                        `places_id`,
                        `written_update`,
                        `accessable`,
                        `Updates`.`timestamp`,
                        `Places`.`name`,
                        `User`.`username`
                    FROM `Updates`
                    JOIN `User` ON `user_id` = `User`.`id`
                    JOIN `Places` ON `places_id` = `Places`.`id`
                    ORDER BY `timestamp` DESC LIMIT 4;""")
    
    results = cursor.fetchall()

    if results is None:
        flash("Please make sure all feilds are filled out in your responce")

    cursor.execute(f"SELECT * FROM `Places` ORDER BY `name`")

    results2 = cursor.fetchall()

    cursor.close()
    conn.close()


    return render_template("updates.html.jinja", updates = results, locations = results2 )







@app.route("/updates/update", methods = ["POST"])
def update():
    conn = connect_db()
    cursor = conn.cursor()

    user_id = flask_login.current_user.id

    written_update = request.form["written_update"]

    places_id = request.form["place"]

    accessable = 1 if request.form.get("accessable") == "Yes" else 0

    cursor.execute(f"""INSERT INTO `Updates`
                        (`user_id`, `places_id`, `written_update`, `accessable`)
                        VALUES
                        ("{user_id}", "{places_id}", "{written_update}", "{accessable}");""")

    return redirect("/updates")







@app.route("/hiring")
def hiring():

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `User` WHERE `role` = 1;")
    
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("hiring.html.jinja", caretakers = results)






    
@app.route("/hiree_profile/<caretaker_id>")
def hiree_profile(caretaker_id):
    if not flask_login.current_user.is_authenticated:
        return redirect("/sign_in")
    else:
    
        conn = connect_db()

        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM `User` WHERE `id` = {caretaker_id}")

        result = cursor.fetchone()
        
        if result is None:
            abort (404)
        
        cursor.execute(f""" SELECT
                            `reviewer_id`,
                            `written_review`,
                            `rating`,
                            `Reviews`.`timestamp`,
                            `username`
                        FROM `Reviews`
                        JOIN `User` ON `reviewer_id` = `User`.`id`
                        WHERE `caretaker_id` = {caretaker_id}
                        ORDER BY `timestamp` DESC;""")
    
        results = cursor.fetchall()

        total = 0 
        try:

            for rating in results:
                number = rating['rating']

                total += number
            
            count = len(results)
            average = total/count
        except:
                average = 0
    

        cursor.close()
        conn.close()

        return render_template("hiree_profile.html.jinja", caretaker = result, reviews = results, average = average)
    
    





@app.route("/hiree_profile/<caretaker_id>/review", methods = ["POST"])
@flask_login.login_required
def review(caretaker_id):
    conn = connect_db()
    cursor = conn.cursor()

    reviewer_id = flask_login.current_user.id

    written_review = request.form["written_review"]
    rating = request.form["rating"]

    cursor.execute(f"""INSERT INTO `Reviews`
                   (`caretaker_id`, `reviewer_id`, `written_review`, `rating`)
                   VALUES
                   ("{caretaker_id}", "{reviewer_id}", "{written_review}", "{rating}")
                   ON DUPLICATE KEY UPDATE
                   `written_review` = "{written_review}",
                   `rating` = "{rating}";
                    """)
    
    return redirect(f"/hiree_profile/{caretaker_id}")


@app.route("/messages")
def messages():
    return render_template("message.html.jinja")








@app.route("/listing")
@flask_login.login_required
def listing():
    return render_template("listing.html.jinja")

