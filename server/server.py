from flask import Flask, request, jsonify, render_template, send_file, redirect, session, url_for
import matplotlib
import matplotlib.pyplot as plt
import io
from datetime import datetime

import pyrebase
import requests
import re
from collections import OrderedDict

matplotlib.use('Agg')

firebaseConfig = {
  "apiKey": "AIzaSyBSQHoBrlEr6GJfd4MQGkwievq3Gp0y7Xk",
  "authDomain": "pr-iot-db.firebaseapp.com",
  "projectId": "pr-iot-db",
  "storageBucket": "pr-iot-db.firebasestorage.app",
  "messagingSenderId": "279718312574",
  "appId": "1:279718312574:web:3cee2550cbc1a938dd362f",
  "measurementId": "G-H01BM9QTX9",
  "databaseURL":"https://pr-iot-db-default-rtdb.europe-west1.firebasedatabase.app/"
}

# app = Flask(__name__)
# app.secret_key = '#@#UGQ@#IU$GQIUG$Q'


firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()


def send_telegram_message(id,message):
    chat_id=7883918835
    TOKEN = "7891743339:AAENMNlD12q609NrOtqlD8ZXu_vL_yzxWx4"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.close()
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")


historical_data = {
    "air_temperature": [],
    "air_humidity": [],
    "soil_humidity": [],
    "luminosity": []
}





latest_data = {
    "air_temperature": "N/A",
    "air_humidity": "N/A",
    "soil_humidity": "N/A",
    "luminosity":"N/A"
}

timestamps = []

count = 0

# @app.route("/")
def login():
    return render_template("login.html")

# Route for the signup page
# @app.route("/signup")
def signup():
    return render_template("signup.html")

# Route for the welcome page
# @app.route("/welcome")
def welcome():
    # Check if user is logged in
    if session.get("is_logged_in", False):
        return render_template("welcome.html", email=session["email"], name=session["name"])
    else:
        # If user is not logged in, redirect to login page
        return redirect(url_for('login'))

# Function to check password strength
def check_password_strength(password):
    # At least one lower case letter, one upper case letter, one digit, one special character, and at least 8 characters long
    return re.match(r'^(?=.*\d)(?=.*[!@#$%^&*])(?=.*[a-z])(?=.*[A-Z]).{8,}$', password) is not None

# Route for login result
# @app.route("/result", methods=["POST", "GET"])
def result():
    if request.method == "POST":
        result = request.form
        email = result["email"]
        password = result["pass"]
        try:
            # Authenticate user
            user = auth.sign_in_with_email_and_password(email, password)
            
            
            
            session["is_logged_in"] = True
            session["email"] = user["email"]
            session["uid"] = user["localId"]
            # Fetch user data
            data = db.child("users").get().val()
            
            
            # Update session data
            if data and session["uid"] in data:
                session["name"] = data[session["uid"]]["name"]
                # Update last login time
                db.child("users").child(session["uid"]).update({"last_logged_in": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})
            else:
                session["name"] = "User"
            
            #get list of sensors 
            sensors = db.child("users").child(session["uid"]).child("sensors").get().val() 
            # print(sensors)
            # print(type(sensors))
            if sensors is not None: 
                session["sensors"] = list(sensors.values()) 
            else:
                session["sensors"] = []
            # Redirect to welcome page
            return redirect(url_for('welcome'))
        except Exception as e:
            print("Error occurred: ", e)
            return redirect(url_for('login'))
    else:
        # If user is logged in, redirect to welcome page
        if session.get("is_logged_in", False):
            return redirect(url_for('welcome'))
        else:
            return redirect(url_for('login'))

# Route for user registration
# @app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        result = request.form
        email = result["email"]
        password = result["pass"]
        name = result["name"]
        # if not check_password_strength(password):
        #     print("Password does not meet strength requirements")
        #     return redirect(url_for('signup'))
        try:
            # Create user account
            auth.create_user_with_email_and_password(email, password)
            # Authenticate user
            user = auth.sign_in_with_email_and_password(email, password)
            session["is_logged_in"] = True
            session["email"] = user["email"]
            session["uid"] = user["localId"]
            session["name"] = name
            # Save user data
            data = {"name": name, "email": email, "last_logged_in": datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}
            db.child("users").child(session["uid"]).set(data)
            return redirect(url_for('welcome'))
        except Exception as e:
            print("Error occurred during registration: ", e)
            return redirect(url_for('signup'))
    else:
        # If user is logged in, redirect to welcome page
        if session.get("is_logged_in", False):
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('signup'))

