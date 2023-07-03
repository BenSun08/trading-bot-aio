from aiohttp import web
from .views import index
from .settings import BASE_DIR

def setup_routes(app):
    app.add_routes([web.get('/', index),
                    web.static('/static', str(BASE_DIR / 'trading_bot' / 'static'))
                    ])