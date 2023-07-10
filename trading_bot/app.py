import asyncio
from aiohttp import web
import logging

from .settings import config, BASE_DIR
from .routes import setup_routes
from .handlers.alpaca import alpacaApp

log = logging.getLogger('app')
log.setLevel(logging.DEBUG)

f = logging.Formatter('[L:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', datefmt = '%d-%m-%Y %H:%M:%S')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(f)
log.addHandler(ch)

async def on_shutdown(app):
    for ws in app['websockets']:
        await ws.close(code=1001, message='Server shutdown')

async def shutdown(server, app, handler):

    server.close()
    await server.wait_closed()
    app.client.close()  # database connection close
    await app.shutdown()
    await handler.finish_connections(10.0)
    await app.cleanup()

async def init(loop):
    app = web.Application(loop=loop)
    app['websockets'] = []
    app['config'] = config

    setup_routes(app)
    app.add_subapp('/alpaca', alpacaApp)

    handler = app.make_handler()
    app.on_shutdown.append(on_shutdown) 

    serv_generator = loop.create_server(handler, '0.0.0.0', 8080)
    return serv_generator, handler, app

loop = asyncio.get_event_loop()
serv_generator, handler, app = loop.run_until_complete(init(loop))
serv = loop.run_until_complete(serv_generator)
log.debug('start server %s' % str(serv.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    log.debug(' Stop server begin')
finally:
    loop.run_until_complete(shutdown(serv, app, handler))
    loop.close()
log.debug('Stop server end')