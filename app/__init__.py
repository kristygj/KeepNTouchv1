from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from config import Config
from flask_moment import Moment
from flask_admin import Admin

app = Flask(__name__)
app.config.from_object(Config)
app.config['FLASK_ADMIN_SWATCH']='cerulean'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mailobject = Mail(app)
login= LoginManager(app)
bootstrap=Bootstrap(app)
moment=Moment(app)

login.login_view = 'login'
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB
admin=Admin(app,name='keepntouch', template_mode='bootstrap3')
from app import routes, models

#print IMAGES
#print 'this is file path %s' % app.config['UPLOADED_PHOTOS_DEST']







#from forms import *
#import forms

# def send_mail(to, subject, template, **kwargs):
#     msg=Message(subject,
#                 sender=app.config['MAIL_USERNAME'],
#                 recipients=[to])
#     # msg.body=render_template(template+'.txt',**kwargs)
#     msg.html=render_template(template+'.html',**kwargs)
#     mailobject.send(msg)





