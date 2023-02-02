"""User view tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, bcrypt, User, Message, Follows
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# For the routing and view function tests, things get a bit more complicated. 
# You should make sure that requests to all the endpoints supported in the 
# views files return valid responses. Start by testing that the response code 
# is what you expect, then do some light HTML testing to make sure the response 
# is what you expect.

class AnonViewsTestCase(TestCase):
    """Test view functions with anon user page."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_homepage(self):
        resp = self.client.get('/')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)