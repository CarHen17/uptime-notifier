import json
import os
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from zoneinfo import ZoneInfo

app = Flask(__name__)
CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "channels.json")
TIMEZONE = ZoneInfo("America/Sao_Paulo")


def load_channels():
    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)


def format_datetime(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt = dt.astimezone(TIMEZONE)
        return dt.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return datetime.now(TIMEZONE).strftime("%d/%m/%Y às %H:%M")


def build_message(payload):
    heartbeat = payload.get("heartbeat") or {}
    monitor = payload.get("monitor") or {}

    name = monitor.get("name", "Desconhecido")
    host = monitor.get("hostname") or monitor.get("url", "N/A")
    status = heartbeat.get("status", 0)
    ping = heartbeat.get("ping")
    time_str = format_datetime(heartbeat.get("time", ""))

    if status == 1:
        latency = f"{ping}ms" if ping is not None and ping >= 0 else "N/A"
        return (
            f"✅ *SERVIÇO RECUPERADO*\n\n"
            f"📍 *Monitor:* {name}\n"
            f"🌐 *Host:* `{host}`\n"
            f"📊 *Status:* ONLINE\n"
            f"⏱ *Latência:* {latency}\n"
            f"📅 *Data/Hora:* {time_str}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚡ _Monitoramento Automático_"
        )
    else:
        return (
            f"🔴 *ALERTA DE QUEDA*\n\n"
            f"📍 *Monitor:* {name}\n"
            f"🌐 *Host:* `{host}`\n"
            f"📊 *Status:* OFFLINE\n"
            f"📅 *Data/Hora:* {time_str}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚡ _Monitoramento Automático_"
        )


def send_telegram(bot_token, chat_id, message, protect_content=False):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "protect_content": protect_content,
    }
    resp = requests.post(url, json=payload, timeout=10)
    return resp.status_code, resp.json()


@app.route("/webhook/<channel>", methods=["POST"])
def webhook(channel):
    channels = load_channels()

    if channel not in channels:
        return jsonify({"error": f"Canal '{channel}' não encontrado"}), 404

    payload = request.get_json(force=True, silent=True) or {}
    heartbeat = payload.get("heartbeat") or {}

    is_test = not heartbeat
    if not is_test and not heartbeat.get("important", False):
        return jsonify({"status": "ignored", "reason": "not important"}), 200

    cfg = channels[channel]
    message = build_message(payload)
    status_code, resp = send_telegram(
        cfg["bot_token"],
        cfg["chat_id"],
        message,
        cfg.get("protect_content", False),
    )

    return jsonify({"telegram_status": status_code, "response": resp}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
