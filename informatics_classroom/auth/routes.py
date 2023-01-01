from flask_session import Session
import requests
from flask import render_template, session, redirect,url_for, request
from informatics_classroom.auth import auth_bp
import msal
from informatics_classroom.config import Config

def auth_configure_app(app):
    app.config.from_object(Config)
    Session(app)
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.jinja_env.globals.update(_build_auth_code_flow=_build_auth_code_flow)  # Used in template
    return app

@auth_bp.route("/")
def index():
    if not session.get("user"):
        return redirect(url_for("auth_bp.login"))
    if 'user' in session.keys():
        if 'return_to' in session.keys():
            return redirect(url_for(session['return_to'], exercise=session['exercise']))
    return render_template('index.html', user=session["user"], version=msal.__version__)

@auth_bp.route("/login")
def login():
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
          
    session["flow"] = _build_auth_code_flow(scopes=Config.SCOPE)
    return render_template("login.html", auth_url=session["flow"]["auth_uri"], version=msal.__version__)

@auth_bp.route(Config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args)
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRF
        pass  # Simply ignore them
    return redirect(url_for("auth_bp.index"))

@auth_bp.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        Config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("auth_bp.index", _external=True))

@auth_bp.route("/graphcall")
def graphcall():
    token = _get_token_from_cache(Config.SCOPE)
    if not token:
        return redirect(url_for("auth_bp.login"))
    graph_data = requests.get(  # Use token to call downstream service
        Config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
        ).json()
    return render_template('display.html', result=graph_data)


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
        redirect_uri=url_for("auth_bp.authorized", _external=True))

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result

