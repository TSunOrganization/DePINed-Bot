
from flask import Flask
from threading import Thread
import time

app = Flask('')

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>DePINed Bot Status</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f0f0f0; }
                .status { color: #28a745; font-size: 24px; margin: 20px 0; }
                .info { color: #666; margin: 10px 0; }
                .bot-name { color: #007bff; font-size: 28px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="bot-name">DePINed Bot</div>
            <div class="status">✅ Bot is Running</div>
            <div class="info">Status: Active</div>
            <div class="info">Uptime Monitor Endpoint</div>
            <div class="info">Last Check: ''' + time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()) + '''</div>
        </body>
    </html>
    '''

@app.route('/health')
def health():
    return {"status": "ok", "bot": "DePINed", "timestamp": time.time()}

@app.route('/ping')
def ping():
    return "pong"

def run():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()()
