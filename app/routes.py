import os 
from flask import render_template, redirect, url_for, flash, request, session
from flask_mail import Message, Mail
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy import and_, event
#import secrets
from PIL import Image
from config import Config
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from app import app, db, bcrypt, mailobject, admin
from app.forms import Formname, formCreateEvent, LoginForm, confirmParticipation, deleteParticipation, EditProfileForm, LeaveFeedback,FeedbackForm, PostForm
from app.models import Student, Event, BusinessPartner, partecipation, Feedback, Post
import forms
from datetime import datetime
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin

#admin = Admin(app,name='keepntouch', template_mode='bootstrap3')
admin.add_view(ModelView(Student,db.session))
admin.add_view(ModelView(BusinessPartner,db.session))
admin.add_view(ModelView(Feedback,db.session))
admin.add_view(ModelView(Post,db.session))
admin.add_view(ModelView(Event,db.session))
@app.before_first_request
def setup_all():
    db.create_all()


#@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():

    confirmParticipation = forms.confirmParticipation()
    deleteParticipation = forms.deleteParticipation()
    LeaveFeedback= forms.LeaveFeedback()
    FeedbackForm = forms.FeedbackForm()
    if "submitD" in request.form and deleteParticipation.validate_on_submit():
        event_id = deleteParticipation.event_id.data
        event = Event.query.filter_by(id=event_id).first()
        student = Student.query.filter_by(id=session.get('id')).first()
        event.numofPeople += -1
        student.partecipations.remove(event)
        db.session.commit()
        return redirect('home')
    elif "submitC" in request.form and confirmParticipation.validate_on_submit():
        # add user to the list of participants
        event_id = confirmParticipation.event_id.data
        event = Event.query.filter_by(id=event_id).first()
        student = Student.query.filter_by(id=session.get('id')).first()

        if not Student.query.join(partecipation).join(Event).filter( (partecipation.c.student_id == student.id) & (partecipation.c.event_id == event.id)).first():
            event.numofPeople += 1

        student.partecipations.append(event)
        db.session.add(student)
        db.session.add(event)
        db.session.commit()

        return redirect('home')

    elif "submitE" in request.form and LeaveFeedback.validate_on_submit():
        # add feedback
        event_id = LeaveFeedback.event_id.data
        session['event_id'] = event_id
        session['event_name'] = Event.query.filter_by(id=event_id).first().name
        return redirect('feedback')

    if current_user.is_authenticated:

        if Student.query.filter_by(email=session.get('email')).first():  ## if student then show the wall
            events=Event.query.all()
            return render_template('index.html', events=events, confirmParticipation=confirmParticipation, deleteParticipation=deleteParticipation, partecipation=partecipation, Student = Student, Event=Event, BPs = BusinessPartner, and_=and_, feedback=feedback, LeaveFeedback=LeaveFeedback)
        elif BusinessPartner.query.filter_by(email=session.get('email')).first():

             #if bp show its own events
            events = Event.query.filter_by(bp_id=session.get('id'))
            return render_template('index.html', events=events, BPs = BusinessPartner)
    else:
        return redirect('welcome')

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    formpage = FeedbackForm()

    if formpage.validate_on_submit():
        event = Event.query.filter_by(id=session.get('event_id')).first()
        student = Student.query.filter_by(id=session.get('id')).first()
        print "Your feedback's been posted bro"
        feedback = Feedback(
            student_id = student.id,
            event_id = event.id,
            title=formpage.title.data,
            content=formpage.content.data
        )

        db.session.add(feedback)
        db.session.commit()
        flash('Your feedback has been posted', 'success')
        return redirect(url_for('home'))

    return render_template('feedback_post.html', formpage = formpage)

