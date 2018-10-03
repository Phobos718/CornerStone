## CornerStone - A project for exploratory data analysis of personal habits and their outcomes 

As a brief summary, this is a Flask application designed to gather data of a user's habits daily and to provide a platform for analyzing it via data visualisation and more advanced methods later on to allow for seeing through more noisy data.
It's being developed predominantly for personal use as an attempt to identify the causes of certain food sensitivities and minor (although rather annoying) sleep disorders that run in my family and to maximise personal performance by eliminating them. 

Information is gathered via a survey about food and supplement intake, physical and other activities, and a set of metrics each day. 
Once enough data is gathered it can be analysed by the user (see screenshots below)

Many aspects of this project are still in a prototype phase, multiple changes in structure can be expected as I refactor the code to allow for better scalability. Net functionality is my top priority, therefore design and front end will be moving the slowest.

The live version of this project is currently being hosted on AWS. Feel free to message me for access and test credentials.

### Screenshots

1
2
3


## To-Do list (in order of priority)

- Interactive data visualisation dashboard with Bokeh (in progress)
- Ability for users to add new supplements and activities to DB like they can foods
- Ability for users to directly modify survey prefill defaults in a profile page
- Serve JSON endpoints
- Front end improvements, bugfixes, better documentation
- A minimal admin dashboard with database backup functionality
- Items frequently entered by users to show up on top of selector list on the Edit Records page
- Streamlining date selection on 'Edit Records' page via asynchronous calls
- Improved security and login

- MLP2

## Main technologies used

1. Python 3
2. MongoDB
3. Flask
4. Bokeh (for interactive data visualisation)
