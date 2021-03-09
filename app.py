import os
from flask import Flask ,render_template , url_for,flash,redirect
from flask import request,session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
#from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_login import LoginManager,login_user,logout_user





app = Flask(__name__)
app.config['SECRET_KEY'] = 'cXjCnwAeojwfoEehwgfdrwefsADnrnsEmls'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///website.db'
app.config['UPLOADED_PHOTOS_DEST'] = os.getcwd()+"/static"
app.config['MAIL_SERVER']='smtp.mail.com'
app.config['MAIL_PORT']=587
app.config['MAIL_TLS']=True
app.config['MAIL_USERNAME']='keepntouch@engineer.com'
app.config['MAIL_PASSWORD']='keepntouch'


db=SQLAlchemy(app)
bcrypt=Bcrypt(app)
mailobject=Mail(app)
login_manager=LoginManager()
login_manager.init_app(app)

#photos = UploadSet('photos', IMAGES)
#configure_uploads(app, photos)
#patch_request_class(app)  # set maximum file size, default is 16MB

#print IMAGES
#print 'this is file path %s' % app.config['UPLOADED_PHOTOS_DEST']

partecipation = db.Table('partecipation',
                   db.Column('student_id', db.Integer, db.ForeignKey('student.id')),
                   db.Column('event_id', db.Integer, db.ForeignKey('event.id'))
                )

