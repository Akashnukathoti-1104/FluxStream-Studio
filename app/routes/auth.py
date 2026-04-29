from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_login import login_user, logout_user
from jose import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _issue_token(user: User) -> str:
    payload = {
        'sub': str(user.id),
        'username': user.username,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm=current_app.config['JWT_ALGORITHM'])


@auth_bp.post('/register')
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not username or not email or not password:
        return jsonify({'error': 'username, email, and password are required'}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'user already exists'}), 409

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role='creator',
        plan='free',
    )
    db.session.add(user)
    db.session.commit()
    login_user(user)

    return jsonify({'token': _issue_token(user), 'user': {'id': user.id, 'username': user.username, 'plan': user.plan}}), 201


@auth_bp.post('/login')
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'invalid credentials'}), 401

    login_user(user)
    return jsonify({'token': _issue_token(user), 'user': {'id': user.id, 'username': user.username, 'plan': user.plan}})


@auth_bp.get('/google/callback')
def google_callback():
    # OAuth integration point for Google login callback.
    return jsonify({'message': 'google oauth callback placeholder'}), 501


@auth_bp.post('/logout')
def logout():
    logout_user()
    return jsonify({'message': 'logged out'})
