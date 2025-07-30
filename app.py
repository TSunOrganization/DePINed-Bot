
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import pytz
import os
import json

app = Flask(__name__)
wib = pytz.timezone('Asia/Jakarta')

# Bot statistics (these would be updated by the actual bot)
start_time = datetime.now().astimezone(wib)

@app.route('/')
def dashboard():
    with open('index.html', 'r') as f:
        html_content = f.read()
    return html_content

@app.route('/styles.css')
def styles():
    with open('styles.css', 'r') as f:
        css_content = f.read()
    return css_content, 200, {'Content-Type': 'text/css'}

@app.route('/uptime-data')
def uptime_data():
    current_time = datetime.now().astimezone(wib)
    uptime_delta = current_time - start_time
    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return jsonify({
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "active_accounts": 32,  # This would be dynamic in the real bot
        "total_pings": 1500,   # This would be dynamic in the real bot
        "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S %Z')
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "uptime": str(datetime.now().astimezone(wib) - start_time)})

@app.route('/ping')
def ping():
    return jsonify({"message": "pong", "timestamp": datetime.now().astimezone(wib).isoformat()})

@app.route('/status')
def status():
    current_time = datetime.now().astimezone(wib)
    uptime_delta = current_time - start_time
    return jsonify({
        "status": "running",
        "uptime": str(uptime_delta),
        "active_accounts": 32,
        "total_pings_sent": 1500,
        "start_time": start_time.isoformat(),
        "current_time": current_time.isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