class Student(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password=db.Column(db.String(100),nullable=False)
    university = db.Column(db.String(50), nullable=True)
    partecipations = db.relationship('Event', secondary=partecipation, backref=db.backref('partecipants', lazy='joined'))

    def __repr__(self):
        return "<Student %r>" % self.name

class Event(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=True)
    date = db.Column(db.Date)
    bp_id = db.Column(db.Integer, db.ForeignKey('businesspartner.id'))
    description=db.Column(db.String(500))
    maxPeople = db.Column(db.Integer)
    location = db.Column(db.String(100))
    #partecipants = db.relationship("Student", secondary=partecipation)

    def __repr__(self):
        return "<Event %r>" % self.name


class BusinessPartner(db.Model):
    __tablename__ = 'businesspartner'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    events = db.relationship('Event', backref='creator', ) #creator column of the Event row contains the BP who created it

    def __repr__(self):
        return "<Business Partner %r>" % self.name

@app.before_first_request
def setup_all():
    db.create_all()

from forms import *
import forms

# def send_mail(to, subject, template, **kwargs):
#     msg=Message(subject,
#                 sender=app.config['MAIL_USERNAME'],
#                 recipients=[to])
#     # msg.body=render_template(template+'.txt',**kwargs)
#     msg.html=render_template(template+'.html',**kwargs)
#     mailobject.send(msg)




def send_mail(to,subject,template,**kwargs):
    msg=Message(subject,recipients=[to],sender=app.config['MAIL_USERNAME'])
    msg.body= render_template(template + '.txt',**kwargs)
    msg.html= render_template(template + '.html',**kwargs)
    mailobject.send(msg)


class mailClass():

    template = "mail.html"
    sender = app.config['MAIL_USERNAME']
    subject = ""
    toList = []
    def send(self,**kwargs):
        msg=Message(subject=self.subject,recipients=self.toList,sender=self.sender)
        msg.html=render_template(self.template,**kwargs)
        mailobject.send(msg)


def sendmail(**kwargs):

    mailc=mailClass()
    mailc.toList=[kwargs['email']]
    mailc.subject=[kwargs['subject']]
    mailc.send(user=kwargs['user'])

    #print "mail has been send"
    return True


# @app.route('/mail')
# def mail():
#     send_mail('m.ghazivakili@gmail.com','Test message','mail',message_body='Hi this is a test')
#     return 'message has beed send!'


#@app.route("/upload",methods=["POST","GET"])
#def upload():
 #   if session.get('id'):
  #      if not os.path.exists('static/'+ str(session.get('id'))):
   #         os.makedirs('static/'+ str(session.get('id')))
    #    file_url = os.listdir('static/'+ str(session.get('id')))
     #   file_url = [ str(session.get('id')) +"/"+ file for file in file_url]
      #  formupload = UploadForm()
       # #print session.get('email')
        #if formupload.validate_on_submit():
         #   filename = photos.save(formupload.file.data,name=str(session.get('id'))+'.jpg',folder=str(session.get('id')))
          #  file_url.append(filename)
        #return render_template("upload.html",formupload=formupload,filelist=file_url) # ,filelist=file_url
    #else:
     #   return redirect('login')

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    confirmParticipation = forms.confirmParticipation()
    if confirmParticipation.validate_on_submit():
        # add user to the list of participants
        event_id = confirmParticipation.event_id.data
        event = Event.query.filter_by(id=event_id).first()
        student = Student.query.filter_by(id=session.get('id')).first()
        print "event id is " + str(event_id)
        print "student is " + student.name
        print "partecipations are " + str(student.partecipations)
        student.partecipations.append(event)

        db.session.add(student)
        #db.session.add(event)

        db.session.commit()

        return redirect('home')
    if session.get('id'):

        if Student.query.filter_by(email=session.get('email')).first(): # if student then show the wall
            events=Event.query.all()
            return render_template('index.html', events=events, confirmParticipation=confirmParticipation, BPs = BusinessPartner)
        else: # if bp show its own events
            events = Event.query.filter_by(id=session.get('id'))
            return render_template('index.html', events=events, BPs = BusinessPartner)
    else:
        return redirect('login')


@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/register",methods=['POST','GET'])
def register():
    formpage=Formname()

    if formpage.validate_on_submit():
        password_1 = bcrypt.generate_password_hash(formpage.password.data).encode('utf-8')

        if formpage.usertype.data=="Student":
             reg=Student(name=formpage.name.data,
                email=formpage.email.data,
                password=password_1,
                university=formpage.university.data ) #role=Role.query.filter_by(name='Student'))
        elif formpage.usertype.data=="Activity Owner":
            reg=BusinessPartner(
                name=formpage.name.data,
                email=formpage.email.data,
                password=password_1
            )
        db.session.add(reg)
        db.session.commit()
        try:
            sendmail(email=formpage.email.data, subject='Welcome onboard!', user=formpage.name.data)
        except:
            print "Some error with the given mail"
        return redirect(url_for('home'))  #TODO create an html page informing the user about success of his registration to render after it
    return render_template('register.html', formpage = formpage , title='Register Page')


@app.route("/login",methods=['POST','GET'])
def login():
    formpage=LoginForm()
    if formpage.validate_on_submit():
        # TODO make login possible also for BPs
        st=Student.query.filter_by(email=formpage.email.data).first()
        bp = BusinessPartner.query.filter_by(email=formpage.email.data).first()
        if st and bcrypt.check_password_hash(st.password,formpage.password.data):
            session['email']=st.email
            session['name']=st.name
            session['uni']=st.university
            session['id']=st.id
            session['student']=True
        elif bp and bcrypt.check_password_hash(bp.password,formpage.password.data):
            session['email']=bp.email
            session['name']=bp.name
            session['id']=bp.id
            session['student'] = False

    return render_template('login.html', formpage = formpage,
                           email=session.get('email',False) ,
                           title='Login Page')
@login_manager.user_loader
def load_user(user_id):
    return Student.get(id)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/createevent",methods=['POST','GET'])
def createEvent():
    formpage=formCreateEvent()

    if formpage.validate_on_submit():
        reg = Event(
            name=formpage.name.data,
            date=formpage.date.data,
            bp_id=session.get('id'),
            description=formpage.description.data,
            maxPeople=formpage.maxPeople.data,
            location=formpage.location.data
        )

        db.session.add(reg)
        db.session.commit()
        # sendmail(email=formpage.email.data, user=formpage.name.data, subject='Welcome onboard!') #if u want TODO send a mail when event is created successfully
        return redirect(url_for('home'))  # btw the BP should see the new event on its wall
    #if BP then ok
    if session.get('student') == False:
        return render_template('createevent.html', formpage = formpage , title='Create new Event')
    elif session.get('student') == True:
        return render_template('youcannot.html')
    else:
        return redirect('login')
    #if a student then you can't


@app.route("/profile")
def profiles(): #correct this one
    if session.get('id'):
        if session.get('student') == True:
            st=Student.query.filter_by().all()
            return render_template("profile.html",student=st)

    else:
        return redirect('login')

@app.route("/map")
def map():
    return render_template("map.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
