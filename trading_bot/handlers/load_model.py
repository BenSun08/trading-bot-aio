from .agent import Agent
from collections import deque
import numpy as np
from random import randint
from datetime import datetime, timedelta
import requests
import json
import asyncio
from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle

window_size = 10
model_name = "trading_bot/models/GOOGscore_doubledqn_50.h5"
strategy = 'dqn'
pretrained = True

def load_model(topic):
    agent = Agent(window_size, strategy=strategy, pretrained=pretrained, model_name=model_name)
    # score = get_score_before_trade(topic)
    score = np.ones_like(window_size) * 5.5
    return { "agent": agent, "score": score }

q = deque(maxlen=window_size)

def fetch_news(topic, date, num_news):
    # Format the date to match the API's required format (yyyy-mm-dd)
    topic = topic.split("/")[0]
    end_date = date.strftime("%Y-%m-%dT%H:%M:%SZ")
    start_date = date - timedelta(days=14)
    start_date = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    # Set your API key here (sign up at gnews.io to get an API key)
    api_key = "1fdb388c9ba3b4b166a93481440fd73e"
    # Create the API request URL
    url = f"https://gnews.io/api/v4/search?q={topic}&from={start_date}&to={end_date}&lang=en&token={api_key}&sortby=relevance&max={num_news}"
    # Send the HTTP GET request to the API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the articles from the response
        articles = response.json()["articles"]
        return articles
    else:
        print("Error:", response.status_code, response.json())

async def get_score(news, topic):
    cookies = json.loads(open("trading_bot/bing_cookies_*.json", encoding="utf-8").read()) # 可能会忽略 cookie 选项
    bot = await Chatbot.create(cookies=cookies)
    prompt = f"Given news as follow: \"{news['description']}\" Give me a score ranges from 0-9 " \
            f"to show whether it is a good news or a bad news for {topic}. " \
            f"Your answer should strictly follow this format: The score is ..., e.g., if the score is 5, then return \"The score is 5.\""
    response = await bot.ask(prompt=prompt,
                            conversation_style=ConversationStyle.creative, simplify_response=True)
    answer = json.dumps(response["text"], indent=2)
    print("Q:", prompt)
    print("A:", answer[:20])
    """
    {
        "text": str,
        "author": str,
        "sources": list[dict],
        "sources_text": str,
        "suggestions": list[str],
        "messages_left": int
    }
    """
    await bot.close()
    return answer

def get_stock_data(data):
    if type(data) is np.ndarray:
        raise Exception("Numpy input is required")
    try:
        return data[:window_size]
    except:
        print("input sequence requires minimal length of {}, while current shape is {}".format(window_size, data.size()))

def get_score_before_trade(topic):
    cur_date_str = datetime.today().strftime('%Y-%m-%d') # need check the format, currently assumed as "YYYY-MM-DD"
    cur_date = cur_date_str.split("-")

    date = datetime(int(cur_date[0]), int(cur_date[1]), int(cur_date[2]))
    articles = fetch_news(topic, date, num_news=3)

    score_cur_week = []
    for j, article in enumerate(articles,1):
        answer = asyncio.run(get_score(article, topic))
        if answer[14].isdigit():
            score_cur_week.append(int(answer[14]))
        else: continue
    score_cur_week = np.array(score_cur_week)
    if len(score_cur_week) == 0:
        score = 4 # mean value
    else:
        score = score_cur_week.mean()
    print("score: ", score)
    scores_arr = np.ones_like(window_size) * score
    return scores_arr

async def make_action(data, agent, make_order, score, test = False):
    print("data: ", data)

    cost, profit = -1., -1.
    
    if 'bid_price' not in data:
        return {'result': 'no bid_price input', 'cost':cost, 'profit':profit}
    if 'ask_price' not in data:
        return {'result': 'no ask_price input', 'cost':cost, 'profit':profit}
    if 'bid_size' not in data:
        return {'result': 'no bid_size input', 'cost':cost, 'profit':profit}
    if 'ask_size' not in data:
        return {'result': 'no ask_size input', 'cost':cost, 'profit':profit}
    # if 'balance' not in data:
    #     return {'result': 'please specify balance', 'cost':cost, 'profit':profit}

    bid_price = data['bid_price']
    ask_price = data['ask_price']
    bid_size = data['bid_size']
    ask_size = data['ask_size']
    mid_price = (bid_price + ask_price)/2
    
    q.append(mid_price)

    print("algo start....")
    try:
        if len(q) == window_size:
            x = np.reshape(list(q), (1, -1))
            if test:
                a = randint(0, 2)
                action = (a, 1.)
            else:    
                action = agent.act_with_score(x, score,is_eval=True)
        else:
            return {'action': 'hold', 'cost':0., 'profit':0. }
    except Exception as e:
        print("algo error: ", e)
        action = (0, 0.)
    print("algo end....")

    order = {}
    print("action: ", action)
    

    act = action[0]
    prob = action[1]

    try:
        if act == 1:
            actStr = 'buy'
            cost =  bid_price * bid_size
            # if balance >= cost:
            cost, profit = bid_price * bid_size, 0.
            order = await make_order('buy')
            
        # SELL
        elif act == 2:
            actStr = 'sell'
            cost, profit = 0., ask_price * ask_size
            order = await make_order('sell')
            
        # HOLD
        else:
            return {'action': 'hold', 'cost':0., 'profit':0. }
    except Exception as e:
        print("algo error: ", e)
        order = { "error": str(e) }

    print("buy order made: ", order)

    res = { 'action': actStr, 'cost':cost, 'profit':profit }
    return { **res, **order }
