from .agent import Agent
from collections import deque
import numpy as np
from random import randint

window_size = 10
model_name = "trading_bot/models/doubledqn_ggl_30.h5"
strategy = 'dqn'
pretrained = True

def load_model():
    agent = Agent(window_size, strategy=strategy, pretrained=pretrained, model_name=model_name)
    return agent

q = deque(maxlen=window_size)
async def make_action(data, agent, make_order, test = False):
    print("data: ", data)
    bid_price = data['bid_price']
    ask_price = data['ask_price']
    bid_size = data['bid_size']
    ask_size = data['ask_size']
    # balance = data['balance']
    
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
                action = agent.act(x, is_eval=True)
        else:
            return {'action': 'hold', 'cost':0., 'profit':0. }
    except Exception as e:
        print("algo error: ", e)
        action = (0, 0.)
    print("algo end....")

    order = {}
    

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
