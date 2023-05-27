import os
from flask import current_app, Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_user, logout_user, current_user, login_required


error = Blueprint('error', __name__,
                 template_folder='templates',
                 static_folder='static',
                 static_url_path='assets')


