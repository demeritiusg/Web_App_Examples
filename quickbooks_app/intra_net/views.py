from aiohttp import web
import aiohttp_jinja2
# from dashboards import dashing
from reports import asset_listing

urls = {
    'index': '/',
    'acct': 'accounting',
    'upload': 'uploaded'
}


@aiohttp_jinja2.template('index.html')
async def index(request):
    context = {
        'title': 'Index'
    }
    return aiohttp_jinja2.render_template('index.html', request, context=context)


@aiohttp_jinja2.template('About.html')
async def about(request):
    context = {
        'title': 'About'
    }
    return aiohttp_jinja2.render_template('About.html', request, context=context)


@aiohttp_jinja2.template('acct_purch_clearing.html')
async def accounting(request):
    return aiohttp_jinja2.render_template('acct_purch_clearing.html', request, {})


# @aiohttp_jinja2.template('dash_chart.html')
# async def reporting(request):
#    context = {
#        'title': 'Reporting'
#    }
#     chart = dashing.process_data()
#     return aiohttp_jinja2.render_template('dash_chart.html', request, context=context, {'chart': chart})


@aiohttp_jinja2.template('upload.html')
async def uploaded(request):
    context = {
        'title': 'Upload'
    }
    return aiohttp_jinja2.render_template('upload.html', request, context=context)


@aiohttp_jinja2.template('nav.html')
async def nav(request):
    # context = urls
    aiohttp_jinja2.render_template('nav.html', request, {})
