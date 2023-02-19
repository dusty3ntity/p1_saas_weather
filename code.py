import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

# API: https://www.weatherapi.com/

API_TOKEN = "123asd123"
API_KEY = ""
BASE_URL = "http://api.weatherapi.com/v1"

app = Flask(__name__)


def get_forecast_weather(location, date):
    url = f"{BASE_URL}/forecast.json?key={API_KEY}&q={location}&days=10&aqi=no&alerts=no"

    response = requests.request("GET", url, headers={}, data={})
    response.raise_for_status()
    responseData = response.json()

    weather = responseData["forecast"]["forecastday"]

    was_date_found = False
    for i in weather:
        if i["date"] == date:
            was_date_found = True
            weather = i["day"]
            weather["debug_date"] = i["date"]
            break;

    if not was_date_found:
        # for some reason, weatherapi.com only provides forecast for the next 10 days from today, 
        # and the "future" endpoint is only available for dates after 14 days from today
        weather = "sorry, no forecast is available for the given data"
    else:
        weather["debug_location"] = responseData["location"]

    return weather


def get_past_weather(location, date):
    url = f"{BASE_URL}/history.json?key={API_KEY}&q={location}&dt={date}"

    response = requests.request("GET", url, headers={}, data={})
    response.raise_for_status()
    responseData = response.json()
    weather = responseData["forecast"]["forecastday"][0]["day"]

    weather["debug_location"] = responseData["location"]
    weather["debug_date"] = responseData["forecast"]["forecastday"][0]["date"]
    
    return weather


def get_future_weather(location, date):
    url = f"{BASE_URL}/future.json?key={API_KEY}&q={location}&dt={date}"

    response = requests.request("GET", url, headers={}, data={})
    response.raise_for_status()
    responseData = response.json()
    weather = responseData["forecast"]["forecastday"][0]["day"]

    weather["debug_location"] = responseData["location"]
    weather["debug_date"] = responseData["forecast"]["forecastday"][0]["date"]
    
    return weather


def get_weather(location: str, date: str):
    date_obj = dt.datetime.strptime(date, '%Y-%m-%d')

    should_use_past = date_obj.date() < dt.datetime.today().date()
    should_use_future = date_obj >= dt.datetime.today() + dt.timedelta(days=13)

    if should_use_future:
        return get_future_weather(location, date)
    elif should_use_past:
        return get_past_weather(location, date)
    else:
        return get_forecast_weather(location, date)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h1>KMA P1: Python Weather Saas.</h1></p>"


@app.route(
    "/weather",
    methods=["GET"],
)
def weather_endpoint():
    json_data = request.get_json()

    token = json_data.get("token")
    if token is None:
        raise InvalidUsage("token is required", status_code=400)
    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    location = json_data.get("location")
    date = json_data.get("date")

    result = {
        "requester_name": json_data.get("requester_name"),
        "timestamp": dt.datetime.utcnow(),
        "location": location,
        "date": date,
        "weather": get_weather(location, date)
    }

    return result
