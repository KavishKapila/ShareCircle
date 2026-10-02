from pathlib import Path
from flask import Flask, g, render_template
from .config import Config
from .db import close_db, get_db, init_db

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)

    from .blueprints.auth import auth_bp
    from .blueprints.main import main_bp
    from .blueprints.api import api_bp
    from .blueprints.judge import judge_bp, hackathon_bp, purge_legacy_demo_data
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(judge_bp, url_prefix='/api/judge')
    app.register_blueprint(hackathon_bp, url_prefix='/api/hackathon')

    @app.context_processor
    def inject_globals():
        unread = 0
        if g.user is not None:
            row = get_db().execute(
                'SELECT COUNT(*) AS c FROM notifications WHERE user_id = ? AND read = 0',
                (g.user['id'],),
            ).fetchone()
            unread = int(row['c'])
        return {
            'current_user': g.user,
            'notification_unread': unread,
            'app_version': app.config['VERSION'],
        }

    @app.errorhandler(404)
    def not_found(_error):
        return render_template('404.html'), 404

    with app.app_context():
        init_db()
        # Remove test accounts created by pre-Overlap Judge Mode builds.
        # Current Judge Mode never writes demo people to the real DB.
        purge_legacy_demo_data(get_db())
    return app
