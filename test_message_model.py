"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message
from sqlalchemy.exc import DataError

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

#Check that messages are created properly
# check that message text is limited to 140 characters
# check that each message has only one user

class MessageModelTestCase(TestCase):
    '''Message model tests'''

    def setUp(self):
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

    def test_message_model(self):
        '''Does basic model work?'''

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(user)
        db.session.commit()

        message = Message(
            text='This is a test message',
            user_id = user.id
        )

        db.session.add(message)
        db.session.commit()

        # check message values match expected values
        self.assertEqual(message.text, 'This is a test message')
        self.assertEqual(message.user_id, user.id)

        #check that timestamp was created
        self.assertTrue(message.timestamp)

        #check that id was created
        self.assertTrue(message.id)

    def test_message_limits(self):
        '''Are messages limited by the constraints we set?'''

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(user)
        db.session.commit()

        message = Message(
                text='This is a test message. We are going to make it longer than the character limit of our message. The rest will be gibberish: jfkdsoapufhjweiofnjiadlovheriaohfnjweqifohe8i9waq7r832ic hfjidosaf6g4b39qo crhu 34i9qp74tr839b qpryhuei acghrufeiag',
                user_id = user.id
            )
        
        db.session.add(message)

        # String longer than 140 character will raise an error
        self.assertRaises(DataError, db.session.commit)
        db.session.rollback()