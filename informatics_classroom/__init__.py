from flask import Flask, session, url_for
from flask_session import Session
from informatics_classroom.config import Config
import msal

from informatics_classroom.classroom.routes import classroom_bp
from informatics_classroom.imageupload.routes import image_bp
from informatics_classroom.networkbuilder.routes import network_bp
from informatics_classroom.mlmodelgame.routes import mlmodel_bp
from informatics_classroom.auth.routes import auth_bp, auth_configure_app


def create_app():
    app=Flask(__name__)  
    app=auth_configure_app(app)
    app.register_blueprint(classroom_bp,url_prefix='/')
    app.register_blueprint(image_bp,url_prefix='/')
    app.register_blueprint(network_bp,url_prefix='/')
    app.register_blueprint(mlmodel_bp,url_prefix='/')
    app.register_blueprint(auth_bp,url_prefix='/')
    return app

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        Config.CLIENT_ID, authority=authority or Config.AUTHORITY,
        client_credential=Config.CLIENT_SECRET, token_cache=cache)

def _build_auth_code_flow(authority=None, scopes=None):
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=url_for("authorized", _external=True))

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result
