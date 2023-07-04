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

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)