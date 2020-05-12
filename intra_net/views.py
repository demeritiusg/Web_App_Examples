from aiohttp import web
import aiohttp_jinja2
from dashboards import dashing
from reports import asset_listing


@aiohttp_jinja2.template('index.html')
async def index(request):
    return aiohttp_jinja2.render_template('index.html', request, {})


@aiohttp_jinja2.template('acct_purch_clearing.html')
async def accounting(request):
    return aiohttp_jinja2.render_template('acct_purch_clearing.html', request, {})


@aiohttp_jinja2.template('dash_chart.html')
async def reporting(request):
    chart = dashing.process_data()
    return aiohttp_jinja2.render_template('dash_chart.html', request, {'chart': chart})


@aiohttp_jinja2.template('upload.html')
async def uploaded(request):

    return aiohttp_jinja2.render_template('upload.html', request, {})
