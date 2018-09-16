from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session as login_session
from flask_pymongo import PyMongo
from utility import Record, User, Food

import pandas as pd
import datetime
import bcrypt
import json




app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/cornerstonePrimary"
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
    return redirect(url_for('homePage'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':

        newUser = User(request.form, mongo.db)

        if newUser.save_to_db():
            login_session['username'] = newUser.name
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

    if request.method == 'POST':
        if 'goto_date' in request.form:
            return redirect('/record/' + request.form['goto_date'])

        newRecord = Record(request.form, mongo.db)
        newRecord.save_to_mongo(login_session['username'], date)
        return redirect('/record/today')
    else:

        existing_record = mongo.db.records.find_one({"user": login_session['username'], "date": date})

        if existing_record:
            prefill = existing_record
        else:
            prefill = mongo.db.users.find_one({"name": login_session['username']})['defaults']

        return render_template("editrecord.html",
                               supplements=list(mongo.db.supplements.find()),
                               foods=list(mongo.db.foods.find()),
                               activities=list(mongo.db.activities.find()),
                               metrics=list(mongo.db.metrics.find()),
                               prefill=prefill,
                               record_date=record_date,
                               login_session=login_session
                               )


@app.route('/editfood/<food_name>', methods=['POST', 'GET'])
def editFood(food_name):
    if 'username' not in login_session:
         return redirect('/')

    if request.method == 'POST':

        newFood = Food(request.form, mongo.db)
        if food_name == 'createnew' and mongo.db.foods.find_one({
            '$or': [
                {'name': newFood.name},
                {'label': newFood.label}
            ]
        }):
            flash("A food by that DB name or label already exists.")
            return render_template('editfood.html', food_name=food_name, food=newFood.json(), login_session=login_session)
        elif not newFood.name or not newFood.label:
            flash("Label and DB name can not be empty.")
            return render_template('editfood.html', food_name=food_name, food=newFood.json(), login_session=login_session)
        newFood.save_to_db(food_name)
        return redirect('/foods')
    else:
        food = mongo.db.foods.find_one({"name": food_name})
        return render_template('editfood.html', food=food, food_name=food_name, login_session=login_session)


@app.route('/foods', methods=['POST', 'GET'])
def foodsPage():
    if 'username' not in login_session:
         return redirect('/')
    foods = list(mongo.db.foods.find())
    return render_template('foods.html', foods=foods, login_session=login_session)


if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)



# @app.route('/util')
# def util():
#
#
#     flash('insert successful')

