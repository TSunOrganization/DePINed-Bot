# TSun DePINed Bot - Changelog

All notable changes to this project will be documented in this file.

---

### **[v4.0.0] - The Live Web App & Auto-URL Update - 2025-08-05**

#### ✨ New Features
* **Live Web Dashboard:** Integrated a Flask web server to serve a beautiful, real-time status dashboard.
* **Auto URL Notification:** The bot now automatically detects its public URL when deployed on Render and sends it to the configured Telegram chats on startup.
* **Live Uptime Counter:** The web dashboard features a JavaScript-powered live uptime counter that updates every second.

#### ⚙️ Enhancements & Code Quality
* **Full Integration:** Merged the `python-telegram-bot` application with the Flask web server using threading to run both concurrently.
* **Render Configuration:** Updated `render.yaml` to deploy as a `web` service with a health check path and automatic URL detection.
* **New Dependency:** Added `Flask` to `requirements.txt` for the web server functionality.

---

### **[v3.0.0] - The Interactive & Dashboard-Ready Update - 2025-08-05**

* **Interactive Telegram Commands:** Added `/status`, `/earnings`, and `/restart_account` commands.
* **Environment Variables:** Migrated all sensitive configurations to a `.env` file.
* **New Dependencies:** Added `python-telegram-bot` and `python-dotenv`.

---

### **[v2.1.0] - The Aesthetic Update - 2025-08-05**

* **Beautiful Telegram Messages:** Overhauled all Telegram notification formats with a unique, visually appealing style.

---

### **[v2.0.0] - The Reporter Update - 2025-08-05**

* **Consolidated Earnings Report:** Added a feature to send a consolidated earnings report for all accounts to Telegram.

---

### **[v1.0.0] - Initial Release - 2025-08-05**

* **Core Bot Functionality:** Auto-pinging, auto-fetching epoch earnings, multi-account support.
* **Proxy Support:** Support for multiple proxy modes and auto-rotation.
* **Basic Notifications:** Startup and error notifications via Telegram.