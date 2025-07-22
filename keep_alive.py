
from flask import Flask
from threading import Thread
import time
import datetime

app = Flask('')

# Store start time when server starts
start_time = time.time()

@app.route('/')
def home():
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)
    
    # Calculate uptime in days, hours, minutes, seconds
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    return f'''
    <!DOCTYPE html>
    <html>
        <head>
            <title>DePINed Bot - Uptime Monitor</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                }}
                
                .container {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    text-align: center;
                    max-width: 500px;
                    width: 90%;
                }}
                
                .bot-title {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 10px;
                    background: linear-gradient(45deg, #00f5ff, #ff00f5);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                
                .status-badge {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    background: #28a745;
                    padding: 12px 24px;
                    border-radius: 50px;
                    font-size: 1.1rem;
                    font-weight: 600;
                    margin: 20px 0;
                    box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
                }}
                
                .pulse {{
                    animation: pulse 2s infinite;
                }}
                
                @keyframes pulse {{
                    0% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.05); }}
                    100% {{ transform: scale(1); }}
                }}
                
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }}
                
                .stat-card {{
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    padding: 20px;
                    text-align: center;
                    transition: transform 0.3s ease;
                }}
                
                .stat-card:hover {{
                    transform: translateY(-5px);
                }}
                
                .stat-number {{
                    font-size: 2rem;
                    font-weight: bold;
                    color: #00f5ff;
                    display: block;
                }}
                
                .stat-label {{
                    font-size: 0.9rem;
                    opacity: 0.8;
                    margin-top: 5px;
                }}
                
                .current-time {{
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                
                .time-display {{
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #ff00f5;
                    font-family: 'Courier New', monospace;
                }}
                
                .info-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                
                .info-item {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-size: 0.95rem;
                    opacity: 0.9;
                }}
                
                .footer {{
                    margin-top: 30px;
                    font-size: 0.8rem;
                    opacity: 0.7;
                }}
                
                @media (max-width: 480px) {{
                    .container {{
                        padding: 20px;
                    }}
                    
                    .bot-title {{
                        font-size: 2rem;
                    }}
                    
                    .stats-grid {{
                        grid-template-columns: repeat(2, 1fr);
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="bot-title">
                    <i class="fas fa-robot"></i> DePINed Bot
                </div>
                
                <div class="status-badge pulse">
                    <i class="fas fa-check-circle"></i>
                    Online & Running
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <span class="stat-number" id="days">{days}</span>
                        <span class="stat-label">Days</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number" id="hours">{hours:02d}</span>
                        <span class="stat-label">Hours</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number" id="minutes">{minutes:02d}</span>
                        <span class="stat-label">Minutes</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number" id="seconds">{seconds:02d}</span>
                        <span class="stat-label">Seconds</span>
                    </div>
                </div>
                
                <div class="current-time">
                    <div style="font-size: 1rem; opacity: 0.8; margin-bottom: 5px;">
                        <i class="fas fa-clock"></i> Current Time (UTC)
                    </div>
                    <div class="time-display" id="current-time">
                        {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
                
                <div class="info-grid">
                    <div class="info-item">
                        <i class="fas fa-server"></i>
                        <span>Status: Active</span>
                    </div>
                    <div class="info-item">
                        <i class="fas fa-heartbeat"></i>
                        <span>Health: Good</span>
                    </div>
                    <div class="info-item">
                        <i class="fas fa-shield-alt"></i>
                        <span>Uptime: 100%</span>
                    </div>
                    <div class="info-item">
                        <i class="fas fa-code"></i>
                        <span>Version: 2.0</span>
                    </div>
                </div>
                
                <div class="footer">
                    <i class="fas fa-code"></i> Made with ❤️ for DePINed Network
                    <br>
                    Bot started at: {datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S UTC')}
                </div>
            </div>
            
            <script>
                let startTime = {start_time};
                
                function updateUptime() {{
                    const currentTime = Date.now() / 1000;
                    const uptimeSeconds = Math.floor(currentTime - startTime);
                    
                    const days = Math.floor(uptimeSeconds / 86400);
                    const hours = Math.floor((uptimeSeconds % 86400) / 3600);
                    const minutes = Math.floor((uptimeSeconds % 3600) / 60);
                    const seconds = uptimeSeconds % 60;
                    
                    document.getElementById('days').textContent = days;
                    document.getElementById('hours').textContent = hours.toString().padStart(2, '0');
                    document.getElementById('minutes').textContent = minutes.toString().padStart(2, '0');
                    document.getElementById('seconds').textContent = seconds.toString().padStart(2, '0');
                }}
                
                function updateCurrentTime() {{
                    const now = new Date();
                    const utcTime = now.toISOString().slice(0, 19).replace('T', ' ');
                    document.getElementById('current-time').textContent = utcTime;
                }}
                
                // Update every second
                setInterval(() => {{
                    updateUptime();
                    updateCurrentTime();
                }}, 1000);
                
                // Initial update
                updateUptime();
                updateCurrentTime();
            </script>
        </body>
    </html>
    '''

@app.route('/health')
def health():
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)
    
    return {
        "status": "ok", 
        "bot": "DePINed", 
        "timestamp": current_time,
        "uptime_seconds": uptime_seconds,
        "uptime_formatted": f"{uptime_seconds // 86400}d {(uptime_seconds % 86400) // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s",
        "start_time": start_time
    }

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
    t.start()
