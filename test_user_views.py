"""User view tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from flask import g, session

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, add_user_to_g

app.config['WTF_CSRF_ENABLED']=False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()
app.app_context().push()

# For the routing and view function tests, things get a bit more complicated. 
# You should make sure that requests to all the endpoints supported in the 
# views files return valid responses. Start by testing that the response code 
# is what you expect, then do some light HTML testing to make sure the response 
# is what you expect.

class AnonViewsTestCase(TestCase):
    '''Test user view functions with anon user page.'''

    def setUp(self):
        '''Create test client, clear database.'''

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_homepage(self):
        '''Does a new/anon user see the landing page + sign up button?'''
        with self.client:
            resp = self.client.get('/')
            html = resp.get_data(as_text=True)

            #check http response from server
            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h1>What's Happening?</h1>", html)
            self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)

            #check that global object doesn't have a user saved
            self.assertEqual(g.user, None)

            #check that session does not have current user
            self.assertIsNone(session.get('curr_user'))

    def test_signup_get(self):
        '''Does the signup route provide correct html and response code?'''
        with self.client:
            resp = self.client.get('/signup')
            html = resp.get_data(as_text=True)

            #check that session does not have current user
            self.assertIsNone(session.get('curr_user'))

            #Check that server is providing correct html
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)
            self.assertEqual(resp.status_code, 200)

    def test_signup_post(self):

        with self.client:
            data = {'username': 'testuser', 'email': 'test@hotmail.com', 'password': 'testacct', 'image_url': 'test.jpg'}
            resp = self.client.post('/signup', data=data)

            # check that server sent redirect
            self.assertEqual(resp.status_code, 302)

            #check that session has current user now
            self.assertIsNotNone(session.get('curr_user'))

            user = User.query.get(session.get('curr_user'))

            #check that user saved in session is user that signed up
            self.assertEqual(user.username, 'testuser')
            self.assertEqual(user.email, 'test@hotmail.com')

    def test_login_get(self):
        '''Does the login route provide correct html and response code?'''
        with self.client:
            resp = self.client.get('/login')
            html = resp.get_data(as_text=True)

            #check that session does not have current user
            self.assertIsNone(session.get('curr_user'))

            #Check that server is providing correct html
            self.assertIn('<button class="btn btn-primary btn-block btn-lg">Log in</button>', html)
            self.assertEqual(resp.status_code, 200)

    def test_valid_login_post(self):
        '''Does login post route work with valid credentials?'''

        User.signup(username='testuser', email='test@hotmail.com', password='testacct', image_url='image.jpg')
        db.session.commit()

        with self.client:
            resp = self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            #check that session has current user
            self.assertIsNotNone(session.get('curr_user'))

            user = User.query.get(session.get('curr_user'))

            #check that user saved in session is user that logged in
            self.assertEqual(user.username, 'testuser')
            self.assertEqual(user.email, 'test@hotmail.com')

            #check that server is redirecting after valid login
            self.assertEqual(resp.status_code, 302)

    def test_invalid_login_post(self):
        '''Does login post route return an error with invalid credentials?'''
        User.signup(username='testuser', email='test@hotmail.com', password='testacct', image_url='image.jpg')
        db.session.commit()

        with self.client:
            resp = self.client.post('/login', data={'username': 'testuser', 'password': 'wrongpass'})
            html = resp.get_data(as_text=True)

            #check that session does not have a current user
            self.assertIsNone(session.get('curr_user'))

            #check resp status code is 200
            self.assertEqual(resp.status_code, 200)

            #check that server sends user back to login page
            self.assertIn('<button class="btn btn-primary btn-block btn-lg">Log in</button>', html)


class UserViewsTestCase(TestCase):
    '''Test user view functions with logged in user.'''

    def setUp(self):
        '''Create test client, add sample data'''

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        user = User.signup(username='testuser', email='test@hotmail.com', password='testacct', image_url='image.jpg')
        db.session.commit()

        # TODO: figure out how to get session to persist across tests, and access it 
        # with self.client:
        #     with self.client.session_transaction() as session:
        #         session['curr_user'] = user.id

        # create user
        # add that user session
        # session needs to persist

    def test_logout(self):
        with self.client:
            # with app.app_context():
            #     #check that there is a user in the session
            #     self.assertIsNotNone(session.get('curr_user'))

            #make request to logout
            resp = self.client.get('/logout')

            #check resp status code is redirect
            self.assertEqual(resp.status_code, 302)

            #check that current user removed from session
            self.assertIsNone(session.get('curr_user'))

    # def test_show_following(self):
    #     with self.client:

    #         resp = self.client.get(f'/users/{session["curr_user"]}/following')


    