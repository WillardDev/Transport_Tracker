import requests
import json

API_KEY = "6e3857d7459724609e7f52369f807aa4"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


KENYAN_TOWNS = [
    "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika", "Malindi",
    "Naivasha", "Nyeri", "Nanyuki", "Meru", "Embu", "Machakos", "Kitui",
    "Garissa", "Wajir", "Mandera", "Isiolo", "Marsabit", "Lodwar", "Kitale",
    "Kakamega", "Bungoma", "Busia", "Kisii", "Migori", "Homa Bay", "Siaya",
    "Voi", "Lamu", "Kilifi", "Kwale", "Ukunda", "Narok", "Ngong", "Kikuyu",
    "Ruiru", "Juja", "Limuru", "Kiambu", "Muranga", "Kerugoya", "Karatina",
    "Molo", "Eldama Ravine", "Kabarnet", "Rongai", "Athi River", "Kitengela",
    "Mariakani", "Sagana", "Makindu", "Sultan Hamud", "Wote", "Makueni",
    "Mwingi", "Mbale", "Kapsabet", "Iten", "Othaya", "Mutomo", "Lokichogio",
    "Kimilili", "Webuye", "Mumias", "Butere", "Port Victoria", "Nyamira",
    "Keroka", "Sotik", "Sare", "Kendu Bay", "Oyugis", "Rachuonyo",
    "Muhoroni", "Ahero", "Bomet", "Sotik", "Taveta", "Taita",
    "Kangundo", "Matuu", "Kathiani", "Tala", "Githunguri", "Ndumberi",
    "Wangige", "Kahawa", "Kasarani", "Utawala", "Pipeline", "Donholm",
]

def validate_kenyan_city(city):
    city_lower = city.strip().lower()
    for town in KENYAN_TOWNS:
        if town.lower() == city_lower:
            return town
    return None


def get_weather(city="Nairobi"):
    try:
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        }
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            return {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["main"],
            }
        else:
            return None
    except requests.exceptions.RequestException:
        return None
    except (json.JSONDecodeError, KeyError):
        return None


def is_rainy(weather_data):
    if weather_data is None:
        return False
    rainy_conditions = ["Rain", "Drizzle", "Thunderstorm", "Squall"]
    return weather_data["condition"] in rainy_conditions


def get_fare_alert(weather_data):
    if weather_data is None:
        return "Could not fetch weather data. No fare alert available."

    temp = weather_data["temperature"]
    condition = weather_data["description"]
    is_rain = is_rainy(weather_data)

    alert = f"Weather: {condition.title()}, {temp:.1f}°C\n"

    if is_rain:
        alert += "RAIN ALERT: Fares may spike today due to rain.\n"
        alert += "Plan ahead and carry extra fare."
    elif temp > 35:
        alert += "Hot day alert: Stay hydrated while waiting for matatus."
    elif temp < 15:
        alert += "Cold weather: Matatus may be fewer. Leave early."
    else:
        alert += "Weather is fair. Fares should be at normal rates."

    return alert
