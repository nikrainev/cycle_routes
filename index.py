import json
import requests
import os
from db_repository import Repository
from services import perform_request, perform_callback
from notifications_service import send_notifications

db = Repository()

def handler(event, context):
    if event.get('body') is not None:
        message = json.loads(event['body'])
        if 'callback_query' in message.keys():
            chat_id = message['callback_query']['message']['chat']['id']
            perform_callback(chat_id, db, message['callback_query']['data'])
        else:   
            perform_request(message['message'], db)
    elif event.get('event_metadata') is not None:
        if (event['event_metadata']['event_type'] == 'yandex.cloud.events.serverless.triggers.TimerMessage'):
            send_notifications(db)

    return {
        'statusCode': 200
    }
