from flask import Flask, render_template
from threading import Thread
import time

app = Flask('', template_folder='.', static_folder='.')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return {"status": "ok", "bot": "DePINed", "timestamp": time.time()}

@app.route('/ping')
def ping():
    return "pong"

@app.route('/status')
def status():
    return {
        "bot_name": "DePINed Bot",
        "status": "running",
        "uptime": time.time(),
        "last_check": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }

def run():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()