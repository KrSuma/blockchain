from datetime import datetime, date, timedelta
import requests, json, re, os, time
from itertools import count
import http.client

sentiment_key = '1eb20bbf70msh12e87c73d706fcdp12edb5jsn8f0ea53ec57b'
websearch_key = '1eb20bbf70msh12e87c73d706fcdp12edb5jsn8f0ea53ec57b'

crypto_key_pairs = {"BTCUSD": "Bitcoin", "BCHUSD": 'Bitcoin Cash', "ETHUSD": "Ethereum", "LTCUSD": "Litecoin", "XRPUSD": "Ripple",
                    "ETCUSD": "ETC", "VET":'VeChain', "XNO": 'Xeno Token', "STEEM": 'Steem',
                    "XLMUSD": "Stellar Lumens", "XMRUSD": "Monero", "STCUSD": "Student Coin",
                    "LUNA": 'Luna', "ANC": 'Anchor Protocol', "MIR": 'Mirror Protocol'}

date_since = date.today() - timedelta(days=1)

cryptocurrencies = []
crypto_keywords = []

for i in range(len(crypto_key_pairs)):
    cryptocurrencies.append(list(crypto_key_pairs.keys())[i])
    crypto_keywords.append(list(crypto_key_pairs.values())[i])


def get_news_headlines():
    """
    search the web for news headlines based on keywords on global var
    :return: the news output dictionary
    """
    news_output = {}

    for crypto in crypto_keywords:
        # create empty dicts in the news output
        news_output["{0}".format(crypto)] = {'description': [], 'title': []}

        url = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/search/NewsSearchAPI"
        querystring = {"q": str(crypto), "pageNumber": "1", "pageSize": "30", "autoCorrect": "true",
                       "fromPublishedDate": date_since, "toPublishedDate": "null"}
        headers = {
            'x-rapidapi-key': websearch_key,
            'x-rapidapi-host': "contextualwebsearch-websearch-v1.p.rapidapi.com"
        }

        # get raw response
        response = requests.request("GET", url, headers=headers, params=querystring)

        # convert response to text format
        result = json.loads(response.text)

        # store headline descriptions
        for news in result['value']:
            news_output[crypto]["description"].append(news["description"])
            news_output[crypto]["title"].append(news['title'])

    return news_output


def analyze_headlines():
    """
    analyze healines pulled through the api for each cryptocurrency
    :return: news_output
    """
    news_output = get_news_headlines()

    for crypto in crypto_keywords:
        # empty list to store sentient value
        news_output[crypto]['sentiment'] = {'pos': [], 'mid': [], 'neg': []}
        # analyze descriptions
        if len(news_output[crypto]['description']) > 0:
            for title in news_output[crypto]['title']:
                # regex
                titles = re.sub('[^A-Za-z0-9]+', ' ', title)

                conn = http.client.HTTPSConnection('text-sentiment.p.rapidapi.com')

                # format
                payload = 'text=' + titles
                headers = {
                    'content-type': 'application/x-www-form-urlencoded',
                    'x-rapidapi-key': sentiment_key,
                    'x-rapidapi-host': 'text-sentiment.p.rapidapi.com'
                }
                conn.request("POST", "/analyze", payload, headers)

                # get response and format it
                res = conn.getresponse()
                data = res.read()
                title_sentiment = json.loads(data)

                if not isinstance(title_sentiment, int):
                    if title_sentiment['pos'] == 1:
                        news_output[crypto]['sentiment']['pos'].append(title_sentiment['pos'])
                    elif title_sentiment['mid'] == 1:
                        news_output[crypto]['sentiment']['mid'].append(title_sentiment['mid'])
                    elif title_sentiment['neg'] == 1:
                        news_output[crypto]['sentiment']['neg'].append(title_sentiment['neg'])
                    else:
                        print(f'sentiment not found for {crypto}')

    return news_output


def calc_sentiment():
    news_output = analyze_headlines()

    for crypto in crypto_keywords:
        if len(news_output[crypto]['title']) > 0:
            news_output[crypto]['sentiment']['pos'] = len(news_output[crypto]['sentiment']['pos']) * 100 / len(
                news_output[crypto]['title'])
            news_output[crypto]['sentiment']['mid'] = len(news_output[crypto]['sentiment']['mid']) * 100 / len(
                news_output[crypto]['title'])
            news_output[crypto]['sentiment']['neg'] = len(news_output[crypto]['sentiment']['neg']) * 100 / len(
                news_output[crypto]['title'])

            # print the output  for each coin to verify the result
            print(crypto, news_output[crypto]['sentiment'])

    return news_output


if __name__ == '__main__':
    for i in count():
        calc_sentiment()
        print(f'Iteration {i}')
        time.sleep(900)

