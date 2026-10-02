from functools import wraps
from flask import g, jsonify, redirect, request, session, url_for

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('auth.login', next=request.full_path if request.query_string else request.path))
        return view(*args, **kwargs)
    return wrapped

def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return jsonify({'error': 'Authentication required.'}), 401
        return view(*args, **kwargs)
    return wrapped
