from unittest import TestCase
from main import *


class Test(TestCase):
    def test_azimuth(self):
        self.assertEqual(azimuth([100, 100], [100, 200]), 0)  # North
        self.assertEqual(azimuth([100, 100], [200, 100]), 1600)  # East
        self.assertEqual(azimuth([100, 100], [100, 0]), 3200)  # South
        self.assertEqual(azimuth([100, 100], [0, 100]), 4800)  # West

        self.assertEqual(azimuth([100, 100], [200, 200]), 800)  # North-east
        self.assertEqual(azimuth([100, 100], [150, 50]), 2400)  # South-east
        self.assertEqual(azimuth([100, 100], [50, 50]), 4000)  # South-west
        self.assertEqual(azimuth([100, 100], [50, 150]), 5600)  # North-west

        self.assertEqual(azimuth([100, 100], [100, 100]), 0)  # Same point
