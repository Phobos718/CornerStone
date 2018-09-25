from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session as login_session
from flask_pymongo import PyMongo

from bokeh.embed import components
from bokeh.models import ColumnDataSource, Spacer, Select, Jitter
from bokeh.layouts import column, row, widgetbox
from bokeh.themes import Theme
from bokeh.plotting import curdoc, figure

from models import Record, User, Food

import pandas as pd
import numpy as np
import datetime
import bcrypt


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/sophrosynePrimary"
#app.config["MONGO_URI"] = "mongodb://user:password@18.130.75.134:27017/cornerStone?authSource=admin"
mongo = PyMongo(app)



# CLIENT_ID = json.loads(
#     app.open_resource('client_secret.json', 'r').read())['web']['client_id']
# APPLICATION_NAME = "CornerStone"


# Show home page
@app.route('/')
@app.route('/home')
def homePage():
    if 'username' in login_session:
        data = list(mongo.db.records.find({"user": "Suplu718"}))
        # df = pd.DataFrame(data)
        # df["date"] = pd.to_date(df["date"])
        df = pd.io.json.json_normalize(data)
        test_data = list(df)

        # Create the plot
        plot = create_figure()

        # Embed plot into HTML via Flask Render
        script, div = components(plot)
        return render_template("index.html", test_data=test_data, script=script, div=div, login_session=login_session)

        # return render_template('index.html', login_session=login_session, test_data=test_data)


    return render_template('login.html')


#Dashboard plotting helper function
def create_figure():

    data = list(mongo.db.records.find({"user": "Suplu718"}).sort('date', 1))
    df = pd.io.json.json_normalize(data).fillna(0)
    df.set_index('date')


    # TODO - create dict of selectable options and what values they pull.
    # TODO - Some of them will pull 1 value, others will pull a list of 2
    # TODO - and apply that to bar height and alpha

    # Plotting Setup

    source = ColumnDataSource(data=dict(date=df['date'], metric1=[], metric2=[], factor1=df['supplements.modafinil'], factor2=[]))
    source.data = source.from_df(df[['metrics.sleep_hours', 'metrics.insomnia', 'supplements.modafinil', 'misc.coffee']])

    vhist, vedges = np.histogram(df['metrics.sleep_quality'].fillna(0), bins=10)
    vzeros = np.zeros(len(vedges) - 1)
    vmax = max(vhist) * 1.1


    p_timeline = figure(x_axis_type="datetime", x_axis_label='Date', y_axis_label='Variable', plot_height=300,
                plot_width=1000, tools='pan,box_zoom,reset')
    p_factors = figure(x_axis_type="datetime", x_range=p_timeline.x_range, plot_height=100, plot_width=1000,
                tools='pan,box_zoom,hover,reset')
    pv = figure(toolbar_location=None, plot_width=200, plot_height=p_timeline.plot_height, x_range=(-vmax, vmax),
                y_range=p_timeline.y_range, min_border=10, y_axis_location="right")
    p3 = figure(plot_height=400, plot_width=400, tools='pan,box_zoom,hover,reset')


    # Timeline plotting

    p_timeline.vbar(x=df['date'], top=df['metrics.sleep_hours'], alpha=(df['metrics.sleep_quality']-2)/10, color='#ADD8E6', width=20 * 60 * 60 * 1000)
    p_timeline.vbar(x=df['date'], top=df['metrics.insomnia'], alpha=0.8, color='red', width=20 * 60 * 60 * 1000)

    # p_timeline.vbar(x='date', top='metric1', source=source, alpha='metric1', color='#ADD8E6', width=20 * 60 * 60 * 1000)
    # p_timeline.vbar(x='date', top='metric2', source=source, alpha=0.8, color='red', width=20 * 60 * 60 * 1000)


    inc = df['metrics.afternoon'] >= df['metrics.morning']
    dec = df['metrics.morning'] > df['metrics.afternoon']
    p_timeline.line(df['date'], df[['metrics.morning', 'metrics.afternoon']].mean(axis=1), line_width=6, color='#ADD8E6')
    p_timeline.segment(df.date[inc], df['metrics.morning'][inc], df.date[inc], df['metrics.afternoon'][inc], color="green", line_width=4, line_cap='round')
    p_timeline.segment(df.date[dec], df['metrics.morning'][dec], df.date[dec], df['metrics.afternoon'][dec], color='#ff9e21', line_width=4, line_cap='round')


    # Timeline histogram


    pv.ygrid.grid_line_color = None
    pv.xaxis.major_label_orientation = np.pi / 4
    pv.quad(left=0, bottom=vedges[:-1]+0.05, top=vedges[1:]-0.05, right=vhist, color='#ADD8E6')
    vh1 = pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vzeros, alpha=0.5)
    vh2 = pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:], right=vzeros, alpha=0.1)


    # Factors plotting

    ser=(df['supplements.modafinil']/25).fillna(0) + pd.to_numeric(df['misc.coffee'])
    p_factors.vbar(x=df['date'], top=ser, color='#ADD8E6', alpha=1, width=20 * 60 * 60 * 1000)


    # Scatter plot

    # p3 = figure(plot_height=400, plot_width=400, tools='pan,box_zoom,hover,reset')
    # rand1 = np.random.randint(-5, 5, df.shape[0])/10
    # rand2 = np.random.randint(-5, 5, df.shape[0])/10
    # p3.circle(x={'value': df['metrics.sleep_quality'], 'transform': Jitter(width=1)}, y=df['metrics.morning']+df['metrics.afternoon'], color='#ADD8E6', size=df['supplements.piracetam'].fillna(0).shift(-1)/25*3+6, alpha=0.5)
    # p3.xaxis.axis_label = 'Sleep Quality'
    # p3.yaxis.axis_label = 'Day Rating'


    def update(attr, old, new):
        print('---------------------------update firing')
        source.data['factor1'] = df['factor1.value']



    # Create a dropdown Select widget: select

    metric1 = Select(title='Metric1', value='foo', options=['supplements.modafinil', 'bar', 'baz'])
    metric1.on_change('value', update)

    metric2 = Select(title='Metric2', value='bar', options=['foo', 'bar', 'baz'])
    metric2.on_change('value', update)

    factor1 = Select(title='Factor1', value='misc.coffee', options=['supplements.modafinil', 'misc.coffee', 'baz'])
    factor1.on_change('value', update)

    factor2 = Select(title='Factor2', value='bar', options=['foo', 'bar', 'baz'])
    factor2.on_change('value', update)


    controls = widgetbox([metric1, metric2, factor1, factor2], width=200)
    main_row = row(p_timeline, pv)
    bottom_row = row(controls, p3)

    layout = column(main_row, p_factors, Spacer(width=200, height=100), bottom_row)
    # TODO under day chart double bar chart with in red on the bottom: insomnia, with blue above: sleep time and sleep quality is color coded


    theme = Theme("theme.yaml")
    doc = curdoc()
    doc.theme = theme
    doc.add_root(layout)

    return layout






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


# @app.route('/util')
# def util():
#
#     data = list(mongo2.db.records.find())
#
#     for item in data:
#         try:
#             mongo.db.records.insert(item)
#         except:
#             print('Insert aborted: document' + str(item['_id']) + ' already exists.')
#
#
#     print("insertion complete")
#
#     flash('insert successful')
#     return redirect(url_for('homePage'))


if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)






