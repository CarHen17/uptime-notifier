import json
import os
import re
import requests
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, flash
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "uptime-notifier-secret")
CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "channels.json")
TIMEZONE = ZoneInfo("America/Sao_Paulo")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Uptime Notifier</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
    .header { background: #1e293b; border-bottom: 1px solid #334155; padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; }
    .header h1 { font-size: 18px; font-weight: 600; color: #f1f5f9; }
    .header span { font-size: 12px; color: #64748b; }
    .logout { font-size: 13px; color: #64748b; text-decoration: none; padding: 6px 12px; border: 1px solid #334155; border-radius: 6px; }
    .logout:hover { color: #e2e8f0; border-color: #475569; }
    .container { max-width: 900px; margin: 32px auto; padding: 0 16px; }
    .flash { padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }
    .flash.success { background: #14532d; color: #86efac; border: 1px solid #166534; }
    .flash.error { background: #7f1d1d; color: #fca5a5; border: 1px solid #991b1b; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 24px; }
    .card h2 { font-size: 15px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 20px; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .form-group { display: flex; flex-direction: column; gap: 6px; }
    .form-group.full { grid-column: 1 / -1; }
    label { font-size: 12px; font-weight: 500; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
    input[type=text], input[type=password] { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; color: #e2e8f0; font-size: 14px; width: 100%; }
    input:focus { outline: none; border-color: #3b82f6; }
    .checkbox-group { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
    .checkbox-group input { width: auto; }
    .checkbox-group label { text-transform: none; font-size: 14px; color: #e2e8f0; letter-spacing: 0; }
    .btn { padding: 10px 20px; border-radius: 8px; border: none; font-size: 14px; font-weight: 500; cursor: pointer; }
    .btn-primary { background: #3b82f6; color: white; }
    .btn-primary:hover { background: #2563eb; }
    .btn-danger { background: transparent; color: #f87171; border: 1px solid #7f1d1d; padding: 6px 12px; font-size: 13px; }
    .btn-danger:hover { background: #7f1d1d; }
    .btn-test { background: transparent; color: #60a5fa; border: 1px solid #1e3a5f; padding: 6px 12px; font-size: 13px; }
    .btn-test:hover { background: #1e3a5f; }
    .channel-list { display: flex; flex-direction: column; gap: 12px; }
    .channel-item { background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
    .channel-info { flex: 1; min-width: 0; }
    .channel-name { font-size: 15px; font-weight: 600; color: #f1f5f9; margin-bottom: 4px; }
    .channel-meta { font-size: 12px; color: #475569; }
    .channel-url { font-size: 12px; color: #3b82f6; font-family: monospace; margin-top: 2px; }
    .channel-actions { display: flex; gap: 8px; flex-shrink: 0; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; }
    .badge-on { background: #14532d; color: #86efac; }
    .badge-off { background: #1e293b; color: #64748b; border: 1px solid #334155; }
    .empty { text-align: center; padding: 40px; color: #475569; font-size: 14px; }
    .login-wrap { display: flex; align-items: center; justify-content: center; min-height: 100vh; }
    .login-card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 40px; width: 100%; max-width: 360px; }
    .login-card h1 { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
    .login-card p { font-size: 14px; color: #64748b; margin-bottom: 28px; }
    .login-card .form-group { margin-bottom: 16px; }
    .login-card .btn { width: 100%; margin-top: 8px; padding: 12px; }
  </style>
</head>
<body>
{% if not logged_in %}
<div class="login-wrap">
  <div class="login-card">
    <h1>Uptime Notifier</h1>
    <p>Digite a senha para acessar o painel</p>
    {% for msg, cat in messages %}
    <div class="flash {{ cat }}">{{ msg }}</div>
    {% endfor %}
    <form method="POST" action="/admin/login">
      <div class="form-group">
        <label>Senha</label>
        <input type="password" name="password" placeholder="••••••••" autofocus>
      </div>
      <button class="btn btn-primary" type="submit">Entrar</button>
    </form>
  </div>
</div>
{% else %}
<div class="header">
  <h1>🔔 Uptime Notifier</h1>
  <div style="display:flex;align-items:center;gap:16px;">
    <span>{{ channels|length }} canal(is) configurado(s)</span>
    <a href="/admin/logout" class="logout">Sair</a>
  </div>
</div>
<div class="container">
  {% for msg, cat in messages %}
  <div class="flash {{ cat }}">{{ msg }}</div>
  {% endfor %}

  <div class="card">
    <h2>Adicionar Canal</h2>
    <form method="POST" action="/admin/channels">
      <div class="form-grid">
        <div class="form-group">
          <label>Nome do Canal</label>
          <input type="text" name="name" placeholder="ex: cliente-a" required>
        </div>
        <div class="form-group">
          <label>Chat ID</label>
          <input type="text" name="chat_id" placeholder="-100123456789" required>
        </div>
        <div class="form-group full">
          <label>Bot Token</label>
          <input type="text" name="bot_token" placeholder="1234567890:AAF..." required>
        </div>
        <div class="form-group full">
          <div class="checkbox-group">
            <input type="checkbox" name="protect_content" id="protect" value="1">
            <label for="protect">Proteger conteúdo (impede encaminhar no Telegram)</label>
          </div>
        </div>
      </div>
      <div style="margin-top:20px;">
        <button class="btn btn-primary" type="submit">Adicionar Canal</button>
      </div>
    </form>
  </div>

  <div class="card">
    <h2>Canais Configurados</h2>
    {% if channels %}
    <div class="channel-list">
      {% for name, cfg in channels.items() %}
      <div class="channel-item">
        <div class="channel-info">
          <div class="channel-name">{{ name }}</div>
          <div class="channel-meta">
            Chat ID: {{ cfg.chat_id }}
            &nbsp;·&nbsp;
            <span class="badge {% if cfg.get('protect_content') %}badge-on{% else %}badge-off{% endif %}">
              {% if cfg.get('protect_content') %}protegido{% else %}não protegido{% endif %}
            </span>
          </div>
          <div class="channel-url">http://uptime-notifier:5000/webhook/{{ name }}</div>
        </div>
        <div class="channel-actions">
          <form method="POST" action="/admin/channels/{{ name }}/test">
            <button class="btn btn-test" type="submit">Testar</button>
          </form>
          <form method="POST" action="/admin/channels/{{ name }}/delete" onsubmit="return confirm('Remover canal {{ name }}?')">
            <button class="btn btn-danger" type="submit">Remover</button>
          </form>
        </div>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div class="empty">Nenhum canal cadastrado ainda.</div>
    {% endif %}
  </div>
</div>
{% endif %}
</body>
</html>
"""


def load_channels():
    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)


def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f, indent=2, ensure_ascii=False)


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


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("admin"))
        return f(*args, **kwargs)
    return decorated


def render_admin(extra_messages=None):
    msgs = [(m, c) for m, c in (session.pop("_flashes", None) or [])]
    if extra_messages:
        msgs.extend(extra_messages)
    channels = load_channels() if session.get("logged_in") else {}
    return render_template_string(
        ADMIN_HTML,
        logged_in=session.get("logged_in", False),
        channels=channels,
        messages=msgs,
    )


# --- Admin routes ---

@app.route("/admin")
def admin():
    return render_admin()


@app.route("/admin/login", methods=["POST"])
def admin_login():
    if request.form.get("password") == ADMIN_PASSWORD:
        session["logged_in"] = True
        return redirect(url_for("admin"))
    flash("Senha incorreta", "error")
    return render_admin(extra_messages=[("Senha incorreta", "error")])


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin"))


@app.route("/admin/channels", methods=["POST"])
@login_required
def add_channel():
    name = re.sub(r"[^a-z0-9\-]", "", request.form.get("name", "").lower().strip().replace(" ", "-"))
    bot_token = request.form.get("bot_token", "").strip()
    chat_id = request.form.get("chat_id", "").strip()
    protect_content = request.form.get("protect_content") == "1"

    if not name or not bot_token or not chat_id:
        flash("Preencha todos os campos obrigatórios.", "error")
        return redirect(url_for("admin"))

    channels = load_channels()
    if name in channels:
        flash(f"Canal '{name}' já existe.", "error")
        return redirect(url_for("admin"))

    channels[name] = {"bot_token": bot_token, "chat_id": chat_id, "protect_content": protect_content}
    save_channels(channels)
    flash(f"Canal '{name}' adicionado com sucesso!", "success")
    return redirect(url_for("admin"))


@app.route("/admin/channels/<name>/delete", methods=["POST"])
@login_required
def delete_channel(name):
    channels = load_channels()
    if name not in channels:
        flash(f"Canal '{name}' não encontrado.", "error")
        return redirect(url_for("admin"))
    del channels[name]
    save_channels(channels)
    flash(f"Canal '{name}' removido.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/channels/<name>/test", methods=["POST"])
@login_required
def test_channel(name):
    channels = load_channels()
    if name not in channels:
        flash(f"Canal '{name}' não encontrado.", "error")
        return redirect(url_for("admin"))
    cfg = channels[name]
    now = datetime.now(TIMEZONE).strftime("%d/%m/%Y às %H:%M")
    msg = (
        f"🔔 *MENSAGEM DE TESTE*\n\n"
        f"📍 *Canal:* {name}\n"
        f"📅 *Data/Hora:* {now}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚡ _Uptime Notifier funcionando!_"
    )
    status_code, resp = send_telegram(cfg["bot_token"], cfg["chat_id"], msg, cfg.get("protect_content", False))
    if resp.get("ok"):
        flash(f"Teste enviado para '{name}' com sucesso!", "success")
    else:
        flash(f"Erro ao enviar: {resp.get('description', 'Erro desconhecido')}", "error")
    return redirect(url_for("admin"))


# --- Webhook ---

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
