from flask import Flask

# Mock backup server for testing load balancer
app = Flask(__name__)

@app.route("/")
async def get_index():
    return "<p>Hello, world!</p>"

@app.route("/status")
async def get_status():
    return ""