import os
import threading
from flask import Flask

app = Flask(__name__)

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
  
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
