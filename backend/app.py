from flask import Flask, jsonify
from flask_cors import CORS

from backend.routes.production_prediction_api import (
    production_predictions_bp,
)

from backend.routes.context_api import (
    context_api_bp,
)


app = Flask(__name__)

CORS(app)


# ============================================================
# Blueprints
# ============================================================

app.register_blueprint(
    production_predictions_bp
)

app.register_blueprint(
    context_api_bp
)


# ============================================================
# Health
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"],
)
def health():

    return jsonify(
        {
            "status":
                "ok",

            "project":
                "FixtureIQ",
        }
    )


# ============================================================
# Entrypoint
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )