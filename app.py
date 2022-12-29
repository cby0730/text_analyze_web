from flask import Flask, redirect, url_for, request, render_template, session
from dotenv import load_dotenv
import os
import requests,json
import openai
openai.api_key = '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'
# Import namespaces
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def index_post():
    if request.form['type'] == "analyze":
        return analyzePage()
    elif request.form['type'] == 'translate':
        return translatePage()
    elif request.form['type'] == 'ask':
        return chatgptPage()

def chatgptPage() :

    msg = request.form['text']
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=msg,
        max_tokens=3999,
        temperature=0.5
    )

    completed_text = response['choices'][0]['text']

    return render_template('openai.html',
                            original=msg,
                            response=completed_text)


def analyzePage():
    lan = ""
    sent = ""
    phrases_list = []
    entities_list = []
    link_list = []
    try:        # Get Configuration Settings
        load_dotenv()
        cog_endpoint = os.getenv('COG_SERVICE_ENDPOINT')
        cog_key = os.getenv('COG_SERVICE_KEY')

        # Create client using endpoint and key
        credential = AzureKeyCredential(cog_key)
        cog_client = TextAnalyticsClient(
            endpoint=cog_endpoint, credential=credential)

        text = request.form['text']
        # Get language
        detectedLanguage = cog_client.detect_language(documents=[text])[0]
        lan = '\n{}'.format(detectedLanguage.primary_language.name)

        # # Get sentiment
        sentimentAnalysis = cog_client.analyze_sentiment(documents=[text])[0]
        # print("\nSentiment: {}".format(sentimentAnalysis.sentiment))
        sent = "\n{}".format(sentimentAnalysis.sentiment)

        # # Get key phrases
        phrases = cog_client.extract_key_phrases(documents=[text])[
            0].key_phrases
        if len(phrases) > 0:
            # print("\nKey Phrases:")
            for phrase in phrases:
                # print('\t{}'.format(phrase))
                phrases_list.append('\t{}'.format(phrase))

        # # Get entities
        entities = cog_client.recognize_entities(documents=[text])[0].entities
        if len(entities) > 0:
            for entity in entities:
                entities_list.append('\t{} ({})'.format(
                    entity.text, entity.category))

        # # Get linked entities
        entities = cog_client.recognize_linked_entities(documents=[text])[
            0].entities
        if len(entities) > 0:
            for linked_entity in entities:
                link_list.append('\t{} ({})'.format(
                    linked_entity.name, linked_entity.url))

        return render_template('analyzeResult.html',
                               original=text,
                               language=lan,
                               sentiment=sent,
                               phrases=phrases_list,
                               entities=entities_list,
                               link=link_list)

    except Exception as ex:
        print(ex)


def translatePage():
    try:
        # Get Configuration Settings
        load_dotenv()
        cog_key = os.getenv('COG_SERVICE_KEY')
        cog_region = os.getenv('COG_SERVICE_REGION')
        translator_endpoint = 'https://api.cognitive.microsofttranslator.com'

        text = request.form['text']

        def GetLanguage(text):
            # Default language is English
            language = 'en'

            # Use the Translator detect function
            # Use the Translator detect function
            path = '/detect'
            url = translator_endpoint + path

            # Build the request
            params = {
                'api-version': '3.0'
            }

            headers = {
                'Ocp-Apim-Subscription-Key': cog_key,
                'Ocp-Apim-Subscription-Region': cog_region,
                'Content-type': 'application/json'
            }

            body = [{
                'text': text
            }]

            # Send the request and get response
            request = requests.post(
                url, params=params, headers=headers, json=body)
            response = request.json()

            # Parse JSON array and get language
            language = response[0]["language"]

            # Return the language
            return language

        def Translate(text, source_language, tarrget_lan):
            translation = ''

            # Use the Translator translate function
            # Use the Translator translate function
            path = '/translate'
            url = translator_endpoint + path

            # Build the request
            params = {
                'api-version': '3.0',
                'from': source_language,
                'to': [tarrget_lan]
            }

            headers = {
                'Ocp-Apim-Subscription-Key': cog_key,
                'Ocp-Apim-Subscription-Region': cog_region,
                'Content-type': 'application/json'
            }

            body = [{
                'text': text
            }]

            # Send the request and get response
            request = requests.post(
                url, params=params, headers=headers, json=body)
            response = request.json()

            # Parse JSON array and get translation
            translation = response[0]["translations"][0]["text"]

            # Return the translation
            return translation
        
        # Get language
        lan = GetLanguage(text)
        tarrget_lan = request.form['language']

        # Translate if not already English
        translatedText = Translate(text,lan, tarrget_lan)

        return render_template('translateResult.html',
                               original=text,
                               language=lan,
                               translated=translatedText)

    except Exception as ex:
        print(ex)


#app.run()
