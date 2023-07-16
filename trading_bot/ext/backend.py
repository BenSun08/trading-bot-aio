# reference: https://zhuanlan.zhihu.com/p/100752901

from flask import Flask
from flask import request
from keras.preprocessing import sequence
from keras.preprocessing.text import Tokenizer
from keras.models import load_model
import json
import numpy as np

from trading_bot.agent import Agent

app = Flask(__name__)

#load model
model_name = "models/doubledqn_goog.h5"
agent = load_model(model_name)

window_size = 10
strategy = 'dqn'
pretrained = True

def get_stock_data(data):
    if type(data) is np.ndarray:
        raise Exception("Numpy input is required")
    try:
        return data[:window_size]
    except:
        print("input sequence requires minimal length of {}, while current shape is {}".format(window_size, data.size()))

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route("/predict", methods=["GET","POST"])
def predict():
    data = request.get_json()
        
    cost, profit = -1., -1.
    
    if 'bid_price' not in data:
        return {'result': 'no bid_price input', 'cost':cost, 'profit':profit}
    if 'ask_price' not in data:
        return {'result': 'no ask_price input', 'cost':cost, 'profit':profit}
    if 'bid_size' not in data:
        return {'result': 'no bid_size input', 'cost':cost, 'profit':profit}
    if 'ask_size' not in data:
        return {'result': 'no ask_size input', 'cost':cost, 'profit':profit}
    
    if 'balance' not in data:
        return {'result': 'please specify balance', 'cost':cost, 'profit':profit}
    
    bid_price = data['bid_price']
    ask_price = data['ask_price']
    bid_size = data['bid_size']
    ask_size = data['ask_size']
    balance = data['balance']
    
    mid_price = (bid_price + ask_price)/2
    
    agent = Agent(window_size, strategy=strategy, pretrained=pretrained, model_name=model_name)
    action = agent.act(mid_price, is_eval=True)

    
    if action == 1:
        cost = bid_price * bid_size
        if balance >= cost:
            cost, profit = bid_price * bid_size, 0.
        
    # SELL
    elif action == 2:
        cost, profit = 0., ask_price * ask_size
        
    # HOLD
    else:
        pass
    
    # if buy, balance -= cost
    # if sell, balance += profit
    return {'result':action.tolist(), 'cost':cost, 'profit':profit}

if __name__ == '__main__':
    app.run()