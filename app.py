from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired
from flask_oauthlib.client import OAuth
import time
import requests

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

# Sea Locations
sea_locations = [
    {"name": "Black Sea", "latitude": 43.4130, "longitude": 34.2993},
    {"name": "Mediterranean Sea", "latitude": 34.5531, "longitude": 18.0480},
    {"name": "Aegean Sea", "latitude": 39.0192, "longitude": 25.2686},
    {"name": "Marmara Sea", "latitude": 40.6681, "longitude": 28.1123}
]

# Dictionary to keep track of failed login attempts
failed_login_attempts = {}

# Dictionary to store blocked emails and their unblock time
blocked_emails = {}

# Configure Google OAuth
app.config['GOOGLE_ID'] = 'id'
app.config['GOOGLE_SECRET'] = 'secret'
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


@app.route('/sea', methods=['GET', 'POST'])
def sea():
    nearest_sea = "... Sea"
    distance_to_sea = 0

    if request.method == 'POST':
        data = request.get_json()
        user_latitude = data['latitude']
        user_longitude = data['longitude']

        nearest_sea, distance_to_sea = find_nearest_sea(user_latitude, user_longitude)
        return jsonify(nearest_sea=nearest_sea, distance_to_sea=distance_to_sea)

    return render_template('sea.html', nearest_sea=nearest_sea, distance_to_sea=distance_to_sea)


@app.route('/sun', methods=['GET', 'POST'])
def sun():
    distance_to_sun = 0

    sun_latitude = 58.8430
    sun_longitude = 76.9489

    if request.method == 'POST':
        data = request.get_json()
        user_latitude = data['latitude']
        user_longitude = data['longitude']

        distance_to_sun = calculate_distance(user_latitude, user_longitude, sun_latitude, sun_longitude)
        return jsonify(distance_to_sun=distance_to_sun)

    return render_template('sun.html', distance_to_sun=distance_to_sun)


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

def get_nearest_sea(latitude, longitude):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={google_maps_api_key}'
    response = requests.get(url)
    data = response.json()

    # Print the entire API response for inspection
    print("Google Maps Geocoding API Response:")
    print(data)

    if response.status_code == 200:
        print("status 200, first if")
        if data['status'] == 'OK':
            print("status ok, second if")
            for result in data['results']:
                for component in result['address_components']:
                    print(component)
                    if 'sea' in component['long_name'].lower():
                        print("sea, third if")
                        nearest_sea = component['long_name']
                        sea_latitude = result['geometry']['location']['lat']
                        sea_longitude = result['geometry']['location']['lng']
                        return nearest_sea, sea_latitude, sea_longitude
            # If no sea component found, return default values or handle appropriately
            return None, None, None
        else:
            print(f"Geocoding request failed with status: {data['status']}")
            return None, None, None
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return None, None, None


def find_nearest_sea(user_latitude, user_longitude):
    # Initialize variables to keep track of the nearest sea and its distance
    nearest_sea_name = None
    nearest_distance = float('inf')  # Start with a large value

    # Iterate through each sea location
    for sea_ in sea_locations:
        sea_name = sea_["name"]
        sea_latitude = sea_["latitude"]
        sea_longitude = sea_["longitude"]

        # Calculate distance to this sea location
        distance = calculate_distance(user_latitude, user_longitude, sea_latitude, sea_longitude)

        # Update nearest sea if this one is closer
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_sea_name = sea_name

    return nearest_sea_name, nearest_distance


def calculate_distance(lat1, lon1, lat2, lon2):
    # Calculate distance between two points using Haversine formula
    from math import radians, sin, cos, sqrt, atan2

    R = 6371.0  # Radius of the Earth in kilometers

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c  # Distance in kilometers
    return distance


if __name__ == '__main__':
    app.run(debug=True)