from tensorflow import keras

async def load_model():
    model_name = "trading_bot/models/doubledqn_ggl_30.h5"
    agent = keras.load_model(model_name)
    return agent

async def make_action(data, agent, buy_callback, sell_callback):
    bid_price = data['bid_price']
    ask_price = data['ask_price']
    bid_size = data['bid_size']
    ask_size = data['ask_size']
    balance = data['balance']
    
    mid_price = (bid_price + ask_price)/2

    action = agent.act(mid_price, is_eval=True)

    if action == 1:
        cost = bid_price * bid_size
        if balance >= cost:
            cost, profit = bid_price * bid_size, 0.
            buy_callback()
        
    # SELL
    elif action == 2:
        cost, profit = 0., ask_price * ask_size
        sell_callback()
        
    # HOLD
    else:
        pass

    return {'result':action.tolist(), 'cost':cost, 'profit':profit}
