




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