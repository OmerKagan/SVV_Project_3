from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired
from flask_oauthlib.client import OAuth
import time

app = Flask(__name__)
app.secret_key = '123app'

# Disable CSRF protection, otherwise CSRF token is required
app.config['WTF_CSRF_ENABLED'] = False

# Define a map containing emails and corresponding passwords
user_credentials = {
    'user1@login.com': 'password1',
    'user2@login.com': 'password2',
    'user3@login.com': 'password3'
}

# Dictionary to keep track of failed login attempts
failed_login_attempts = {}

# Dictionary to store blocked emails and their unblock time
blocked_emails = {}

# Configure Google OAuth
oauth = OAuth(app)
google = oauth.remote_app(
    'google',
    consumer_key=app.config.get('GOOGLE_ID'),
    consumer_secret=app.config.get('GOOGLE_SECRET'),
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = ''
    if form.email.data == '' or form.password.data == '':
        error = 'Empty email or password!'
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # Check if email is blocked
        if email in blocked_emails and time.time() < blocked_emails[email]:
            error = 'Account temporarily blocked! Try again later.'
        else:
            # Check credentials and authenticate user
            if authenticate_user(email, password):
                if email in failed_login_attempts:
                    del failed_login_attempts[email]  # Reset failed attempts
                session['user'] = email
                return redirect(url_for('entry_page'))
            else:
                error = 'Invalid email or password!'
                # Increment failed attempts count
                if email in failed_login_attempts:
                    failed_login_attempts[email] += 1
                else:
                    failed_login_attempts[email] = 1

                # Block account if attempts reach 5
                if failed_login_attempts[email] >= 5:
                    blocked_emails[email] = time.time() + 60  # Block for 60 seconds

    return render_template('login.html', form=form, error=error)


@app.route('/entry-page')
def entry_page():
    if 'user' in session:
        return render_template('entry_page.html', user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/sea')
def sea():
    # Add logic for new_page_1 here if needed
    return render_template('sea.html')


@app.route('/sun')
def sun():
    # Add logic for new_page_2 here if needed
    return render_template('sun.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/google-login')
def google_login():
    return google.authorize(callback=url_for('google_authorized', _external=True))


@app.route('/google-authorized')
def google_authorized():
    resp = google.authorized_response()
    if resp is None or resp.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )
    session['google_token'] = (resp['access_token'], '')
    user_info = google.get('userinfo')
    session['user'] = user_info.data['email']
    return redirect(url_for('entry_page'))


@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')


def authenticate_user(email, password):
    # Check if the email exists in the user_credentials map and if the password matches
    if email in user_credentials and user_credentials[email] == password:
        return True
    else:
        return False


if __name__ == '__main__':
    app.run(debug=True)
