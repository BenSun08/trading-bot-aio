from aiohttp import web
from views import index

def setup_routes(app):
    app.add_routes([web.get('/', index)])