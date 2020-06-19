from aiohttp import web
import asyncio
import jinja2
import aiohttp_jinja2
from settings import config
from routes import setup_routes, setup_static
from middlewares import setup_middlewares
import logging

def web_server(loop):

    app = web.Application(loop=loop)

    app['config'] = config

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

    setup_routes(app)
    setup_static(app)
    setup_middlewares(app)

    print('[INFO] Ready')
    return app


def wakeup():
    loop.call_later(0.1, wakeup)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.call_later(0.1, wakeup)
    server = web_server(loop)
    logging.basicConfig(level=logging.DEBUG)
    web.run_app(server, host='127.0.0.1', port=8080)
