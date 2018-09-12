from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session as login_session
from flask_pymongo import PyMongo

import pandas as pd
import datetime
import bcrypt
import json



app = Flask(__name__)
mongo = PyMongo(app)

CLIENT_ID = json.loads(
    app.open_resource('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "CornerStone"


# Show home page
@app.route('/')
@app.route('/home')
def homePage():
    if 'username' in login_session:

        foods = mongo.db.foods
        test_data = pd.DataFrame(list(foods.find()))
        print(test_data)

        return render_template('index.html', login_session=login_session, test_data=test_data)


    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name': request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user[
            'password']:
            login_session['username'] = request.form['username']
            return redirect(url_for('homePage'))

    flash('Invalid username/password combination')
    return render_template('login.html')


@app.route('/logout')
def logout():

    login_session.clear()
    flash('You have logged out successfully')
    redirect(url_for('homePage'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            newUser = {"name": request.form['username'],
                       "password": hashpass,
                       "defaults": {"nutrition": {
                           "feeding_window": [12, 21],
                           "metrics" : {},
                           "food": {},
                           "supplements": {}
                       },
                           "activity": {}
                       }
                       }

            users.insert(newUser)
            login_session['username'] = request.form['username']
            return redirect(url_for('homePage'))

        flash('That username already exists!')
        return render_template('register.html')

    return render_template('register.html')


# Create or edit today's record
@app.route('/record/<record_date>', methods=['GET', 'POST'])
def editRecord(record_date):
    if 'username' not in login_session:
         return redirect('/')
    if record_date == 'today':
        date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
    else:
        date = datetime.datetime(year=int(record_date[0:4]), month=int(record_date[5:7]), day=int(record_date[8:10]))

    # metrics = 0                                   TODO
    supplements = list(mongo.db.supplements.find())
    activities = list(mongo.db.activities.find())
    foods = list(mongo.db.foods.find())
    metrics = list(mongo.db.metrics.find())
    users = mongo.db.users
    records = mongo.db.records

    today_record = records.find_one({"user": login_session['username'], "date": date})

    if today_record:
        prefill = today_record
    else:
        prefill = users.find_one({"name": login_session['username']})['defaults']

    if request.method == 'POST':

        # if there is an input from the date picker, go to selected date
        if 'goto_date' in request.form:
            return redirect('/record/' + request.form['goto_date'])

        form_input = {
            "user": login_session['username'],
            "date": date,
            "metrics" : {},
            "nutrition": {
                "calories": int(request.form['calories']),
                "feeding_window": [int(x) for x in request.form['feeding_window'].split(",")],
                "food": {},
                "supplements": {
                    "coffee": int(request.form['coffee'])
                }
            },
            "activity": {}
        }

        for metric in metrics:
            name = metric["name"]
            value = int(request.form[name])
            if value:
                form_input["metrics"][name] = value

        # Add non-empty supplements to input object
        for supplement in supplements:
            name = supplement["name"]
            value = int(request.form[name])
            if value:
                form_input["nutrition"]["supplements"][name] = value

        # Add non-empty foods to input object
        for food in foods:
            name = food["name"]
            value = int(request.form[name])
            if value:
                form_input["nutrition"]["food"][name] = value

        # Add non-empty activities to input object
        for activity in activities:
            name = activity["name"]
            intensity = int(request.form[name + "_intensity"])
            time = int(request.form[name + "_time"])
            if intensity:
                form_input["activity"][name] = {"intensity": intensity,
                                                "time": time}

        # update user defaults if option ticked
        if 'save_default' in request.form:
            users.update_one(
                {'username': login_session['username']},
                {'$set': {"defaults": form_input}}
            )

        if today_record:
            records.find_one_and_replace({"user": login_session['username'], "date": date}, form_input)
            flash("Record for {0} Updated.".format(date))
            print(str(today_record))
        else:
            flash("Record Created for: {0}".format(date))
            records.insert(form_input)

        return redirect('/record/today')
    else:
        return render_template("editrecord.html", supplements=supplements, foods=foods, activities=activities, metrics=metrics, prefill=prefill, record_date = record_date, login_session = login_session)


# User Helper Functions
#
#
# def getUserInfo(user_id):
#     users = mongo.db.users
#     user = users.find_one({"email": login_session['email']})
#     return user
#
#
# def getUserID(email):
#     try:
#         users = mongo.db.users
#         user = users.find_one({"email": login_session['email']})
#         return str(user.get('_id'))
#     except:
#         return None


if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)




# Show login page
# @app.route('/login')
# def showLogin():
#     state = ''.join(random.choice(string.ascii_uppercase + string.digits)
#                     for x in range(32))
#     login_session['state'] = state
#     return render_template('login_old.html', STATE=state)


# @app.route('/test/JSON')
# def testJSON():
#     users = mongo.db.users
#     return jsonify(list=[i.serialize for i in records])
#


# @app.route('/gconnect', methods=['POST'])
# def gconnect():
#     # Validate state token
#     if request.args.get('state') != login_session['state']:
#         response = make_response(json.dumps('Invalid state parameter.'), 401)
#         response.headers['Content-Type'] = 'application/json'
#         return response
#     # Obtain authorization code
#     code = request.data
#
#     try:
#         # Upgrade the authorization code into a credentials object
#         oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
#         oauth_flow.redirect_uri = 'postmessage'
#         credentials = oauth_flow.step2_exchange(code)
#     except FlowExchangeError:
#         response = make_response(
#             json.dumps('Failed to upgrade the authorization code.'), 401)
#         response.headers['Content-Type'] = 'application/json'
#         return response
#
#     # Check that the access token is valid.
#     access_token = credentials.access_token
#     url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
#            % access_token)
#     h = httplib2.Http()
#     result = json.loads(h.request(url, 'GET')[1])
#     # If there was an error in the access token info, abort.
#     if result.get('error') is not None:
#         response = make_response(json.dumps(result.get('error')), 500)
#         response.headers['Content-Type'] = 'application/json'
#         return response
#
#     # Verify that the access token is used for the intended user.
#     gplus_id = credentials.id_token['sub']
#     if result['user_id'] != gplus_id:
#         response = make_response(
#             json.dumps("Token's user ID doesn't match given user ID."), 401)
#         response.headers['Content-Type'] = 'application/json'
#         return response
#
#     # Verify that the access token is valid for this app.
#     if result['issued_to'] != CLIENT_ID:
#         response = make_response(
#             json.dumps("Token's client ID does not match app's."), 401)
#         print("Token's client ID does not match app's.")
#         response.headers['Content-Type'] = 'application/json'
#         return response
#
#     stored_access_token = login_session.get('access_token')
#     stored_gplus_id = login_session.get('gplus_id')
#     if stored_access_token is not None and gplus_id == stored_gplus_id:
#         response = make_response(json.dumps('User is already connected.'),
#                                  200)
#         response.headers['Content-Type'] = 'application/json'
#         return response
#
#     # Store the access token in the session for later use.
#     login_session['access_token'] = credentials.access_token
#     login_session['gplus_id'] = gplus_id
#
#     # Get user info
#     userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
#     params = {'access_token': credentials.access_token, 'alt': 'json'}
#     answer = requests.get(userinfo_url, params=params)
#
#     data = answer.json()
#
#     login_session['username'] = data['name']
#     login_session['picture'] = data['picture']
#     login_session['email'] = data['email']
#
#     # see if user exists, if it doesn't make a new one
#     user_id = getUserID(data["email"])
#     if not user_id:
#         user_id = createUser(login_session)
#     login_session['user_id'] = user_id
#
#     output = ''
#     output += '<h1>Welcome, '
#     output += login_session['username']
#     output += '!</h1>'
#     output += '<img src="'
#     output += login_session['picture']
#     output += ''' "style = "width: 300px; height: 300px;
#                  border-radius: 150px;
#                  -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '''
#     return output
#
#
# @app.route('/gdisconnect')
# def gdisconnect():
#     # Disconnect a connected user.
#     access_token = login_session.get('access_token')
#     if access_token is None:
#         response = make_response(
#             json.dumps('Current user not connected.'), 401)
#         response.headers['Content-Type'] = 'application/json'
#         return response
#     url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
#     h = httplib2.Http()
#     result = h.request(url, 'GET')[0]
#     if result['status'] == '200':
#         # Reset the user's sesson.
#         del login_session['access_token']
#         del login_session['gplus_id']
#         del login_session['username']
#         del login_session['email']
#         del login_session['picture']
#
#         response = make_response(json.dumps('Successfully disconnected.'), 200)
#         response.headers['Content-Type'] = 'application/json'
#         return response
#     else:
#         # For whatever reason, the given token was invalid.
#         response = make_response(
#             json.dumps('Failed to revoke token for given user.'), 400)
#         response.headers['Content-Type'] = 'application/json'
#         return response



# @app.route('/insertuser')
# def insertUser():
#     users = mongo.db.users
#     myDict = {"name"    : "Test User3",
#               "id"      : 432,
#               "trends"  : { "entry1"    : 5,
#                             "entry2"    : 10,
#                             "entry3"    : "st1212ring"}
#               }
#
#     users.insert(myDict)
#     return "TEST insert user"
#
# @app.route('/testinsertrecord')
# def insertRecord():
#     records = mongo.db.activities
#
#     itemlist = []
#
#     for item in itemlist:
#         print(item)
#         records.insert(item)
#
#     return "TEST insert items"
#
#
#
# @app.route('/find')
# def findPage():
#     records = mongo.db.records
#     users = mongo.db.users
#     today_dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
#
#     user = users.find_one(ObjectId("5b7eb07960bced39500113d8"))
#     result = user.get('email')
#
#     return str(result)


