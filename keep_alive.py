import os
import logging
import threading
from flask import Flask

app = Flask(__name__)
log = logging.getLogger("keep_alive")

FAKE_PORT = int(os.environ.get("PORT", 1000))

@app.route("/")
def home():
    return "Bot is alive", 200

@app.route("/health")
def health():
    return {"status": "ok"}, 200

def run():

    app.run(host="0.0.0.0", port=FAKE_PORT)


def keep_alive():

    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if external_url:
        log.info(f"Keep-alive URL (βάλε το στο UptimeRobot): {external_url}")
    else:
        log.info(
            f"Keep-alive server ξεκίνησε στο port {FAKE_PORT}. "
            "Αν τρέχεις σε Render, το public URL είναι στο dashboard "
            "(πάνω από το όνομα του service σου)."
        )

    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
