from views import index, accounting, uploaded, about
    #reporting,
import pathlib

PRO_DIR = pathlib.Path(__file__).parent


def setup_routes(app):
    app.router.add_get('/', index, name='index')
    app.router.add_get('/accounting', accounting, name='accounting')
    #app.router.add_get('/reporting', reporting)
    app.router.add_get('/uploading', uploaded, name='uploaded')
    app.router.add_get('/About', about, name='About')


def setup_static(app):
    app.router.add_static('/static/', path=PRO_DIR / 'static', name='static')