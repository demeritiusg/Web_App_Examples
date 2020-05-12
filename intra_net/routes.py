from views import index, accounting, reporting, uploaded
import pathlib

PRO_DIR = pathlib.Path(__file__).parent


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/accounting', accounting)
    app.router.add_get('/reporting', reporting)
    app.router.add_get('/uploading', uploaded)


def setup_static(app):
    app.router.add_static('/static/', path=PRO_DIR / 'static', name='static')
