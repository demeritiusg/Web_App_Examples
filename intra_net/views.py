from aiohttp import web
import aiohttp_jinja2

@aiohttp_jinja2.template('index.html')
async def index(request):
    return aiohttp_jinja2.render_template('index.html', request, {})


@aiohttp_jinja2.template('acct_purch_clearing.html')
async def accounting(request):
    return aiohttp_jinja2.render_template('acct_purch_clearing.html', request, {})


