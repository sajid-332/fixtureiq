from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.register_blueprint(
    production_predictions_bp
)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "project": "FixtureIQ"
    })

from backend.routes.production_prediction_api import (
    production_predictions_bp,
)


if __name__ == "__main__":
    app.run(debug=True)