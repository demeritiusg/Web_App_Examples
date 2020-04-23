import aiohttp_jinja2
from aiohttp import web


async def handle_400(request):
    return aiohttp_jinja2.render_template('404.html', request, {})


async def handle_401(request):
    return aiohttp_jinja2.render_template('401.html', request, {})


async def handle_403(request):
    return aiohttp_jinja2.render_template('403.html', request, {})


async def handle_404(request):
    return aiohttp_jinja2.render_template('404.html', request, {})


async def handle_500(request):
    return aiohttp_jinja2.render_template('500.html', request, {})


async def handle_502(request):
    return aiohttp_jinja2.render_template('502.html', request, {})


async def handle_503(request):
    return aiohttp_jinja2.render_template('503.html', request, {})


async def handle_504(request):
    return aiohttp_jinja2.render_template('504.html', request, {})


def create_error_middleware(overrides):
    @web.middleware
    async def error_middleware(request, handler):

        try:
            response = await handler(request)

            override = overrides.get(response.status)
            if override:
                return await override(request)

            return response

        except web.HTTPException as ex:
            override = overrides.get(ex.status)
            if override:
                return await override(request)

            raise

    return error_middleware


def setup_middlewares(app):
    error_middleware = create_error_middleware({
        400: handle_400,
        401: handle_401,
        403: handle_403,
        404: handle_404,
        500: handle_500,
        502: handle_502,
        503: handle_503,
        504: handle_504
    })
    app.middlewares.append(error_middleware)