# @app.route("/dashboard", methods=["GET"])
def dashboard():
    if session.get("is_logged_in", False):
        return render_template("dashboard.html",devices=session["sensors"])
    else:
        return redirect(url_for('login'))

# Route for password reset
# @app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form["email"]
        try:
            # Send password reset email
            auth.send_password_reset_email(email)
            return render_template("reset_password_done.html")  # Show a page telling user to check their email
        except Exception as e:
            print("Error occurred: ", e)
            return render_template("reset_password.html", error="An error occurred. Please try again.")  # Show error on reset password page
    else:
        return render_template("reset_password.html")  # Show the password reset page

# Route for logout
# @app.route("/logout")
def logout():
    # Update last logout time
    db.child("users").child(session["uid"]).update({"last_logged_out": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})
    session["is_logged_in"] = False
    return redirect(url_for('login'))


# @app.route('/latest_data/<esp_id>', methods=['GET'])
def start(esp_id):
    if session.get("is_logged_in", False):
        if esp_id in session["sensors"]:
            # print("ceva")
            db_latest_data = db.child("sensors").child(esp_id).child("latest_data").get().val()
            print(db_latest_data)
            if db_latest_data is not None:
                return render_template('index.html',air_t=db_latest_data["air_temperature"],
                    air_h=db_latest_data["air_humidity"],
                    soil_h=db_latest_data["soil_humidity"],
                    lum=db_latest_data["luminosity"])
        
        return render_template('index.html',air_t=None,
                    air_h=None,
                    soil_h=None,
                    lum=None)
    else:  
        return redirect(url_for('login'))



# @app.route('/receive', methods=['POST'])
def receive_data():
    global latest_data, historical_data, timestamps, count
    data = request.get_json()  # Parse incoming JSON data
    if not data or 'air_temperature' not in data or 'air_humidity' not in data or 'soil_humidity' not in data or 'luminosity' not in data:
        return jsonify({"error": "Invalid data"}), 400

    print(data)
    
    temp = data['air_temperature']
    humidity = data['air_humidity']
    soil_humidity = data['soil_humidity']
    luminosity = data['luminosity']
    
    latest_data['air_temperature']  = temp
    latest_data['air_humidity']  = humidity
    latest_data['soil_humidity']  = soil_humidity
    latest_data['luminosity']  = luminosity
    
    # historical_data["air_temperature"].append(float(temp))
    # historical_data["air_humidity"].append(float(humidity))
    # historical_data["soil_humidity"].append(float(soil_humidity))
    # historical_data["luminosity"].append(float(luminosity))
    count += 1 
    if count >= 5:
        send_telegram_message("","sa nu uiti sa uzi floarea, boss")
    # Generate a timestamp for the received data
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # timestamps.append(timestamp)
    
    # add to db
    db.child("sensors").child(data["ID"]).child("latest_data").set(
        {'air_temperature':temp,'air_humidity':humidity,'soil_humidity':soil_humidity,'luminosity':luminosity,'timestamp':timestamp})
    # db.child("sensors").child(data["ID"]).child("all_data").push(
    #     {'air_temperature':temp,'air_humidity':humidity,'soil_humidity':soil_humidity,'luminosity':luminosity,'timestamp':timestamp})
    
    db.child("sensors").child(data["ID"]).child("all_data").child(timestamp).set(
        {'air_temperature':temp,'air_humidity':humidity,'soil_humidity':soil_humidity,'luminosity':luminosity,'timestamp':timestamp})
    
    
    
    if count >= 5: 
        return jsonify({"status": "success", "message": "0"})
    
    
    
    print(f"Received message: {temp} , {humidity}, {soil_humidity} , {luminosity} ")
    return jsonify({"status": "success", "message": "1"})

