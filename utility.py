import bcrypt

class Record(object):

    def __init__(self, webform, db):

        self.db = db
        self.feeding_window_open = webform['feeding_window'].split(",")[0]
        self.feeding_window_close = webform['feeding_window'].split(",")[1]
        self.metrics = {}
        self.foods = {}
        self.supplements = {}
        self.activities = {}
        if 'save_default' in webform:
            self.update_default_flag = True

        # Parse webform
        for metric in list(db.metrics.find()):
            name = metric["name"]
            value = int(webform[name])
            if value:
                self.metrics[name] = value

        for supplement in list(db.supplements.find()):
            name = supplement["name"]
            value = int(webform[name])
            if value:
                self.supplements[name] = value

        for food in list(db.foods.find()):
            name = food["name"]
            value = int(webform[name])
            if value:
                self.foods[name] = value

        for activity in list(db.activities.find()):
            name = activity["name"]
            intensity = int(webform[name + "_intensity"])
            time = int(webform[name + "_time"])
            if intensity:
                self.activities[name] = {"intensity": intensity,
                                                "time": time}


    def dataframe(self):
        print('test')

    def save_to_mongo(self, user, date):

        if hasattr(self, 'update_default_flag'):
            print('-----------------------------UPDATE')
            self.db.users.update_one(
                {'name': user},
                {'$set': {"defaults": self.json(user,date)}}
            )
        key = {'user': user, "date": date}
        self.db.records.update(key, self.json(user, date), upsert=True)  # Insert or update if exists

    def json(self, user, date):
        return {
            "user" : user,
            "date" : date,
            "feeding_window_open" : self.feeding_window_open,
            "feeding_window_close" : self.feeding_window_close,
            "metrics" : self.metrics,
            "foods" : self.foods,
            "supplements" : self.supplements,
            "activities" : self.activities
        }


class User(object):

    def __init__(self, webform, db):
        self.db = db
        self.name = webform['username']
        self.password = bcrypt.hashpw(webform['pass'].encode('utf-8'), bcrypt.gensalt())
        self.defaults = {
                    "feeding_window_open": 12,
                    "feeding_window_close": 18,
                    "metrics": {},
                    "foods": {},
                    "supplements": {},
                    "activities": {},
        }

    def save_to_db(self):
        existing_user = self.db.users.find_one({'name': self.name})
        if existing_user is None:
            self.db.users.insert(self.json())
            return True
        return False

    def json(self):
        return {
                "name": self.name,
                "password": self.password,
                "defaults": self.defaults
        }
