"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY, g

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)

        message = Message(text='set Up test message')

        self.testuser2.messages.append(message)

        db.session.commit()

    def test_add_message_get(self):
        '''Does add message return correct html'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/messages/new')
            html = resp.get_data(as_text=True)

            #check that we get an ok status code
            self.assertEqual(resp.status_code, 200)

            #check that html includes the add message button
            self.assertIn('<button class="btn btn-outline-success btn-block">Add my message!</button>', html)

    def test_anon_add_message(self):
        '''Does an anonymous user get redirect to home page'''
        ################GET REQUEST#################
        resp = self.client.get('/messages/new')
        
        #check that we get a redirect status code
        self.assertEqual(resp.status_code, 302)

        #check that we are sent to home page
        self.assertEqual(resp.location, 'http://localhost/')

        ###############POST REQUEST#################
        resp = self.client.post("/messages/new", data={"text": "Hello"})

        #check that we get a redirect status code
        self.assertEqual(resp.status_code, 302)

        #check that we are sent to home page
        self.assertEqual(resp.location, 'http://localhost/')

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of our test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            self.assertEqual(len(self.testuser.messages), 1)
            self.assertEqual(self.testuser.messages[0].text, "Hello")

    def test_add_message_as_other_user(self):
        '''Do we prevent users from posting as other users?'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            #if g.user and current user in session become different
            g.user = self.testuser2

            resp = c.post('/messages/new', data={'text': 'Hello'})

            #a user will only ever be able to post as the user stored in session
            #check for redirect
            self.assertEqual(resp.status_code, 302)

            #check length of testuser2 messages
            self.assertEqual(len(self.testuser2.messages), 1)

            #check length of testuser messages
            self.assertEqual(len(self.testuser.messages), 1)

    def test_messages_show_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            #create a message for user
            c.post('/messages/new', data={'text': 'Hello'})
            
            #make request to get message
            resp = c.get(f'/messages/{self.testuser.messages[0].id}')
            html = resp.get_data(as_text=True)

            #check that we get an ok response code
            self.assertEqual(resp.status_code, 200)

            #check that we see the message in the html
            self.assertIn('Hello', html)

    def test_messages_destroy(self):
        '''Can a user delete their own messages?'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
        #create a message for user
        c.post('/messages/new', data={'text': 'Hello'})  

        #check that message was created
        self.assertEqual(len(self.testuser.messages), 1)

        message_id = self.testuser.messages[0].id

        #make request to delete message
        resp = c.post(f'/messages/{self.testuser.messages[0].id}/delete')

        #check that we get a redirect status code
        self.assertEqual(resp.status_code, 302)

        #check that the message was deleted
        self.assertEqual(len(self.testuser.messages), 0)
        self.assertIsNone(Message.query.get(message_id))

    def test_messages_destroy_diff_user(self):
        '''Can a user delete a message that is not their own?'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        #make request to delete user 2 message
        resp = c.post(f'/messages/{self.testuser2.messages[0].id}/delete')

        #check that we get redirect status code
        self.assertEqual(resp.status_code, 302)

        #check that message was not deleted
        self.assertEqual(len(self.testuser2.messages), 1)
        self.assertEqual(len(self.testuser.messages), 0)

    def test_messages_destroy_anon(self):
        '''Can an anonymous user delete any messages?'''
        with self.client as c:
            #make request
            resp = c.post(f'/messages/{self.testuser2.messages[0].id}/delete')

            #check that we get redirect status code
            self.assertEqual(resp.status_code, 302)

            #check that message was not deleted
            self.assertEqual(len(self.testuser2.messages), 1)


