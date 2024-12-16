from flask import Flask, request, jsonify, render_template,send_file
from flask_cors import CORS, cross_origin
app = Flask(__name__)
# cors = CORS(app) # allow CORS for all domains on all routes.
# app.config['CORS_HEADERS'] = 'Content-Type'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from datetime import datetime
import base64


latest_data = {
    "air_temperature": "N/A",
    "air_humidity": "N/A",
    "soil_humidity": "N/A",
    "luminosity":"N/A"
}

historical_data = {
    "air_temperature": [],
    "air_humidity": [],
    "soil_humidity": [],
    "luminosity": []
}

timestamps = []


@app.route('/latest_data', methods=['GET'])
def start():
    return render_template('index.html',air_t=latest_data["air_temperature"],
                           air_h=latest_data["air_humidity"],
                           soil_h=latest_data["soil_humidity"],
                           lum=latest_data["luminosity"])


@app.route('/receive', methods=['POST'])
def receive_data():
    global latest_data, historical_data, timestamps
    data = request.get_json()  # Parse incoming JSON data
    if not data or 'air_temperature' not in data or 'air_humidity' not in data or 'soil_humidity' not in data or 'luminosity' not in data:
        return jsonify({"error": "Invalid data"}), 400

    print(data)
    
    temp = data['air_temperature']
    humidity = data['air_humidity']
    soil_humidity = data['soil_humidity']
    luminoisty = data['luminosity']
    
    latest_data['air_temperature']  = temp
    latest_data['air_humidity']  = humidity
    latest_data['soil_humidity']  = soil_humidity
    latest_data['luminosity']  = luminoisty
    
    historical_data["air_temperature"].append(float(temp))
    historical_data["air_humidity"].append(float(humidity))
    historical_data["soil_humidity"].append(float(soil_humidity))
    historical_data["luminosity"].append(float(luminoisty))
    
    # Generate a timestamp for the received data
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamps.append(timestamp)
    print(f"Received message: {temp} , {humidity}, {soil_humidity} , {luminoisty} ")
    return jsonify({"status": "success", "message": "succ_trimis"})




@app.route('/plot')
def render_plots():
    plots = [(key.replace("_", " ").title(), f"/plot/{key}") for key in historical_data.keys()]
    return render_template('plot.html', plots=plots)

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

@app.route('/plot/<data_type>')
def serve_plot(data_type):
    
    if data_type not in historical_data:
        return "Invalid data type", 404

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



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Adjust port as needed, threaded=True
