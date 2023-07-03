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

@alpacaRoutes.get('/assets/{type}')
async def get_all_assets(request):
    type = request.match_info['type']
    assets = tradeBot.get_all_assets(type)
    return web.json_response(assets)

@alpacaRoutes.get('/ws')
async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                data = json.loads(msg.data)
                action = data["action"]
                if action == "subscribe":
                    type = data['type']
                    symbols = data['symbols']

                    print(data)
                    if type == 'us_equity' or type == 'crypto':
                        liveBot = AlpacaRealTimeBot(type)
                        liveBot.subscribe(symbols, ws)
                    else:
                        print('ws connection closed with exception %s' %
                            ws.exception())
                        return
                    # conns[request.sid] = liveBot

        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                ws.exception())

    print('websocket connection closed')

    return ws


alpacaApp.add_routes(alpacaRoutes)