import requests
import json
from recommendations_service import get_user_next_prediction

def get_access_token():
    url = 'https://api.bikemap.net/api/v4/oauth2/access_token'
    headers = {
        'authority': 'www.bikemap.net',
        'method': 'POST',
        'path': '/api/v4/oauth2/access_token',
        'scheme': 'https',
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
        'content-length': '221',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': 'csrftoken=bfdGP1q20dwtWe9eycSA8XIeCcmXPeIH; _ga=GA1.1.569867730.1730209131; outdoorish_language=ru; outdoorish_unit=metric; sessionid=2949b5t99ogf43a4o0nzi3e4m1qv0y5b; _ga_GLZ6LEKYFK=GS1.1.1730209130.1.1.1730209205.0.0.0',
        'origin': 'https://web.bikemap.net',
        'priority': 'u=1, i',
        'referer': 'https://web.bikemap.net/',
        'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    }

    response = requests.post(url, headers=headers, data = {
        'client_id': 'HjatjjiIHMqRkv5CCf3R0f8gpmnJUGVBCsALQexy',
        'client_secret': 'c2iI0VM6bEZgNbuY0kjudHf3FXoEKTqpMf7DHywd5NnHvd99o13OBaVugFbEHem8DiIJYL7VWrKlLaqnOF6lhepuIa54yImZMw20xJqjbpodX1GCzZEINyQB5Zq3wsvK',
        'grant_type': 'web_access_token'
    })

    return json.loads(response.text)

def get_variant(user, db):
    user_last_prediction = db.get_user_last_prediction(user['chat_id'])
    
    page_number = 1

    query_settings = {
        'distanceRange': {
            'min': 10,
            'max': 1000000,
        },
        'isLoop': False
    }

    if (user_last_prediction is not None):
        page_number = user_last_prediction['pageNumber'] + 1
        query_settings = get_user_next_prediction(db, user['chat_id'])
    else:
        db.set_user_matching_status(user['chat_id'])    
        
    long_south_west = user.long - 0.08
    lat_south_west = user.lat - 0.08

    long_north_east= user.long + 0.08
    lat_north_east = user.lat + 0.08
    
    bounds = f"{long_south_west}%2C{ lat_south_west}%2C{long_north_east}%2C{lat_north_east}"
    
    print(query_settings)
    response = make_request_to_bike_map(get_access_token()['access_token'], bounds, page_number, query_settings['distanceRange']['min'], query_settings['distanceRange']['max'])
    
    result = response.get('results')
    
    if result is None:
        return
    
    if len(result) == 0:
        return 
    result = result[0]
    
    prediction_id = db.set_user_prediction(
        chat_id = user['chat_id'],
        count = response['count'],
        distance = result['content_object']['distance'],
        pageNumber = page_number,
        altitudeDifference = result['content_object']['altitude_difference'],
        isLoop = result['content_object']['is_loop'],
        category = 0,
        routeId = result['content_object']['id'],
    )
    
    return {
        'distance': result['content_object']['distance'],
        'imageSrc': result['content_object']['staticmap'],
        'routeId': result['content_object']['id'],
        'prediction_id': prediction_id
    }
    

def make_request_to_bike_map(access_token:str, bounds:str, page:int, distanceMin:int, distanceMax:int):
    response = requests.get(f"https://www.bikemap.net/api/v5/search/?page_size=1&page={page}&sort=relevance&sort_order=desc&route_type=user&bounds={bounds}&score_nearby=false&distance_min={distanceMin}&distance_max={distanceMax}&ascent=0&ascent=3001&categories=1&categories=2&categories=4&surface_tags=paved_all%2Cunpaved_all%2Cgravel%2Cground", headers={
        'Authorization': f"Bearer {access_token}"
    })

    return json.loads(response.text)
