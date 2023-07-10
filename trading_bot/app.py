import asyncio
from aiohttp import web

from .settings import config, BASE_DIR
from .routes import setup_routes
from .handlers.alpaca import alpacaApp

async def init(loop):
    app = web.Application(loop=loop)
    app['websockets'] = []
    app['config'] = config
    
    setup_routes(app)
    app.add_subapp('/alpaca', alpacaApp)

    handler = app.make_handler()