import unittest
import final_project
from final_project import *


class TestSources(unittest.TestCase):
    def test_yelp(self):
        results = get_resturants_from_yelp("Detroit", "italian")
        self.assertEqual(results[0].type, "italian")
        self.assertEqual(results[0].source, 'yelp')
        self.assertEqual(results[0].location, 'Detroit')
        self.assertEqual(results[0].name, "Supino Pizzeria")
        self.assertEqual(results[0].rating, 4.5)
        self.assertEqual(results[0].price, 2)

    def test_google(self):
        results = get_resturants_using_google_places("Detroit", "italian")
        self.assertEqual(results[0].type, "italian")
        self.assertEqual(results[0].source, 'google')
        self.assertEqual(results[0].location, "Detroit")
        self.assertEqual(results[0].name, "Giovanni's")
        self.assertEqual(results[0].rating, 4.7)
        self.assertEqual(results[0].price , 3)

class TestDataBase(unittest.TestCase):
    def test_resturants(self):
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()

        sql = "SELECT Name from resturants"
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Supino Pizzeria',), result_list)

        sql1 = "SELECT Name from sources"
        results1 = cur.execute(sql1)
        results_list = results.fetchall()
        self.assertEqual(len(results_list), 2)
        self.assertEqual(results_list[0][0], 'yelp')

        sql2 = "SELECT Name from cities"
        results2 = cur.execute(sql2)
        results_list = results.fetchall()
        self.assertEqual(results_list[0][0], "Detroit")

unittest.main()
