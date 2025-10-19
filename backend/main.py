from flask import Flask, request
import os
import json
from app.channels import telegram
from app.utils.env import is_local
from cal.secrets import get_secret

def telegram_webhook(request):
    TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")
    update = request.get_json()
    telegram.handle_update(TELEGRAM_BOT_TOKEN, update)
    return json.dumps({"ok": True}), 200

if __name__ == "__main__" and is_local():
    app = Flask(__name__)

    @app.route("/telegram/webhook", methods=["POST"])
    def telegram_route():
        return telegram_webhook(request)

    app.run(host="0.0.0.0", port=8080, debug=True)
