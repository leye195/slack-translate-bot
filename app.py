from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt import App
import requests

SLACK_BOT_TOKEN = ''  
SLACK_SIGNING_SECRET = '' 

client_id = "" # papago API Client ID 
client_secret = "" # papago API Client Secret 
header = {"X-Naver-Client-Id":client_id,
          "X-Naver-Client-Secret":client_secret}
base_url = "https://openapi.naver.com/v1/papago/"

def detect_language(text):
    url = base_url + "detectLangs"

    data = {
        'query': text
    }

    response = requests.post(url, headers = header, data = data) 
    rescode = response.status_code

    if(rescode==200):
        t_data = response.json()
        return t_data['langCode']
    else:
        print('detectLangs Error Code:', rescode)

def get_translate(text):
    url = base_url + "n2mt" # API url
    
    source = detect_language(text) # get LanguageCode for source language
    
    if source=='en':
        data = {'text' : text,
            'source' : source,
            'target': 'ko'
        } # translate to Korean

        response = requests.post(url, headers = header, data = data)
        rescode = response.status_code

        if(rescode==200):
            t_data = response.json()
            print(t_data['message']['result']['translatedText'])
            return ':kr: '+t_data['message']['result']['translatedText']
        else:
            print("n2mt Error Code:" , rescode)
    elif source=='ko':
        data = {'text' : text,
            'source' : source,
            'target': 'en'
        } # translate to Korean

        response = requests.post(url, headers=header, data=data)
        rescode = response.status_code

        if(rescode==200):
            t_data = response.json()
            print(t_data['message']['result']['translatedText'])
            return ':us: '+t_data['message']['result']['translatedText']
        else:
            print("n2mt Error Code:" , rescode)

app = App(token = SLACK_BOT_TOKEN, signing_secret = SLACK_SIGNING_SECRET)

@app.event("app_mention")
def handle_mention(event,client):
    text = event['text']
    translated_text = get_translate(text)

    client.chat_postMessage(
        channel = event['channel'],
        attachments = [
		    {
			    "blocks": [
				    {
					    "type": "section",
					    "text": {
							"type": "mrkdwn",
							"text": translated_text,
						}
				    }
			    ]
		    },
	    ],
        thread_ts = event['ts']
    )


@app.shortcut({"callback_id": "t_action", "type": "message_action"})
def t_action(ack, shortcut, client):
    ack()

    channel_id = shortcut['user']['id']
    if('channel' in shortcut):        
        channel_id = shortcut['channel']['id']
    
    timestamp = shortcut['message_ts']
    text = shortcut['message']['text']


    if('thread_ts' in shortcut['message']):
        timestamp = shortcut['message']['thread_ts']
    translated_text = get_translate(text) 
    #print('shortcut: ', translated_text)

    client.chat_postMessage(
        channel = channel_id,
        attachments = [
		    {
			    "blocks": [
				    {
					    "type": "section",
					    "text": {
							"type": "mrkdwn",
							"text": translated_text,
						}
				    }
			    ]
		    },
	    ],
        #reply_broadcast = True,
        thread_ts = timestamp
    )

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)
