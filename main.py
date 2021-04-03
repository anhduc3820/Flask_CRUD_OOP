from threading import __all__
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from flask_login import logout_user
import datetime
import json
from flask_mail import Mail,Message

app = Flask(__name__)
app.secret_key = "Secret Key"
oauth = OAuth(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/my_data'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GOOGLE_CLIENT_ID'] = "53375158605-vbg4tdc9jpa5g34cmo0j29lqbnspnjgc.apps.googleusercontent.com"
app.config['GOOGLE_CLIENT_SECRET'] = "N7mHeR7Ksqw3g79vxRfuZfcs"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "buianhduck2@gmail.com"
app.config['MAIL_PASSWORD'] = "abc13579"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

google = oauth.register(
    name = 'google',
    client_id = app.config["GOOGLE_CLIENT_ID"],
    client_secret = app.config["GOOGLE_CLIENT_SECRET"],
    access_token_url = 'https://accounts.google.com/o/oauth2/token',
    access_token_params = None,
    authorize_url = 'https://accounts.google.com/o/oauth2/auth',
    authorize_params = None,
    api_base_url = 'https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint = 'https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs = {'scope': 'openid email profile'},
)

db = SQLAlchemy(app)

#Creating model table for our CRUD database
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(250), nullable=False)
    verified_email = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(120), nullable=True)
    given_name = db.Column(db.String(120), nullable=True)
    family_name = db.Column(db.String(120), nullable=True)
    picture = db.Column(db.Text, nullable=True)
    locale = db.Column(db.String(120), nullable=True)
    tokens = db.Column(db.Text)

    def __init__(self, email, verified_email, name, given_name, family_name, picture, locale, tokens):
        self.email = email
        self.verified_email = verified_email
        self.name = name
        self.given_name = given_name
        self.family_name = family_name
        self.picture = picture
        self.locale = locale
        self.tokens = tokens

class Data(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(100))
 
 
    def __init__(self, name, email, phone):
 
        self.name = name
        self.email = email
        self.phone = phone

    

@app.route('/index', methods=["GET"])
def index():
    my_data = Data.query.all()
    user = User.query.all()
    return render_template("index.html", employees=my_data, user=user)

@app.route('/', methods=["GET"])
def get_login():
    return render_template("login.html")

@app.route('/login/google')
def google_login():
    google = oauth.create_client('google')
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize', methods = ['GET'])
def google_authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo').json()
    email = resp['email']
    verified_email = resp['verified_email']
    name = resp['name']
    given_name = resp['given_name']
    family_name = resp['family_name']
    picture = resp['picture']
    locale = resp['locale']
    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(email = email,
                    verified_email = verified_email, 
                    name = name, 
                    given_name = given_name,
                    family_name = family_name, 
                    picture = picture, 
                    locale = locale,
                    tokens = json.dumps(token)
                    )
        db.session.add(user)
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/logout', methods=["GET", "POST"])
def logout():
    session.pop('email')
    return redirect(url_for('get_login'))

@app.route('/insert', methods=["GET", "POST"])
def insert():
    if request.method == "POST":

        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        my_data = Data(name, email, phone)
        db.session.add(my_data)
        db.session.commit()

        flash("Employee Inserted Successfully")
        return redirect(url_for('index'))

@app.route('/update', methods=["GET", "POST"])
def update():
    if request.method == "POST":
        my_data = Data.query.filter_by(id=request.form.get('id')).first()

        my_data.name = request.form.get('name')
        my_data.email = request.form.get('email')
        my_data.phone = request.form.get('phone')

        db.session.commit()
        flash("Employee Update Successfully")
        return redirect(url_for('index'))

@app.route('/delete/<id>/', methods=["GET", "POST"])
def delete(id):
    my_data = Data.query.get(id)
    db.session.delete(my_data)
    db.session.commit()
    flash("Employee Delete Successfully")
    return redirect(url_for('index'))

@app.route('/email_compose')
def email_compose():
    user = User.query.all()
    return render_template('email-compose.html', user=user)

@app.route('/send_message', methods=["GET", "POST"])
def send_message():
    if request.method == "POST":
        email = request.form['email']
        subject = request.form['subject']
        msg = request.form['message']
        print(email)
        print(subject)
        print(msg)
        message = Message(subject, sender="buianhduck2@gmail.com", recipients=[email])
        message.body = msg
        mail.send(message)
    return redirect(url_for('email_compose'))

@app.route('/email_inbox')
def email_inbox():
    user = User.query.all()
    return render_template('email-inbox.html', user=user)

@app.route('/email_read')
def email_read():
    user = User.query.all()
    return render_template('email-read.html', user=user)

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/profile')
def profile():
    user = User.query.all()
    return render_template('profile.html',user=user)

if __name__ == '__main__':
    app.run(debug=True)