@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/register",methods=['GET','POST'])
def register():
    formpage=Formname()

    if formpage.validate_on_submit():
        password_1 = bcrypt.generate_password_hash(formpage.password.data).encode('utf-8')

        if formpage.usertype.data=="Student":
            reg=Student(name=formpage.name.data,
                email=formpage.email.data,
                password=password_1,
                university=formpage.university.data ) #role=Role.query.filter_by(name='Student'))
            db.session.add(reg)
            db.session.commit()
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
        return redirect(url_for('login'))  #TODO create an html page informing the user about success of his registration to render after it
    flash("Congratulations, you are now a registered user!")
    return render_template('register.html', formpage = formpage , title='Register ')

@app.route("/login",methods=['GET','POST'])
def login():
    #if current_user.is_authenticated:
    #    return redirect(url_for('home'))
    formpage=LoginForm()
    if formpage.validate_on_submit():

        st=Student.query.filter_by(email=formpage.email.data).first()
        bp = BusinessPartner.query.filter_by(email=formpage.email.data).first()
        if st and bcrypt.check_password_hash(st.password,formpage.password.data):
            session['email']=st.email
            session['name']=st.name
            session['uni']=st.university
            session['id']=st.id
            session['student']=True
            login_user(st)
        elif bp and bcrypt.check_password_hash(bp.password,formpage.password.data):
            session['email']=bp.email
            session['name']=bp.name
            session['id']=bp.id
            session['student'] = False
            login_user(bp)

    return render_template('login.html', formpage = formpage,
                           email=session.get('email',False) ,
                           title='Login ')

@app.route('/logout')
def logout():
    current_user.image_file = ""
    logout_user()
    session.clear()
    return redirect(url_for('welcome'))

@app.route("/createevent",methods=['GET','POST'])
def createEvent():
    formpage=formCreateEvent()

    if formpage.validate_on_submit():
        reg = Event(
            name=formpage.name.data,
            date=formpage.date.data,
            bp_id=session.get('id'),
            description=formpage.description.data,
            numofPeople=0,
            location=formpage.location.data
        )

        db.session.add(reg)
        db.session.commit()

        return redirect(url_for('home'))  # btw the BP should see the new event on its wall
    #if BP then ok
    if session.get('student') == False:
        return render_template('createevent.html', formpage = formpage , title='Create new Event')
    elif session.get('student') == True:
        return render_template('youcannot.html')
    else:
        return redirect('login')
    #if a student then you can't

photos = UploadSet('photos', IMAGES)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():


    image_file = "/static/default.jpeg"
    if current_user.is_authenticated:
        st = Student.query.filter_by(email=current_user.email).first_or_404()
        page = request.args.get('page', 1, type=int)
        posts = st.posts.order_by(Post.timestamp.desc()).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('profile', name=st.name, page=posts.next_num) \
            if posts.has_next else None
        prev_url = url_for('profile', name=st.name, page=posts.prev_num) \
            if posts.has_prev else None
        return render_template('profile.html',student=st, image_file=image_file, posts=posts.items, next_url=next_url, prev_url=prev_url)
    else:
        return redirect('login')


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.about_me = form.about_me.data
        current_user.university = form.university.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.about_me.data = current_user.about_me
        form.university.data= current_user.university
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/events/<id>')
@login_required
def events(id):
    event = Event.query.filter_by(id=id).first()
    feedbacks = Feedback.query.filter_by(event_id=id)
    return render_template("viewevent.html", title=event.name, feedbacks=feedbacks, Student = Student)

@app.route("/")
@app.route("/welcome")
def welcome():
    return render_template("welcome.html")

@app.route("/map")
def map():
    return render_template("map.html")

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


@app.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    form=PostForm()

    if  form.validate_on_submit():
       post = Post(body=form.post.data, author=current_user)
       db.session.add(post)
       db.session.commit()
       flash('Your post is now live!')
       return redirect(url_for('explore'))


    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page,app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
      if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
      if posts.has_prev else None
    return render_template('explore.html', title='Home', form=form,
                       posts=posts.items, next_url=next_url,
                       prev_url=prev_url)



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500