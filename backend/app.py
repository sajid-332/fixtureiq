from flask import Flask, jsonify
from flask_cors import CORS

from backend.routes.production_prediction_api import (
    production_predictions_bp,
)


app = Flask(__name__)

CORS(app)


# ============================================================
# Production prediction API
# ============================================================

app.register_blueprint(
    production_predictions_bp
)


# ============================================================
# Basic health endpoint
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"],
)
def health():

    return jsonify(
        {
            "status": "ok",
            "project": "FixtureIQ",
        }
    )


# ============================================================
# Development server
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )