# import asyncio
import argparse
from aiohttp import web
from aiohttp.web_log import AccessLogger
import logging
from aiohttp_request_id_logging import (
    setup_logging_request_id_prefix,
    request_id_middleware,
    RequestIdContextAccessLogger)
# import aiohttp_jinja2
# import jinja2

from .settings import config, BASE_DIR
from .routes import setup_routes
from .handlers.alpaca import alpacaApp


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(threadName)s] %(name)-26s %(levelname)5s: %(requestIdPrefix)s%(message)s')

setup_logging_request_id_prefix()
# from .middlewares import setup_middlewares
# from db import pg_context

# loop = asyncio.get_event_loop()
app = web.Application(middlewares=[request_id_middleware()])
app['config'] = config
# aiohttp_jinja2.setup(app, 
#     loader=jinja2.FileSystemLoader(str(BASE_DIR / 'trading_bot' / 'templates')))
setup_routes(app)
app.add_subapp('/alpaca', alpacaApp)
# setup_middlewares(app)
# app.cleanup_ctx.append(pg_context)
parser = argparse.ArgumentParser(description='Trading Bot')
parser.add_argument('--port', type=int, default=8080, help='port to listen on')
parser.add_argument('--path')

if __name__ == '__main__':
    args = parser.parse_args()
    web.run_app(app, port=args.port, path=args.path, 
                access_log_class=RequestIdContextAccessLogger,
                access_log_format=AccessLogger.LOG_FORMAT.replace(' %t ', ' ') + ' %Tf'
                )