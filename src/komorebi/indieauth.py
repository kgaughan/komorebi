from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    Response,
    url_for,
)

auth = Blueprint("auth", __name__)


@auth.route("/")
def auth_endpoint():
    """
    https://indieauth.com/auth?me=https://aaronparecki.com/&
                           redirect_uri=https://ownyourgram.com/auth/callback&
                           client_id=https://ownyourgram.com&
                           state=1234567890&
                           scope=create&
                           response_type=code
    """
    # https://indieweb.org/authorization-endpoint
    #
    # Request:
    #
    # me: identifies URI for identity being auth'd
    # redirect_uri: callback URI for when the authentication goes through successfully
    # client_id: URL of site being logged into (can extract some stuff to display from this to prevent identity spoofing)
    # state: a value to pass to the callback URI given in 'redirect_uri' to tie the code to the auth request
    # scope:
    # response_type:
    #
    # Response:
    #
    # HTTP/1.1 302 Found
    # Location: https://ownyourgram.com/auth/callback?code=xxxxxxxx&state=1234567890
    #
    # state: the original value of state received
    # code: an authorization code (for later use against the token endpoint)

    return ""


@auth.route("/callback")
def callback():
    return ""


@auth.route("/token")
def token_endpoint():
    return ""
