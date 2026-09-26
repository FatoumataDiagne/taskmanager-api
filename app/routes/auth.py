from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from app.services.auth_service import register, authenticate
from app.models.user import User
from app.extensions import limiter

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/register', methods=['POST'])
def register_user():
    """
    Crée un compte utilisateur.
    ---
    tags: [Auth]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [username, email, password]
          properties:
            username: {type: string, example: alice}
            email: {type: string, example: alice@test.com}
            password: {type: string, example: pass1234}
    responses:
      201:
        description: Utilisateur créé
      400:
        description: Champs manquants ou nom d'utilisateur/email déjà pris
    """
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": {
            "code": "MISSING_FIELDS",
            "message": "username, email et password sont requis.",
            "status": 400
        }}), 400

    try:
        user = register(username, email, password)
        return jsonify({"id": user.id, "username": user.username, "email": user.email}), 201
    except ValueError as e:
        return jsonify({"error": {"code": "REGISTER_CONFLICT", "message": str(e), "status": 400}}), 400


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login_user():
    """
    Connecte un utilisateur et délivre les jetons JWT.
    ---
    tags: [Auth]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [username, password]
          properties:
            username: {type: string, example: alice}
            password: {type: string, example: pass1234}
    responses:
      200:
        description: access_token et refresh_token
      401:
        description: Identifiants invalides
      429:
        description: Trop de tentatives (limite de débit)
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": {
            "code": "MISSING_FIELDS",
            "message": "username et password sont requis.",
            "status": 400
        }}), 400

    user = authenticate(username, password)
    if not user:
        return jsonify({"error": {
            "code": "INVALID_CREDENTIALS",
            "message": "Nom d'utilisateur ou mot de passe invalide.",
            "status": 401
        }}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Utilisateur introuvable.", "status": 404}}), 404
    return jsonify({"id": user.id, "username": user.username, "email": user.email}), 200