from flask import Flask, redirect, request, session, url_for, render_template

import requests
import json
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', auth_url=auth_url)

@app.route('/nav')
def nav():
    return render_template('nav.html', auth_url=auth_url)

@app.route('/refresh_token')
def qbo_refresh_token():
    refresh_token = session.get('refresh_token')
    if not refresh_token:
        return 'No refresh token available', 400

if __name__ == '__main__':
    app.run(debug=True)