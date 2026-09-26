from app.extensions import db
from app.models.user import User


def register(username, email, password):
    """Enregistre un nouvel utilisateur avec username, email et mot de passe."""
    if User.query.filter_by(username=username).first():
        raise ValueError("Nom d'utilisateur déjà pris.")
    if User.query.filter_by(email=email).first():
        raise ValueError("Email déjà utilisé.")

    user = User(username=username, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return user


def authenticate(username, password):
    """Authentifie un utilisateur avec le nom d'utilisateur et le mot de passe fournis."""
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return None
