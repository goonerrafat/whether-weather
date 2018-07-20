import os , utilities 
from datetime import datetime

from flask import Flask, session, render_template , request, redirect, url_for,g, flash,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/") 
def index():
    return redirect(url_for('search'))

@app.route('/login', methods = ['POST' , 'GET'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        existing_user = db.execute("SELECT * FROM userlist WHERE username = :username AND password =:password",
           {"username":username , "password":password})

        if(existing_user.rowcount == 1): 
            session['user'] = username
            return redirect(url_for("search"))

        message = "your credential doesn't match with an existing account.try again"
        return render_template("login.html" , message = message , al_type = "danger")
    try:
        message = session['message']
        al_type = session['al_type']
    except KeyError: 
         return render_template('login.html')

    return render_template('login.html', message = message, al_type = al_type)

@app.route("/signup" , methods = ["POST" , "GET"])
def signup():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")


        check_for_existing_user = db.execute("SELECT * FROM userlist WHERE username = :username", {"username":username})
        if(check_for_existing_user.rowcount > 0):
            message_u = "Sorry the username has already taken"
            return render_template("signup.html" ,message_u = message_u, al_type = "danger")

        if(not utilities.process_password(password, confirm_password)):
            message_p = "bad password, try again!"
            return render_template("signup.html" ,message_p = message_p, al_type = "danger")

        db.execute("INSERT INTO userlist (username, password) VALUES (:username, :password)",{
            "username":username, "password":password })
        db.commit()
        session['message'] = "Login Now!"
        session['al_type'] = "primary"
        return redirect(url_for('login'))
        #return render_template("login.html" , message = "Login now!" , al_type = "primary")

    return render_template("signup.html") 

@app.route('/search' , methods = ['POST' , 'GET'])
def search():
    if request.method == 'POST':
       search_item = request.form.get("search_item") 
       return redirect(url_for('search_result' ,search_item = search_item))
       
    return render_template("search.html")


@app.route('/search/<string:search_item>')
def search_result(search_item):
    city_list = db.execute("SELECT * FROM cities WHERE Zipcode LIKE :search_item \
        OR City LIKE UPPER(:search_item)" , {"search_item":'%'+ search_item +'%'}).fetchall()
    if(len(city_list) == 0):
        flash("Nothing found. try again.")
        return redirect(url_for("search"))
    return render_template("searched.html" , search_items = city_list)


@app.route('/search/<int:zipp>' ,methods = ['POST' , 'GET'])
def display(zipp):
    #city_id=request.args.get('city_id')
    city = db.execute("SELECT * FROM cities WHERE zipcode = :zipcode" ,{"zipcode":str(zipp)}).fetchone()
    weather_information = utilities.json.loads(utilities.handle_weather(str(city.lat) , str(city.long)))
    timeline = weather_information["time"]
    timeline = datetime.fromtimestamp(int(timeline)).strftime('Date: %Y-%m-%d,  Time: %H:%M:%S')
    weather_information["time"] = timeline ;

    if request.method == "POST":
        review = request.form.get("user_review")
        user_id = db.execute("SELECT * FROM userlist WHERE username = :username", {"username":session['user']}).fetchone()
        user_id = user_id.id

        db.execute("INSERT INTO reviews (username, review, timeline, city_id, user_id) VALUES(:username, :review, :timeline, :city_id,\
            :user_id)", {"username":session['user'], "review":str(review), "timeline":str(timeline), "city_id":int(city.id), "user_id":int(user_id)})
        db.commit()
        flash("Your review is recorded!") ;

    
    user_reviews = db.execute("SELECT * FROM reviews WHERE city_id = :city_id" , {"city_id":int(city.id)}).fetchall()
    total_checkin = len(user_reviews)
    if(db.execute("SELECT * FROM reviews WHERE city_id = :city_id AND username = :username" , 
        {"city_id":int(city.id), "username": session['user']}).rowcount >0):
        button_disabled = True 
    else:
        button_disabled = False 

    return render_template("information.html" , location = city , 
        weather_information = weather_information,user_reviews = user_reviews , check_ins = total_checkin,
        button_disabled = button_disabled)


@app.route("/api/<string:zippy>")
def api_request(zippy):

    city_information = db.execute("SELECT * FROM cities WHERE Zipcode = :zippy" , {"zippy" : zippy}).fetchone()
    if(not city_information):
        return jsonify({"error":"Invalid Zipcode"}), 422

    checkin_num= db.execute("SELECT COUNT(*) FROM reviews WHERE city_id = :city_id" , {"city_id": city_information.id}).fetchone()
    checkin_num = checkin_num.count

    return jsonify({
    "place_name": city_information.city,
    "state": city_information.state,
    "latitude": float(city_information.lat),
    "longitude": float(city_information.long),
    "zip": int(city_information.zipcode),
    "population": city_information.population,
    "check_ins": checkin_num
    })




@app.route('/logout')
def logout():
    session.pop("user", None)
    session.pop("message", None)
    session.pop("al_type", None)
    return redirect(url_for('login'))

@app.before_request
def before_request():
    if (('user' not in session) and (request.endpoint != 'login' and request.endpoint !='signup')):
        return redirect(url_for('login'))
    elif(('user' in session) and (request.endpoint == 'login' or request.endpoint == 'signup')):
        return redirect(url_for('search'))
