import os
import requests
from dotenv import load_dotenv
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from twilio.rest import Client

load_dotenv()


@dataclass
class Config:
    stock_api_key: str
    news_api_key: str
    twilio_phone: str
    twilio_sid: str
    twilio_token: str
    today: str
    yesterday: str


def process_stock_data(stock_dict: Dict, _config: Config) -> Tuple[float, float]:
    close_today = float(stock_dict[_config.today]['4. close'])
    close_yesterday = float(stock_dict[_config.yesterday]['4. close'])
    abs_variation = round((close_today - close_yesterday), 2)
    perc_variation = round(((close_today - close_yesterday) / close_yesterday) * 100, 2)
    return abs_variation, perc_variation


def process_news_data(news_dict: Dict) -> Dict:
    print(news_dict.keys())
    title = news_dict['title']
    description = news_dict['description']
    source = news_dict['source']['name']
    _temp_dict = {
        "title": title,
        "brief": description,
        "from": source
    }
    return _temp_dict


def send_message(_config: Config, body: str):
    client = Client(_config.twilio_sid, _config.twilio_token)
    message = client.messages.create(
        body=body,
        from_=_config.twilio_phone,
        to='+XXXXXXX' #TODO: Replace number
    )
    return message.status


def prepare_msg(stock_name: str, abs_variation: float, perc: float, top_news: Dict) -> str:
    if perc > 0:
        reaction = "🎉"
    else:
        reaction = "🔻"

    body_msg = f"""{stock_name}: {reaction} {abs_var} - ${abs_variation}
    Headline: {top_news['title']}
    Brief: {top_news['brief']}
    Source: {top_news['from']}
    """
    return body_msg


today = datetime.today().strftime("%Y-%m-%d")
yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

config = Config(
    stock_api_key=os.environ.get('STOCK_API_KEY'),
    news_api_key=os.environ.get('NEWS_API_KEY'),
    twilio_phone=os.environ.get("TWILIO_PHONE"),
    twilio_sid=os.environ.get("TWILIO_SID"),
    twilio_token=os.environ.get("TWILIO_TOKEN"),
    today=today,
    yesterday=yesterday
)

STOCK = "AMZN"
COMPANY_NAME = "Amazon Inc"

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

stock_response = requests.get(
    url=STOCK_ENDPOINT,
    params={
        "function": "TIME_SERIES_DAILY",
        "symbol": STOCK,
        "apikey": config.stock_api_key,
    }
)
stock_response.raise_for_status()
stock_data = stock_response.json()["Time Series (Daily)"]
abs_var, perc_var = process_stock_data(stock_dict=stock_data, _config=config)

# Get the news
news_response = requests.get(
    url=NEWS_ENDPOINT,
    params={
        "q": COMPANY_NAME,
        "from": config.yesterday,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 1,
        "apiKey": config.news_api_key,
    }
)
news_response.raise_for_status()
news_articles = news_response.json()['articles']
top_headline = process_news_data(news_articles[0])

# Send message
msg = prepare_msg(STOCK, abs_var, perc_var, top_headline)
print(msg)
msg_response = send_message(_config=config, body=msg)
print(msg_response)
