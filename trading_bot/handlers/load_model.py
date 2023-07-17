from .agent import Agent
import asyncio

model_name = "trading_bot/models/doubledqn_ggl_30.h5"
window_size = 2
strategy = 'dqn'
pretrained = True

def load_model():
    agent = Agent(window_size, strategy=strategy, pretrained=pretrained, model_name=model_name)
    return agent

async def make_action(data, agent, make_order):
    print("data: ", data)
    bid_price = data['bid_price']
    ask_price = data['ask_price']
    bid_size = data['bid_size']
    ask_size = data['ask_size']
    # balance = data['balance']
    
    mid_price = (bid_price + ask_price)/2

    print("algo start....")
    try:
        action = agent.act(mid_price, is_eval=True)
    except Exception as e:
        print("algo error: ", e)
        action = (0, 0.)
    print("algo end....")

    order = {}
    
    print("action that made: ", action)

    act = action[0]
    prob = action[1]

    if act == 1:
        cost =  bid_price * bid_size
        # if balance >= cost:
        cost, profit = bid_price * bid_size, 0.
        order = await make_order('buy')

        print("buy order made: ", order)
        
    # SELL
    elif act == 2:
        cost, profit = 0., ask_price * ask_size
        order = await make_order('sell')
        
    # HOLD
    else:
        return { 'result':action, 'cost':0., 'profit':0. }

    res = {'result':action, 'cost':cost, 'profit':profit }
    print("trade result: ", res)
    return { **res, **order }
