import requests
import json
import secrets
import sqlite3
from requests_oauthlib import OAuth1Session
import plotly.plotly as py
import plotly.graph_objs as go

db_name = 'resturants.db'

##on startup open cache
cache_file_name = 'cache.json'
try:
    cache_file = open(cache_file_name, 'r')
    cache_contents = cache_file.read()
    cache_dict = json.loads(cache_contents)
    cache_file.close()

except:
    cache_dict = {}


class resturant:
    def __init__(self,
                 name=None,
                 type=None,
                 location=None,
                 rating=None,
                 source=None):
        self.name = name
        self.type = type
        self.location = location
        self.rating = rating
        self.source = source

    def read_from_yelp_dict(self, yelp_dict):
        self.name = yelp_dict['name']
        self.rating = yelp_dict['rating']
        self.location = yelp_dict['location']['city']
        self.source = 'yelp'
        try:
            self.type = yelp_dict['categories'][1]['title']
        except:
            pass

    def read_from_google_dict(self, google_dict):
        self.name = google_dict['name']
        self.rating = google_dict['rating']
        self.source = 'google'

    def read_from_cache_dict(self, cache_dict):
        self.name = cache_dict['name']
        self.type = cache_dict['type']
        self.rating = cache_dict['rating']
        self.location = cache_dict['location']
        self.source = cache_dict['source']

    def write_to_cache_dict(self):
        cache_dict = {}
        cache_dict['name'] = self.name
        cache_dict['type'] = self.type
        cache_dict['rating'] = self.rating
        cache_dict['location'] = self.location
        cache_dict['source'] = self.source
        return cache_dict

    def __str__(self):
        statement = str(self.name) + " " + str(self.type) + " " + str(
            self.location) + " " + str(self.rating)
        statement += " " + str(self.source)
        return statement


#run at the beggining of the program to setup the DB
def init_db(db_name):
    try:
        conn = sqlite3.connect(db_name)
    except:
        print("error occurred")

    cur = conn.cursor()

    statement = "SELECT count(*) FROM sqlite_master WHERE "
    statement += "type = 'table' AND name = 'resturants'"

    statement2 = "SELECT count(*) FROM sqlite_master WHERE "
    statement2 += "type = 'table' AND name = 'cities'"

    statement3 = "SELECT count(*) FROM sqlite_master WHERE "
    statement3 += "type = 'table' AND name = 'sources'"

    if not cur.execute(statement3).fetchone()[0]:
        create_sources = '''CREATE TABLE 'sources'(
                            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                            'Name' TEXT) '''

        cur.execute(create_sources)
        conn.commit()

    if not cur.execute(statement2).fetchone()[0]:
        create_cities = """CREATE TABLE 'cities'(
                           'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                           'Name' TEXT) """

        cur.execute(create_cities)
        conn.commit()

    if not cur.execute(statement).fetchone()[0]:
        create_resturants = """ CREATE TABLE 'resturants'(
                                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                                'Name' TEXT,
                                'Type' TEXT,
                                'Rating' FLOAT,
                                'Location' INTEGER,
                                'Source' INTEGER) """
        cur.execute(create_resturants)
        conn.commit()

    conn.close()


#writes resturants to db
#can only be run if bars and cities are fully populated
#params: list of resturant objects
def insert_resturants_to_db(resturant_list):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    for resturant in resturant_list:

        #statement to check if city is already in db
        statement = """SELECT count(*)
                       FROM cities
                       WHERE Name = (?) """
        values = (resturant.location, )

        #if city is not in db then add it
        if not cur.execute(statement, values).fetchone()[0]:
            statement = """ INSERT INTO cities
                            ("Name") VALUES (?)"""
            insertion = (resturant.location, )
            cur.execute(statement, insertion)

        #statement to check if source is already in db
        statement = """SELECT count(*)
                       FROM sources
                       WHERE Name = (?) """
        values = (resturant.source, )

        if not cur.execute(statement, values).fetchone()[0]:
            statement = """ INSERT INTO sources
                            ("Name") VALUES (?)"""
            insertion = (resturant.source, )
            cur.execute(statement, insertion)

        conn.commit()
        #get source id from source table
        statement = """ SELECT Id
                        FROM sources
                        WHERE Name = (?) """
        values = (resturant.source, )
        source_id = cur.execute(statement, values).fetchone()[0]

        #first check if entry is already in db
        statement = """ SELECT count(*)
                        FROM resturants
                        WHERE Name = (?)
                        AND Source = (?) """
        values = (resturant.name, source_id)

        #if resturant is not in db, add to db
        if not cur.execute(statement, values).fetchone()[0]:
            statement = """SELECT Id
                            FROM cities
                            WHERE Name = (?) """
            values = (resturant.location, )
            city_id = cur.execute(statement, values).fetchone()[0]

            statement = """ INSERT INTO resturants
                            ("Name", "Type", "Rating", "Location", "Source")
                            VALUES (?, ?, ?, ?, ?)"""
            insertion = (resturant.name, resturant.type, resturant.rating,
                         city_id, source_id)

            cur.execute(statement, insertion)

    conn.commit()
    conn.close()


