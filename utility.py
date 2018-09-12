from pymongo import Connection
from bson import ObjectId
from itertools import imap


class Record(object):

    def __init__(self, webform, db):

        self.db = db
        self.user = ''
        self.date = "today"               # TODO
        self.metrics = {}
        self.food = {}
        self.supplement = {}
        self.activity = {}

        for supplement in db.supplements:
            name = supplement["name"]
            value = int(webform[name])
            if value:
                self.supplement[name] = value

        for food in db.foods:
            name = food["name"]
            value = int(webform[name])
            if value:
                self.food[name] = value

        for activity in db.activities:
            name = activity["name"]
            intensity = int(webform[name + "_intensity"])
            time = int(webform[name + "_time"])
            if intensity:
                self.activity[name] = {"intensity": intensity,
                                                "time": time}


    def parse_webform(self, webform, login_session):
        form_input = {
            "user": login_session['email'],
            "date": date,
            "morning": int(webform['morning']),
            "afternoon": int(webform['afternoon']),
            "inflammation": int(webform['inflammation']),
            "sleep_h": int(webform['sleep_h']),
            "sleep_q": int(webform['sleep_q']),
            "nutrition": {
                "calories": int(webform['calories']),
                "feeding_window": [int(x) for x in webform['feeding_window'].split(",")],
                "food": {},
                "supplements": {
                    "coffee": int(webform['coffee'])
                }
            },
            "activity": {}
        }


    def to_dataframe(self):
        pass


    def save_to_mongo(self, user, date):

        self.db.insert(collection='records',
                         data=self.json(user, date))


    def json(self, user, date):
        return {
            "user" : user,
            "date" : date
            "metrics" : self.metrics,
            "food" : self.food,
            "supplement" : self.supplement,
            "activity" : self.activity
        }


class Model(dict):
    """
    A simple model that wraps mongodb document
    """
    __getattr__ = dict.get
    __delattr__ = dict.__delitem__
    __setattr__ = dict.__setitem__

    def save(self):
        if not self._id:
            self.collection.insert(self)
        else:
            self.collection.update(
                { "_id": ObjectId(self._id) }, self)

    def reload(self):
        if self._id:
            self.update(self.collection\
                    .find_one({"_id": ObjectId(self._id)}))

    def remove(self):
        if self._id:
            self.collection.remove({"_id": ObjectId(self._id)})
            self.clear()


# ------------------------------
# Here is the example model
# ------------------------------

class Document(Model):
    collection = Connection()["test_database"]["test_collections"]

    @property
    def keywords(self):
        return self.title.split()


# ------------------------------
# Mapping documents to the model
# ------------------------------

documents = imap(Document, Document.collection.find())

# that's all

for document in documents:
    print document.title, document.keywords


# ------------------------------
# Creating new document
# ------------------------------

document = Document({
    "title": "test document",
    "slug": "test-document"
})

print document._id # none
document.save()
print document._id # "50d3cb0068c0064a21e76be4"

# -------------------------
# Getting a single document
# -------------------------

document = Document({
    "_id": "50d3cb0068c0064a21e76be4"
})

print document.title # None
document.reload()
print document.title # "test document"

# -----------------
# Updating document
# -----------------

document.title = "test document 2"
document.save()
print document.title # "test document 2"
document.reload()
print document.title # "test document 2"

# -----------------
# Removing document
# -----------------

document.remove()
print document # {}




form_input = {
            "user": login_session['email'],
            "date": date,
            "morning": int(request.form['morning']),
            "afternoon": int(request.form['afternoon']),
            "inflammation" : int(request.form['inflammation']),
            "sleep_h": int(request.form['sleep_h']),
            "sleep_q": int(request.form['sleep_q']),
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