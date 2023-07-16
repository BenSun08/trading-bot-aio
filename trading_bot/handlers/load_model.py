from ..ext.trading_bot.agent import Agent

model_name = "trading_bot/models/doubledqn_ggl_30.h5"
window_size = 10
strategy = 'dqn'
pretrained = True

async def load_model():
    agent = Agent(window_size, strategy=strategy, pretrained=pretrained, model_name=model_name)
    return agent

async def make_action(data, agent, make_order):
    bid_price = data['bid_price']
    ask_price = data['ask_price']
    bid_size = data['bid_size']
    ask_size = data['ask_size']
    balance = data['balance']
    
    mid_price = (bid_price + ask_price)/2

    action = agent.act(mid_price, is_eval=True)

    order = {}

    if action == 1:
        cost = bid_price * bid_size
        if balance >= cost:
            cost, profit = bid_price * bid_size, 0.
            order = await make_order('buy')
        
    # SELL
    elif action == 2:
        cost, profit = 0., ask_price * ask_size
        order = await make_order('sell')
        
    # HOLD
    else:
        pass
    res = {'result':action.tolist(), 'cost':cost, 'profit':profit }
    return { **res, **order }
