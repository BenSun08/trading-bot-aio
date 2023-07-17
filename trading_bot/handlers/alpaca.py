import asyncio
import aiohttp
from aiohttp import web
import json
import nest_asyncio
nest_asyncio.apply()

from .alpaca_bots import AlpacaTradeBot, AlpacaDataBot, AlpacaRealTimeBot
from ..utils import DateTimeEncoder
from .load_model import load_model, make_action


alpacaApp = web.Application()
alpacaRoutes = web.RouteTableDef()

tradeBot = AlpacaTradeBot()
dataBots = {
    "crypto": AlpacaDataBot("crypto"),
    "us_equity": AlpacaDataBot("stock")
}
conns = {}

@alpacaRoutes.get('/account')
async def get_account():
    account = tradeBot.get_account()
    return web.json_response(account)


@alpacaRoutes.get('/assets/{type}')
async def get_all_assets(request):
    type = request.match_info['type']
    assets = tradeBot.get_all_assets(type)
    return web.json_response(assets)

@alpacaRoutes.get('/asset/{id_or_symbol}')
async def get_asset(request):
    id_or_symbol = request.match_info['id_or_symbol']
    asset = tradeBot.get_asset(id_or_symbol)
    return web.json_response(asset)

@alpacaRoutes.get('/orders')
async def get_orders(request):
    status = request.query['status']
    side = request.query['side']
    orders = tradeBot.get_orders(status, side)
    return web.json_response(json.dumps(orders, default=str))

@alpacaRoutes.post('/orders/make/{side}')
async def make_order(request):
    data = await request.post()
    side = request.match_info['side']
    qty = data["qty"]
    symbol = data["symbol"]
    o = tradeBot.make_order(symbol, qty, side)
    order = { "symbol": o.symbol, "qty": o. qty, "side": o.side, "filled_avg_price": o.filled_avg_price }
    return web.json_response(order)

@alpacaRoutes.get('/orders/cancel/{id}')
async def cancel_order(request):
    id = request.match_info['id']
    if id == "all":
        cancel_status = tradeBot.cancel_all_orders()
    else:
        cancel_status = tradeBot.cancel_order(id)
    return web.json_response(cancel_status)

@alpacaRoutes.post('/market-data/{type}/historical')
async def get_historical_data(request):
    type = request.match_info['type']
    data = await request.post()
    symbol = data["symbol"]
    start = data["start"]
    end = data["end"]
    d = dataBots[type].get_history(symbol_or_symbols=symbol, start=start, end=end)
    print(d)
    return web.json_response(json.dumps(d, default=str))

@alpacaRoutes.get('/market-data/{type}/quote')
async def get_quote_data(request):
    type = request.match_info['type']
    symbol = request.query["symbol"]
    d = dataBots[type].get_latest_quote(symbol_or_symbols=symbol)
    print(d)
    return web.json_response(json.dumps(d, default=str))


# async def unsubscribe_task(symbols, bot):
#     # print("unsubs", symbols)
#     bot.unsubscribe(symbols)

background_tasks = set()
# @alpacaRoutes.get('/ws')
# async def websocket_handler(request):

#     ws = web.WebSocketResponse()
#     await ws.prepare(request)
#     # task = request.app.loop.create_task(trading_algo(ws))

#     await ws.send_str("Websocket connected!!!")
#     request_id = request['request_id']
#     print("request id: ", request_id)

#     try:
#         task = None
#         async for msg in ws:
#             print(msg)
#             if msg.type == aiohttp.WSMsgType.TEXT:
#                 if msg.data == 'close':
#                     if request_id in conns:
#                         await conns[request_id].stop()
#                         del conns[request_id]
#                     await ws.close()
#                 else:
#                     data = json.loads(msg.data)
#                     action = data["action"]
#                     if action == "subscribe":
#                         type = data['type']
#                         symbols = data['symbols']
#                         if type == 'us_equity' or type == 'crypto':
#                             task_load_model = request.app.loop.create_task(load_model())

#                             async def make_order(side):
#                                 o = tradeBot.make_order(symbols, 1, side)
#                                 order = { "symbol": o.symbol, "qty": o. qty, "side": o.side, "filled_avg_price": o.filled_avg_price }
#                                 return order
                            
#                             agent = await task_load_model
#                             async def action_callback(data):
#                                 res = await make_action(data, agent, make_order)
#                                 return res

