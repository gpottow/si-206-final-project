import requests
import json
import secrets
from requests_oauthlib import OAuth1Session

##on startup open cache
cache_file_name = 'cache.json'
try:
    cache_file = open(cache_file_name, 'r')
    cache_contents = cache_file.read()
    cache_diction = json.loads(cache_contents)
    cache_file.close()

except:
    cache_diction = {}


class resturant:
    def __init__(self,
                 name=None,
                 type=None,
                 location=None,
                 yelp_rating=None,
                 open_table_rating=None,
                 google_rating=None):
        self.name = name
        self.type = type
        self.location = location
        self.yelp_rating = yelp_rating
        self.open_table_rating = open_table_rating
        self.google_rating = google_rating

    def read_from_yelp_dict(self, yelp_dict):
        self.name = yelp_dict['name']
        self.yelp_rating = yelp_dict['rating']
        self.location = yelp_dict['location']['city']
        try:
            self.type = yelp_dict['categories'][1]['title']
        except:
            pass

    def __str__(self):
        statement = str(self.name) + str(self.type) + str(self.location) + str(self.yelp_rating)
        statement += str(self.open_table_rating) + str(self.google_rating)
        return statement


def get_resturants_from_yelp(city, food_type):
    base_url = 'https://api.yelp.com/v3/businesses/search'
    header = headers = {'Authorization': 'bearer %s' % secrets.yelp_api_key}

    params = {'categories':food_type, 'location':city}
    resturant_search = requests.get(base_url, params=params, headers=header)
    resturant_search_results = json.loads(resturant_search.text)

    result_list = resturant_search_results['businesses']

    print(json.dumps(result_list[0], indent=4))
    print(result_list[0]['categories'][1]['title'])

    result_obj_list = []
    for result in result_list:
        r = resturant()
        r.read_from_yelp_dict(result)
        result_obj_list.append(r)

    return result_obj_list


list = get_resturants_from_yelp("New York City", "Mexican")
print(list[0])













#here for spacing
