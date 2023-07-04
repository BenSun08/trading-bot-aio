import argparse
from aiohttp import web
# import aiohttp_jinja2
# import jinja2

from .settings import config, BASE_DIR
from .routes import setup_routes
from .handlers.alpaca import alpacaApp
# from .middlewares import setup_middlewares
# from db import pg_context

app = web.Application()
app['config'] = config
# aiohttp_jinja2.setup(app, 
#     loader=jinja2.FileSystemLoader(str(BASE_DIR / 'trading_bot' / 'templates')))
setup_routes(app)
app.add_subapp('/alpaca', alpacaApp)
# setup_middlewares(app)
# app.cleanup_ctx.append(pg_context)
parser = argparse.ArgumentParser(description='Trading Bot')
parser.add_argument('--port', type=int, default=8080, help='port to listen on')

if __name__ == '__main__':
    args = parser.parse_args()
    web.run_app(app, port=args.port)