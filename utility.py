import bcrypt

class Record(object):

    def __init__(self, webform, db):

        self.db = db
        self.metrics = {}
        self.foods = {}
        self.supplements = {}
        self.activities = {}
        self.misc = {
            "feeding_window_open": webform['feeding_window'].split(",")[0],
            "feeding_window_close": webform['feeding_window'].split(",")[1],
            "coffee": webform["coffee"]
        }

        if 'save_default' in webform:
            self.update_default_flag = True

        for metric in list(db.metrics.find()):
            name = metric["name"]
            value = float(webform[name])
            if value:
                self.metrics[name] = value

        for supplement in list(db.supplements.find()):
            name = supplement["name"]
            value = float(webform[name])
            if value:
                self.supplements[name] = value

        for food in list(db.foods.find()):
            name = food["name"]
            value = float(webform[name])
            if value:
                self.foods[name] = value

        for activity in list(db.activities.find()):
            name = activity["name"]
            intensity = float(webform[name + "_intensity"])
            time = float(webform[name + "_time"])
            if intensity:
                self.activities[name] = {
                    "intensity": intensity,
                    "time": time
                }

        self.calculate_macros()
        print(self.misc['protein'])

        if 'calories_manual' in webform:
            self.misc["calories"] = webform["calories"]
        else:
            self.misc["calories"] = int(
                self.misc['protein']*4 +
                self.misc['fat']*9 +
                self.misc['carb']*4
            )


    def dataframe(self):
        print('test')

    def calculate_macros(self):

        protein = 0
        fat = 0
        carb = 0
        fibre = 0
        for food_name, food_grams in self.foods.items():
            food_info = self.db.foods.find_one({"name": food_name})
            protein = protein + food_info['protein'] * food_grams / 100
            fat = fat + food_info['fat'] * food_grams / 100
            carb = carb + food_info['carb'] * food_grams / 100
            fibre = fibre + food_info['fibre'] * food_grams / 100

        self.misc['protein'] = protein
        print(protein)
        self.misc['fat'] = fat
        self.misc['carb'] = carb   # total carb including fibre
        self.misc['fibre'] = fibre


    def save_to_mongo(self, user, date):

        if hasattr(self, 'update_default_flag'):
            self.db.users.update_one(
                {'name': user},
                {'$set': {"defaults": self.json(user,date)}}
            )
        key = {'user': user, "date": date}
        self.db.records.update(key, self.json(user, date), upsert=True)  # Insert or update if exists

    def json(self, user, date):
        return {
            "user": user,
            "date": date,
            "misc": self.misc,
            "metrics": self.metrics,
            "foods": self.foods,
            "supplements": self.supplements,
            "activities": self.activities
        }


class User(object):

    def __init__(self, webform, db):
        self.db = db
        self.name = webform['username']
        self.password = bcrypt.hashpw(webform['pass'].encode('utf-8'), bcrypt.gensalt())
        self.defaults = {
                    "misc": {
                        "feeding_window_open": 12,
                        "feeding_window_close": 18,
                    },
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

class Food(object):

    def __init__(self, webform, db):
        self.db = db
        self.label = webform['label']
        self.name = webform['name']
        self.protein = int(webform['protein'])
        self.fat = int(webform['fat'])
        self.carb = int(webform['carb'])
        self.fibre = int(webform['fibre'])
        self.standard_portion = float(webform['standard_portion'])
        self.p_price = float(webform['p_price'])
        self.max_portions = int(webform['max_portions'])

    def json(self):
        return {
            "label": self.label,
            "name": self.name,
            "protein": self.protein,
            "fat": self.fat,
            "carb": self.carb,
            "fibre": self.fibre,
            "standard_portion": self.standard_portion,
            "p_price": self.p_price,
            "max_portions": self.max_portions
        }

    def save_to_db(self, food_name):

        key = {'name': food_name}
        self.db.foods.update(key, self.json(), upsert=True)


class Supplement(object):
    pass