#todo: impliment way of handling unsupported cateogries
def get_resturants_from_yelp(city, food_type):
    base_url = 'https://api.yelp.com/v3/businesses/search'
    header = headers = {'Authorization': 'bearer %s' % secrets.yelp_api_key}

    params = {'categories': food_type.lower(), 'location': city, 'limit': '50'}
    resturant_search = requests.get(base_url, params=params, headers=header)
    resturant_search_results = json.loads(resturant_search.text)

    result_list = resturant_search_results['businesses']
    result_obj_list = []
    for result in result_list:
        r = resturant()
        r.read_from_yelp_dict(result)
        for category in result['categories']:
            if food_type in category.values():
                r.type = food_type
        result_obj_list.append(r)

    return result_obj_list


def get_resturants_using_google_places(city, food_type):
    search_url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
    search_text = city + "+" + food_type
    params = {
        'query': search_text,
        'type': 'resturant',
        'key': secrets.google_places_key
    }

    search = requests.get(search_url, params)
    result_format = json.loads(search.text)
    search_results = result_format['results']

    result_obj_list = []
    for result in search_results:
        r = resturant()
        r.read_from_google_dict(result)
        r.location = city
        r.type = food_type
        result_obj_list.append(r)

    return result_obj_list


#uses unofficial api
def get_resturants_using_open_table(city, food_type):
    base_url = 'https://opentable.herokuapp.com/api/restaurants'
    params = {
        'city': city,
    }
    pass


##todo: add open table to get new data
def get_resturants_using_cache(city, food_type):
    resturant_list = []
    unique_id = city + "_" + food_type.lower()

    if unique_id in cache_dict:
        print("Getting cached data... ")
        dict_list = cache_dict[unique_id]
        for dict in dict_list:
            r = resturant()
            r.read_from_cache_dict(dict)
            resturant_list.append(r)

    else:
        print("Getting new data... ")
        resturant_list = get_resturants_from_yelp(city, food_type.lower())
        google_list = get_resturants_using_google_places(city, food_type)
        for g in google_list:
            resturant_list.append(g)
        #todo: add Opentable
        resturant_dict_list = []
        for r in resturant_list:
            r_dict = r.write_to_cache_dict()
            resturant_dict_list.append(r_dict)

        cache_dict[unique_id] = resturant_dict_list
        dumped_json_cache = json.dumps(cache_dict)
        fw = open(cache_file_name, 'w')
        fw.write(dumped_json_cache)
        fw.close()

    return resturant_list


#get average raitngs
#returns list where first item is yelp second is google
def get_average_ratings_by_type(city, food_type):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    #initizlize city id to impossible value
    city_id = -1

    #statement to find city_id
    try:
        statement = """SELECT Id
                       FROM cities
                       WHERE Name = (?) """

        values = (city, )
        city_id = cur.execute(statement, values).fetchone()[0]

    except:
        city_id = -1

    statement = """SELECT count(*)
                   FROM resturants
                   WHERE Location = (?)
                   AND Type = (?) """
    values = (city_id, food_type)

    if not cur.execute(statement, values).fetchone()[0]:
        list = get_resturants_using_cache(city, food_type)
        insert_resturants_to_db(list)

    statement = """SELECT Id
                   FROM cities
                   WHERE Name = (?) """

    values = (city, )
    city_id = cur.execute(statement, values).fetchone()[0]

    ratings_statement = """SELECT ROUND(AVG(Rating),2)
                        FROM resturants
                        WHERE Location = (?)
                        GROUP BY Source
                        ORDER BY Source"""

    values = (city_id, )
    cur.execute(ratings_statement, values)

    average_ratings = []
    for row in cur:
        average_ratings.append(row)

    return average_ratings

def plot_average_ratings_by_type(city, food_type):
    ratings = get_average_ratings_by_type(city, food_type)
    yelp_rating = ratings[0][0]
    google_rating = ratings[1][0]
    trace1 = go.Bar(
             x = ["Yelp", "Google"],
             y = [yelp_rating, google_rating],
             name = "Average food Ratings for " + food_type + " food in " + city
    )
    data = [trace1]
    layout = go.Layout(
        title = "Average food ratings for " + food_type + " food in " + city,
        yaxis = dict(
            range=[2, 5]
        ),
        barmode='basic'
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='grouped-bar')

plot_average_ratings_by_type("Detroit", "italian")


#here for spacing
