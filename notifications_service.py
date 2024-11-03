import os
import json
import requests

TG_TOKEN=os.getenv('BOT_TOKEN')
URL = f"https://api.telegram.org/bot{TG_TOKEN}/"

def send_text(reply, chat_id):
    url = URL + f"sendMessage?text={reply}&chat_id={chat_id}"
    requests.get(url)

def send_notifications(db):
    result = db.find_users_with_locations()
    weatherArr = []
    for user in result:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={user['lat']}&longitude={user['long']}&hourly=temperature_2m&forecast_days=1"
        
        response = requests.get(url)
        response = json.loads(response.text)
        print(response)
    
        weatherArr.append({
            'chat_id': user['chat_id'],
            'temperatureStr': f"Сегодня в 18:00 обещают хорошую погоду: {response['hourly']['temperature_2m'][18]}°C, самое время найти отличный маршрут!"
        })
    
    for weather in weatherArr:
        send_text(weather['temperatureStr'], weather['chat_id'])   
