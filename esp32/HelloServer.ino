
#include "DHT.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <Arduino_JSON.h>

#define soil_humidity_pin  33
#define luminozity_pin 32
#define dht22_senzor_pin 4
#define buzzer_senzor_pin 5

#define DHTPIN 4
#define DHTTYPE DHT21     

DHT dht(DHTPIN, DHTTYPE);

int air_temperature = 0;
int air_humidity = 0;
int soil_humidity = 0;
int luminosity = 0;


const char *ssid = "Trollus iPhone";
const char *password = "oliver2003";
// const char *ssid = "DIGI_cce578";
// const char *password = "989d331a";


const char* serverUrl = "http://172.20.10.2:5000/receive";


void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("\nConnected to WiFi");
  
  
  pinMode(buzzer_senzor_pin, OUTPUT);
  dht.begin();
}

void loop() {
  // read sensor data 

  // read DHT21 sensor 
  // float temperature = 0;
  // float humidity = 0;
  // int err = SimpleDHTErrSuccess;
  // if ((err = dht22.read2(&temperature, &humidity, NULL)) != SimpleDHTErrSuccess) {
  //   Serial.print("Read DHT22 failed, err="); Serial.print(SimpleDHTErrCode(err));
  //   Serial.print(","); Serial.println(SimpleDHTErrDuration(err)); delay(2000);
  //   // return;
  // }
  float h = dht.readHumidity();
  // Read temperature as Celsius (the default)
  float t = dht.readTemperature();  
  air_temperature  = t;
  air_humidity = h; 
  Serial.print("Sample OK: ");
  Serial.print(t); Serial.print(" *C, ");
  Serial.print(h); Serial.println(" RH%");
  


  Serial.print("Soil humidity: ");
  int sensorValue = analogRead(soil_humidity_pin);  // Read the analog value from sensor
  soil_humidity = map(sensorValue, 0, 1023, 255, 0); // map the 10-bit data to 8-bit data
  Serial.print(soil_humidity);
  Serial.println("");

  Serial.print("Luminosity: ");
  int luminosity = analogRead(luminozity_pin);  // Read the analog value from sensor
  Serial.print(luminosity);
  Serial.println("");

  // activate buzzer
  tone(buzzer_senzor_pin, 500);



  // connect to wifi
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    // Specify the URL
    http.begin(serverUrl);

    // Add headers
    http.addHeader("Content-Type", "application/json");
    
    // Create JSON payload
    JSONVar jsonPayload;
    jsonPayload["air_temperature"] = air_temperature;
    jsonPayload["air_humidity"] = air_humidity;
    jsonPayload["soil_humidity"] = soil_humidity;
    jsonPayload["luminosity"] = luminosity;
    // jsonPayload["message"] = "Hello, this is a detailed POST request from ESP32.";

    String jsonString = JSON.stringify(jsonPayload);

    // Send the POST request
    int httpResponseCode = http.POST(jsonString);

    // Handle response
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Server response:");
      Serial.println(response);
    } else {
      Serial.print("Error on sending POST: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }




  // 10000 - 10 secunde 
  // 2500 -2.5 secunde 

  delay(2500);  
}
