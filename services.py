import os
import json
import requests

from bikemap_service import get_variant
UserStatuses = {
    'INITIAL': 1,
    'LOCATION_SET': 2,
    'MATCHING_STARTED': 3
}

TG_TOKEN=os.getenv('BOT_TOKEN')
URL = f"https://api.telegram.org/bot{TG_TOKEN}/"

def send_text(reply, chat_id):
    url = URL + f"sendMessage?text={reply}&chat_id={chat_id}"
    requests.get(url)

def create_keyboard(prediction_id):
    return json.dumps(
        {
            "inline_keyboard":[
                [{ "text": "Дизлайк", "callback_data": f"{prediction_id}_no"},
                 { "text": "Лайк", "callback_data": f"{prediction_id}_yes"}]
            ]
        }
    )

def send_pic(chat_id, prediction_id, map_src, route_id, distance): 
    url = URL + "sendPhoto"
    data = {
        'photo': map_src,
        'chat_id': chat_id,
        'caption': f"Расстояние: {distance // 1000}км, ссылка на маршрут: https://web.bikemap.net/r/{route_id}",
        'parse_mode': 'Markdown',
        'reply_markup': create_keyboard(prediction_id)
    }
    requests.post(url, data=data)

def perform_callback(chat_id, db, action_data):
    split_arr = action_data.split('_')
    if len(split_arr) > 0:
        if split_arr[1] == 'yes':
            db.set_prediction_result(prediction_id = split_arr[0], is_like = True)
        else:
            db.set_prediction_result(prediction_id = split_arr[0], is_like = False)

    user = db.get_user(int(chat_id))
    predictionResult = get_variant(user, db)
    return send_pic(chat_id = int(chat_id), prediction_id = predictionResult['prediction_id'], map_src = predictionResult["imageSrc"], route_id = predictionResult["routeId"], distance = predictionResult["distance"])

def perform_request(message, db):
    chat_id = message['chat']['id']
    user = db.get_user(int(chat_id))

    if user is None:
        db.add_user(int(chat_id))

    user = db.get_user(int(chat_id))

    if user['status'] == UserStatuses['INITIAL']:
        if message.get('location') is None:
            return failed_startup_message(chat_id)
        else:
            location = message.get('location')
            db.set_user_geo_info(int(chat_id), location['latitude'] , location['longitude'])
            return success_start_up_message(chat_id)
    if user['status'] == UserStatuses['LOCATION_SET']:
        if message.get('text') == '/search':
            predictionResult = get_variant(user, db)
            return send_pic(chat_id = int(chat_id), prediction_id = predictionResult['prediction_id'], map_src = predictionResult["imageSrc"], route_id = predictionResult["routeId"], distance = predictionResult["distance"])
        else:
            return failed_matching_message(chat_id)
    return 0

def failed_startup_message(chat_id):
    send_text("Чтобы начать использовать бота отправьте сообщение с гео-локацией", chat_id)
    return 0

def success_start_up_message(chat_id):
    send_text("Отлично! Чтобы начать подбор маршрута отправьте /search", chat_id)
    return 0

def failed_matching_message(chat_id):
    send_text("Чтобы начать подбор маршрута отправьте /search", chat_id)
    return 0
