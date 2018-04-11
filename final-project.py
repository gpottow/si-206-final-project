import requests
import json
import secrets
import sqlite3
from requests_oauthlib import OAuth1Session

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
    statement2 +="type = 'table' AND name = 'cities'"

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
        values = (resturant.location,)

        #if city is not in db then add it
        if not cur.execute(statement, values).fetchone()[0]:
            statement = """ INSERT INTO cities
                            ("Name") VALUES (?)"""
            insertion = (resturant.location,)
            cur.execute(statement, insertion)


        #statement to check if source is already in db
        statement = """SELECT count(*)
                       FROM sources
                       WHERE Name = (?) """
        values = (resturant.source,)


        if not cur.execute(statement, values).fetchone()[0]:
            statement = """ INSERT INTO sources
                            ("Name") VALUES (?)"""
            insertion = (resturant.source,)
            cur.execute(statement, insertion)

        conn.commit()
        #get source id from source table
        statement = """ SELECT Id
                        FROM sources
                        WHERE Name = (?) """
        values = (resturant.source,)
        source_id = cur.execute(statement, values).fetchone()[0]

        #first check if entry is already in db
        statement = """ SELECT count(*)
                        FROM resturants
                        WHERE Name = (?)
                        AND Source = (?) """
        values = (resturant.name, source_id)

        #if resturant is not in db, add to db
        if not cur.execute(statement, values).fetchone()[0]:
            statement  = """SELECT Id
                            FROM cities
                            WHERE Name = (?) """
            values = (resturant.location,)
            city_id = cur.execute(statement, values).fetchone()[0]

            statement = """ INSERT INTO resturants
                            ("Name", "Type", "Location", "Source")
                            VALUES (?, ?, ?, ?)"""
            insertion = (resturant.name, resturant.type, city_id, source_id)

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
    params = {'query': search_text, 'type':'resturant', 'key': secrets.google_places_key}

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
        resturant_list.append(get_resturants_using_google_places(city, food_type))
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

init_db(db_name)

list = get_resturants_using_google_places("Detroit", "italian")




#here for spacing