# @app.route('/connect_esp32',methods=['GET','POST'])
def connect_esp():
    if request.method == 'POST': 
        id = request.form['id']
        
        print(id)
        # de verificat daca exista senzorul mai intai in db 
        db.child("users").child(session["uid"]).child("sensors").push(id)
        session["sensors"] = session["sensors"] + [ int(id) ]
        
        return redirect(url_for('connect_esp'))
    
    if session.get("is_logged_in", False):
        return render_template('connect_esp.html',devices=session["sensors"])
    else:
        return redirect(url_for('login'))    

# @app.route('/plot/<esp_id>')
def render_plots(esp_id):
    if session.get("is_logged_in", False):
        plots = [(key.replace("_", " ").title(), f"/plot/{esp_id}/{key}") for key in historical_data.keys()]
        return render_template('plot.html', plots=plots)
    else:
        return redirect(url_for('login'))    

def generate_plot(data, timestamps, title, ylabel):
    plt.figure(figsize=(6, 4))
    plt.plot(timestamps, data, marker='o')
    plt.title(title)
    plt.xlabel("Timestamp")
    plt.ylabel(ylabel)
    plt.grid()
    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# @app.route('/plot/<esp_id>/<data_type>')
def serve_plot(esp_id,data_type):
    if not session.get("is_logged_in", False):
        return redirect(url_for('login'))
    
    if data_type not in historical_data:
        return "Invalid data type", 404

    historical_data[data_type] = []
    timestamps = []
    # populate historical_data
    db_h_data=db.child("sensors").child(esp_id).get().val()
    # print(type(db_h_data['all_data']))
    print(type(db_h_data))
    if db_h_data is None or 'all_data' not in db_h_data:
        return 'Senzor data does not exist'
    
    render_data = db_h_data['all_data']
    data_to_plot = OrderedDict(render_data.items())
    cut = min(10,len(data_to_plot.items()))
    # cut = -cut 
    for i in list(reversed(data_to_plot.items()))[:cut]:
        historical_data[data_type].insert(1,i[1][data_type])
        timestamps.insert(1,i[0])
        # historical_data['air_humidity'].insert(1,i[1]['air_humidity'])
        # historical_data['soil_humidity'].insert(1,i[1]['soil_humidity'])
        # historical_data['luminosity'].insert(1,i[1]['luminosity'])
    
    
    
    title_map = {
        "air_temperature": "Air Temperature (°C)",
        "air_humidity": "Air Humidity (%)",
        "soil_humidity": "Soil Humidity (%)",
        "luminosity": "Luminosity (lux)"
    }
    ylabel_map = {
        "air_temperature": "Temperature (°C)",
        "air_humidity": "Humidity (%)",
        "soil_humidity": "Humidity (%)",
        "luminosity": "Luminosity (lux)"
    }

    buf = generate_plot(
        historical_data[data_type],
        timestamps,
        title_map[data_type],
        ylabel_map[data_type]
    )

    return send_file(buf, mimetype='image/png')








# if __name__ == '__main__':
#     app.add_url_rule('/plot/<esp_id>/<data_type>', view_func=serve_plot,methods=['GET'])
#     app.add_url_rule('/plot/<esp_id>', view_func=render_plots,methods=['GET'])
#     app.add_url_rule('/connect_esp32', view_func=connect_esp,methods=['GET','POST'])
#     app.add_url_rule('/receive', view_func=receive_data,methods=['POST'])
#     app.add_url_rule('/latest_data/<esp_id>', view_func=start,methods=['GET'])
#     app.add_url_rule('/logout', view_func=logout,methods=['GET'])
#     app.add_url_rule('/reset_password', view_func=reset_password,methods=['GET','POST'])
#     app.add_url_rule('/dashboard', view_func=dashboard,methods=['GET'])
#     app.add_url_rule('/register', view_func=register,methods=['GET','POST'])
#     app.add_url_rule('/result', view_func=result,methods=['GET','POST'])
#     app.add_url_rule('/welcome', view_func=welcome,methods=['GET'])
#     app.add_url_rule('/signup', view_func=signup,methods=['GET'])
#     app.add_url_rule('/', view_func=login,methods=['GET'])
#     app.run(host='0.0.0.0', port=5000,threaded=True)
