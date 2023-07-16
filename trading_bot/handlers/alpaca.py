import asyncio
import aiohttp
from aiohttp import web
import json
import nest_asyncio
nest_asyncio.apply()

from .alpaca_bots import AlpacaTradeBot, AlpacaDataBot, AlpacaRealTimeBot

alpacaApp = web.Application()
alpacaRoutes = web.RouteTableDef()

tradeBot = AlpacaTradeBot()
dataBots = {
    "crypto": AlpacaDataBot("crypto"),
    "stock": AlpacaDataBot("stock")
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


async def unsubscribe_task(symbols, bot):
    # print("unsubs", symbols)
    bot.unsubscribe(symbols)

background_tasks = set()
@alpacaRoutes.get('/ws')
async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    # task = request.app.loop.create_task(trading_algo(ws))

    await ws.send_str("Websocket connected!!!")
    request_id = request['request_id']
    print("request id: ", request_id)

    try:
        task = None
        async for msg in ws:
            print(msg)
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    if request_id in conns:
                        await conns[request_id].stop()
                        del conns[request_id]
                    await ws.close()
                else:
                    data = json.loads(msg.data)
                    action = data["action"]
                    if action == "subscribe":
                        type = data['type']
                        symbols = data['symbols']
                        if type == 'us_equity' or type == 'crypto':
                            if request_id in conns:
                                task = request.app.loop.create_task(conns[request_id].subscribe(symbols, ws))
                            else:
                                liveBot = AlpacaRealTimeBot(type)
                                task = request.app.loop.create_task(liveBot.subscribe(symbols, ws))
                                conns[request_id] = liveBot
                            background_tasks.add(task)
                            task.add_done_callback(background_tasks.discard)
                        else:
                            print('ws connection closed with exception %s' %
                                ws.exception())
                            return
                    elif action == "unsubscribe":
                        symbols = data['symbols']
                        if request_id in conns:
                            await conns[request_id].unsubscribe(symbols)
                            task.cancel()
                            try:
                                await task
                            except asyncio.CancelledError:
                                print("Subscription cancelled!!!")
                        # del conns[request_id]
                        # await ws.close()
                    
                    elif action == "start_trading":
                        async def buy():
                            side = request.match_info['side']
                            qty = data["qty"]
                            symbol = data["symbol"]
                            o = tradeBot.make_order(symbol, qty, side)
                            order = { "symbol": o.symbol, "qty": o. qty, "side": o.side, "filled_avg_price": o.filled_avg_price }
                            pass
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