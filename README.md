# Odoo Telegram Bridge & Stock Checker Bot

A robust backend integration bridge that connects an **Odoo ERP** instance with a **Telegram Bot** using asynchronous Python. The system provides real-time stock level checks on-demand and features an automated warehouse monitoring system utilizing **Celery** and **Redis** to alert administrators about low inventory conditions.

## 🚀 Features

* **On-Demand Stock Checking:** Users can send a Product SKU (e.g., `FURN_7777`) via Telegram to receive an instant breakdown of stock metrics (`On Hand`, `Reserved`, `Forecasted`) fetched directly from Odoo via XML-RPC.
* **Automated Low Stock Alarms:** A background cron-like task manages "Minimum Stock Rules". If a tracked item's forecasted availability drops below a defined critical threshold, a high-priority alert is dispatched to the procurement team/admin.
* **Asynchronous & Distributed Architecture:** Uses `aiogram` for responsive Telegram polling and `Celery` with a `Redis` broker to isolate heavy ERP polling into independent background worker processes.

## 🛠️ Tech Stack

* **Language:** Python 3.12+
* **Framework:** [aiogram v3](https://github.com/aiogram/aiogram) (Asynchronous Telegram Bot framework)
* **Task Queue:** [Celery](https://github.com/celery/celery)
* **Message Broker:** [Redis](https://redis.io/)
* **ERP Integration:** XML-RPC (Odoo External API)

---

## 📂 Project Structure

```text
odoo-telegram-bridge/
│
├── bot/
│   ├── __init__.py
│   ├── handlers.py          # Telegram message routers and commands
│   └── celery_app.py        # Monolithic Celery configuration & background tasks
│
├── .env                     # Local environment variables (ignored by git)
├── .gitignore
├── requirements.txt
└── main.py                  # Telegram bot entry point