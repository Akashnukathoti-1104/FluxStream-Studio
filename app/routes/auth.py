from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, request
import requests
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


@auth_bp.post('/google/callback')
def google_callback():
    """Exchange authorization code for tokens, create/find user, and login.

    Expects JSON: { code: str, redirect_uri: str }
    """
    data = request.get_json(silent=True) or {}
    code = data.get('code')
    redirect_uri = data.get('redirect_uri') or current_app.config.get('GOOGLE_OAUTH_REDIRECT_URI')
    if not code or not redirect_uri:
        return jsonify({'error': 'code and redirect_uri required'}), 400

    client_id = current_app.config.get('GOOGLE_CLIENT_ID') or ''
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET') or ''
    token_url = 'https://oauth2.googleapis.com/token'

    resp = requests.post(token_url, data={
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    })

    if resp.status_code != 200:
        return jsonify({'error': 'token exchange failed', 'details': resp.text}), 400

    tok = resp.json()
    id_token = tok.get('id_token')
    if not id_token:
        return jsonify({'error': 'no id_token returned'}), 400

    try:
        info = jwt.get_unverified_claims(id_token)
    except Exception:
        info = {}

    # basic checks
    if info.get('aud') and client_id and info.get('aud') != client_id:
        return jsonify({'error': 'audience mismatch'}), 400

    email = info.get('email')
    name = info.get('name') or (email.split('@')[0] if email else 'google_user')
    picture = info.get('picture')

    if not email:
        return jsonify({'error': 'email not provided by provider'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(username=name, email=email, password_hash='')
        if picture:
            user.avatar_url = picture
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return jsonify({'token': _issue_token(user), 'user': {'id': user.id, 'username': user.username}})


@auth_bp.post('/logout')
def logout():
    logout_user()
    return jsonify({'message': 'logged out'})
