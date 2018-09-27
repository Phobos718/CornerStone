from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session as login_session
from flask_pymongo import PyMongo
from bokeh.embed import components
from bokeh.models import ColumnDataSource, Spacer, Select, CustomJS, Slider
from bokeh.layouts import column, row, widgetbox
from bokeh.themes import Theme
from bokeh.plotting import curdoc, figure
from bokeh.transform import jitter
from models import Record, User, Food
import pandas as pd
import numpy as np
import datetime
import bcrypt
import os


app = Flask(__name__)

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
mongo = PyMongo(app)


# Show home page
@app.route('/')
@app.route('/home')
def homePage():
    if 'username' in login_session:

        # Create the plot
        plot = create_figure(login_session['username'])

        # Embed plot into HTML via Flask Render
        script, div = components(plot)
        return render_template(
            "index.html",
            script=script,
            div=div,
            login_session=login_session
        )

    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name': request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
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
        newRecord.save_to_db(login_session['username'], date)
        return redirect('/record/today')
    else:

        existing_record = mongo.db.records.find_one({"user": login_session['username'], "date": date})

        if existing_record:
            prefill = existing_record
        else:
            prefill = mongo.db.users.find_one({"name": login_session['username']})['defaults']

        return render_template(
            "editrecord.html",
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
            return render_template(
                'editfood.html',
                food_name=food_name,
                food=newFood.json(),
                login_session=login_session
            )
        elif not newFood.name or not newFood.label:
            flash("Label and DB name can not be empty.")
            return render_template(
                'editfood.html',
                food_name=food_name,
                food=newFood.json(),
                login_session=login_session
            )
        newFood.save_to_db(food_name)
        return redirect('/foods')
    else:
        food = mongo.db.foods.find_one({"name": food_name})
        return render_template(
            'editfood.html',
            food=food,
            food_name=food_name,
            login_session=login_session
        )


@app.route('/foods', methods=['POST', 'GET'])
def foodsPage():
    if 'username' not in login_session:
         return redirect('/')
    foods = list(mongo.db.foods.find())
    return render_template(
        'foods.html',
        foods=foods,
        login_session=login_session
    )


def create_figure(username):

    MID_BLUE = "#91c8ff"
    PALE_BLUE = "#add8e6"
    ANGRY_RED = "#ef5252"
    WHITE = "#FFFFFF"
    HOUR = 60 * 60 * 1000  # 1hr in miliseconds

    data = list(mongo.db.records.find({"user": username}).sort('date', 1))
    df = pd.io.json.json_normalize(data).fillna(0)
    df.set_index('date')
    df_indices = list(df)
    # TODO - dict of paired metrics to populate bar height and alpha

    # Plot Setup
    metric = Select(title='metric', value='metrics.insomnia', options=df_indices)
    factor1 = Select(title='factor1', value='misc.carb', options=df_indices)
    factor2 = Select(title='factor2', value='misc.coffee', options=df_indices)
    jitter_slider = Slider(title="Jitter", start=0, end=1, value=0, step=0.1)

    source_raw = ColumnDataSource(df.drop(['_id'], axis=1))
    source = ColumnDataSource(
        data=dict(
            date=df['date'],
            metric=source_raw.data[metric.value],
            factor1=source_raw.data[factor1.value],
            factor2=source_raw.data[factor2.value]
        )
    )

    callback = CustomJS(args=dict(source=source, source_raw=source_raw), code="""
            var value = cb_obj.value;
            var title = cb_obj.title;
            source.data[title] = source_raw.data[value];
            source.change.emit();
        """)

    metric.callback=callback
    factor1.callback=callback
    factor2.callback=callback

    p_timeline = figure(x_axis_type="datetime", y_axis_label='Variable', plot_height=300,
                plot_width=1000, tools='pan,box_zoom,reset', )
    p_factor1 = figure(x_axis_type="datetime", x_range=p_timeline.x_range, plot_height=100, plot_width=1000,
                tools='pan,box_zoom,hover,reset')
    p_factor2 = figure(x_axis_type="datetime", x_range=p_timeline.x_range, plot_height=100, plot_width=1000,
                       tools='pan,box_zoom,hover,reset')
    pv = figure(toolbar_location=None, plot_width=200, plot_height=p_timeline.plot_height,
                y_range=p_timeline.y_range, min_border=10, y_axis_location="right")
    p3 = figure(plot_height=400, plot_width=400, tools='pan,box_zoom,hover,reset')


    # Timeline
    p_timeline.vbar(x=df['date'], top=df['metrics.sleep_hours'], alpha=(df['metrics.sleep_quality']-2)/10,
                    color=PALE_BLUE, width=20 * HOUR)
    p_timeline.vbar(x='date', top='metric', alpha=0.8, color=ANGRY_RED, source=source, width=20 * HOUR)

    inc = df['metrics.afternoon'] >= df['metrics.morning']
    dec = df['metrics.morning'] > df['metrics.afternoon']
    p_timeline.line(df['date'], df[['metrics.morning', 'metrics.afternoon']].mean(axis=1), line_width=6,
                    color=PALE_BLUE)
    p_timeline.segment(df.date[inc], df['metrics.morning'][inc], df.date[inc], df['metrics.afternoon'][inc],
                       color=WHITE, line_width=4, line_cap='square')
    p_timeline.segment(df.date[dec], df['metrics.morning'][dec], df.date[dec], df['metrics.afternoon'][dec],
                       color=ANGRY_RED, line_width=4, line_cap='square')


    # Histogram - metrics
    # TODO - reflect selected metric; reflect values selected on scatter plot
    vhist, vedges = np.histogram(df['metrics.sleep_quality'].fillna(0), bins=10)
    pv.ygrid.grid_line_color = None
    pv.quad(left=0, bottom=vedges[:-1]+0.05, top=vedges[1:]-0.05, right=vhist, color=PALE_BLUE)


    # Factor plots
    p_factor1.vbar(x='date', top='factor1', color=WHITE, source=source, alpha=1, width=20*HOUR)
    p_factor2.vbar(x='date', top='factor2', color=MID_BLUE, source=source, alpha=1, width=20*HOUR)


    # Scatter plot
    p3.circle(x=jitter('metric', width=0.5), y='factor1', color=WHITE, size=8, alpha=0.5, source=source)
    p3.circle(x=jitter('metric', width=0.5), y='factor2', color=MID_BLUE, size=8, alpha=0.5, source=source)
    p3.xaxis.axis_label = 'Selected Metric'
    p3.yaxis.axis_label = 'Factor1 (white), Factor2 (blue)'


    controls = widgetbox([metric, factor1, factor2, jitter_slider], width=200)
    main_row = row(p_timeline, pv)
    bottom_row = row(controls, Spacer(width=150, height=0), p3)
    layout = column(main_row, p_factor1, p_factor2, bottom_row)

    # Add theme to document
    theme_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'theme.yaml')
    theme = Theme(theme_path)
    doc = curdoc()
    doc.theme = theme

    return layout


if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)






