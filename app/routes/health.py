from flask import Blueprint, jsonify
from sqlalchemy import text
from app.extensions import db

health_bp = Blueprint('health', __name__, url_prefix='/health')


@health_bp.route('/', methods=['GET'])
def health_check():
    """Vérifie que l'API répond ET que la base de données est joignable."""
    try:
        db.session.execute(text('SELECT 1'))
        db_status = 'up'
        status_code = 200
    except Exception:
        db_status = 'down'
        status_code = 503

    return jsonify(status='healthy' if db_status == 'up' else 'unhealthy', database=db_status), status_code