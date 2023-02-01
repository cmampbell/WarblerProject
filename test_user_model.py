"""User model tests."""

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


class UserModelTestCase(TestCase):
    """Test models for user."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        #User should have test data
        self.assertEqual(u.email, 'test@test.com')
        self.assertEqual(u.username, 'testuser')
        self.assertEqual(u.password, "HASHED_PASSWORD")

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

        # User __repr__ method returns correct value
        self.assertIn(str(u.id), u.__repr__())
        self.assertIn(u.username, u.__repr__())
        self.assertIn(u.email, u.__repr__())

    def test_user_follows(self):
        '''Are users able to follow each other?'''

        user1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD1"
        )

        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        user1.followers.append(user2)
        db.session.commit()

        #User1 should have one follower, user2 should have 0
        self.assertEqual(len(user1.followers), 1)
        self.assertEqual(len(user2.followers), 0)

        #User1 should be following 0 users, user2 should be following 1
        self.assertEqual(len(user1.following), 0)
        self.assertEqual(len(user2.following), 1)

        #user2 is following user1
        self.assertTrue(user1.is_followed_by(user2))
        self.assertTrue(user2.is_following(user1))

        #user1 is not following user2
        self.assertFalse(user2.is_followed_by(user1))
        self.assertFalse(user1.is_following(user2))

    def test_user_signup(self):
        '''Does user signup properly create a new user?'''

        user1 = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url = User.image_url.default.arg
        )

        db.session.commit()

        #check that user properties equal entered info
        self.assertEqual(user1.email, 'test@test.com')
        self.assertEqual(user1.username, 'testuser')

        #check that user without image_url has default url
        self.assertEqual(user1.image_url, "/static/images/default-pic.png")

        #check that user password matches
        self.assertTrue(bcrypt.check_password_hash(user1.password, "HASHED_PASSWORD"))

        # check that the user object matches the user in our database
        self.assertEqual(user1, User.query.get(user1.id))

        # New user with username that already exists
        User.signup(
            email="test2@test.com",
            username="testuser",
            password="HASHED_PASSWORD2",
            image_url = User.image_url.default.arg
        )

        # Checks that an error is raised if a user tries to
        # signup with an existing username in the database
        self.assertRaises(IntegrityError, db.session.commit)
        db.session.rollback()

        # New user with null values in non-nullable fields
        # email
        User.signup(
            email=None,
            username="testuser2",
            password="HASHED_PASSWORD2",
            image_url = User.image_url.default.arg
        )
        self.assertRaises(IntegrityError, db.session.commit)
        db.session.rollback()

        #username
        User.signup(
            email="test3@hotmail.com",
            username=None,
            password="HASHED_PASSWORD3",
            image_url = User.image_url.default.arg
        )
        self.assertRaises(IntegrityError, db.session.commit)
        db.session.rollback()

        #password
        self.assertRaises(ValueError, User.signup,
                        email="test3@hotmail.com",
                        username='testuser4',
                        password=None,
                        image_url = User.image_url.default.arg)
        db.session.rollback()

    def test_valid_user_authenticate(self):
        '''Does user authenticate return a valid user
        if credentials are correct?'''

        user = User.signup(
            email="test@hotmail.com",
            username='testuser',
            password="HASHED_PASSWORD",
            image_url = User.image_url.default.arg
        )
        db.session.commit()

        # correct credentials return correct user
        self.assertEqual(user, User.authenticate('testuser', "HASHED_PASSWORD"))

    def test_invalid_user_authenticate(self):
        '''Does user authenticate return false
        if credentials are incorrect?'''

        User.signup(
            email="test@hotmail.com",
            username='testuser',
            password="HASHED_PASSWORD",
            image_url = User.image_url.default.arg
        )
        db.session.commit()

        # Invalid username
        self.assertFalse(User.authenticate('testuserbob', "HASHED_PASSWORD"))

        # Wrong password
        self.assertFalse(User.authenticate('testuser', "WRONG_PASSWORD"))
    
    def test_update_info(self):
        '''Does update info method update every field on the user?'''
        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        new_info = {
            'username': 'updateduser',
            'email': 'update@hotmail.com',
            'bio': 'updated bio',
            'header_image_url': 'testheader.jpg',
            'image_url': 'testimage.jpg'
        }

        user.update_info(new_info)

        self.assertEqual(user.username, 'updateduser')
        self.assertEqual(user.email, 'update@hotmail.com')
        self.assertEqual(user.bio, 'updated bio')
        self.assertEqual(user.header_image_url, 'testheader.jpg')
        self.assertEqual(user.image_url, 'testimage.jpg')