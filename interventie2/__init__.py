# General imports
from flask import Flask
from flask_talisman import Talisman
from flask_login import LoginManager
from interventie2 import config
from flaskext.markdown import Markdown

app = Flask(__name__)

# Load configuration
app.config.from_object(config.DevelopmentConfig)
app.config.from_envvar('CONFIG_FILE', silent=True)

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
#     'pool_size': 10,
#     'pool_recycle': 60,
#     'pool_pre_ping': True
# }

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "main.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

Talisman(app, content_security_policy=None)
Markdown(app)

# Project imports
from interventie2.main.routes import main
from interventie2.admin.routes import admin
from interventie2.catalog.routes import catalog
from interventie2.tools.routes import tools
from interventie2.export.routes import export
from interventie2.analysis.routes import analysis
from interventie2.error.routes import error
from interventie2.models import User

app.register_blueprint(main, url_prefix='/')
app.register_blueprint(admin, url_prefix='/admin/')
app.register_blueprint(catalog, url_prefix='/catalog/')
app.register_blueprint(tools, url_prefix='/tools/')
app.register_blueprint(export, url_prefix='/export/')
app.register_blueprint(analysis, url_prefix='/analysis/')
app.register_blueprint(error, url_prefix='/error/')