#                             if request_id in conns:
#                                 task = request.app.loop.create_task(conns[request_id].subscribe(symbols, ws, action_callback))
#                             else:
#                                 liveBot = AlpacaRealTimeBot(type)
#                                 task = request.app.loop.create_task(liveBot.subscribe(symbols, ws, action_callback))
#                                 conns[request_id] = liveBot
#                             background_tasks.add(task)
#                             task.add_done_callback(background_tasks.discard)
#                         else:
#                             print('ws connection closed with exception %s' %
#                                 ws.exception())
#                             return
#                     elif action == "unsubscribe":
#                         symbols = data['symbols']
#                         if request_id in conns:
#                             await conns[request_id].unsubscribe(symbols)
#                             task.cancel()
#                             try:
#                                 await task
#                             except asyncio.CancelledError:
#                                 print("Subscription cancelled!!!")
#                         # del conns[request_id]
#                         # await ws.close()
                    
#                     elif action == "start-trading":
#                         if request_id in conns:
#                             conns[request_id].set_trading(True)
#                     elif action == "stop-trading":
#                         if request_id in conns:
#                             conns[request_id].set_trading(False)
#             elif msg.type == aiohttp.WSMsgType.CLOSED:
#                 print('ws connection closed')
#                 break
#             elif msg.type == aiohttp.WSMsgType.ERROR:
#                 print('ws connection closed with exception %s' %ws.exception())
#     finally:
#         await ws.close()
#         print('websocket connection closed')


#     return ws

@alpacaRoutes.get('/ws')
async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    # task = request.app.loop.create_task(trading_algo(ws))

    await ws.send_str("Websocket connected!!!")
    request_id = request['request_id']
    print("request id: ", request_id)


    try:
        subscribed = False
        subsTask = None
        trading = False

        async for msg in ws:
            print(msg)
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    subscribed = False
                    trading = False
                    await ws.close()
                else:
                    data = json.loads(msg.data)
                    action = data["action"]

                    if action == "subscribe":
                        type = data['type']
                        symbols = data['symbols']
                        if type == 'us_equity' or type == 'crypto':
                            subscribed = True

                            agent = await asyncio.to_thread(load_model)
                            symbol = symbols[0]

                            async def make_order_callback(side):
                                print("make order...")
                                o = tradeBot.make_order(symbol, 1, side)
                                order = { "symbol": o.symbol, "qty": o. qty, "side": o.side, "filled_avg_price": o.filled_avg_price }
                                print("order made...: ", order)
                                return order


                            async def get_data():
                                while subscribed:
                                    d = dataBots[type].get_latest_quote(symbol_or_symbols=symbols)
                                    res = {}
                                    # for symbol in d:
                                        # res[symbol] = {}
                                        # res[symbol]['symbol'] = d[symbol].symbol
                                        # res[symbol]['ask_price'] = d[symbol].ask_price
                                        # res[symbol]['ask_size'] = d[symbol].ask_size
                                        # res[symbol]['bid_price'] = d[symbol].bid_price
                                        # res[symbol]['bid_size'] = d[symbol].bid_size
                                    res['symbol'] = d[symbol].symbol
                                    res['ask_price'] = d[symbol].ask_price
                                    res['ask_size'] = d[symbol].ask_size
                                    res['bid_price'] = d[symbol].bid_price
                                    res['bid_size'] = d[symbol].bid_size
                                    await ws.send_json(res)
                                    if trading:
                                        trade_res = await make_action(res, agent, make_order_callback)
                                        await ws.send_json(trade_res)

                                    await asyncio.sleep(2)
                            subsTask = request.app.loop.create_task(get_data())
                        else:
                            print('ws connection closed with exception %s' %
                                ws.exception())
                            return
                        
                    elif action == "unsubscribe":
                        symbols = data['symbols']
                        subscribed = False
                        trading = False
                        subsTask.cancel()
                        try:
                            await subsTask
                        except asyncio.CancelledError:
                            print("Subscription cancelled!!!")
                    
                    elif action == "start-trading":
                        print("start trading...")
                        trading = True

                    elif action == "stop-trading":
                        trading = False

            elif msg.type == aiohttp.WSMsgType.CLOSED:
                print('ws connection closed')
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %ws.exception())
    finally:
        await ws.close()
        print('websocket connection closed')


    return ws

alpacaApp.add_routes(alpacaRoutes)