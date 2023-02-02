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

from app import app, add_user_to_g, do_logout

app.config['WTF_CSRF_ENABLED']=False
app.config['TESTING'] = True

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

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

        users = [User.signup(username=f'testuser{num}', email=f'test{num}@hotmail.com', password='testacct', image_url='image.jpg')for num in range(5)]

        main_user = User.signup(username='testuser', email='test@hotmail.com', password='testacct', image_url='image.jpg')

        #for user in users, append to user.following
        for follower in users:
            main_user.followers.append(follower)

        #main_user follows one other user
        main_user.following.append(users[1])

        #generate messages for main_user
        main_user.messages = [Message(text=f'test message {num}', user_id = main_user.id) for num in range(5)]
        
        db.session.commit()

        self.user=main_user
    
    def tearDown(self):
        db.session.rollback()

    def test_do_logout(self):
        '''Does logout route log out user from session?'''

        with self.client as client: 
            client.post('/login', data={'username': 'testuser', 'password': 'testacct'})   

            #check that there is a user in the session
            self.assertIsNotNone(session.get('curr_user'))
            
            #make request to logout
            resp = client.get('/logout')

            # print(resp.data)
            #check resp status code is redirect
            self.assertEqual(resp.status_code, 302)

            #check that current user removed from session
            self.assertIsNone(session.get('curr_user'))

    def test_list_users(self):
        '''Does list users route return a page with a list of users'''
        with self.client:
            self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            resp = self.client.get('/users')
            html = resp.get_data(as_text=True)

            #check that correct status code was sent
            self.assertEqual(resp.status_code, 200)

            #check that user cards are apperaing
            self.assertIn('<div class="card user-card">', html)

            #check that unfollow button appears on followed user
            self.assertIn(f'<form method="POST" action="/users/stop-following/{self.user.following[0].id}">', html)

            #check that follow button appears on unfollowed user
            self.assertIn(f'<form method="POST" action="/users/follow/{self.user.followers[2].id}">', html)

    def test_list_users_with_search(self):
        '''Does list users route return a page with correct user after search'''
        with self.client:
            self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            resp = self.client.get('/users?q=1')
            html = resp.get_data(as_text=True)

            #check that correct status code was sent
            self.assertEqual(resp.status_code, 200)

            #check that user cards are apperaing
            self.assertIn('<div class="card user-card">', html)

            #check that unfollow button appears on followed user
            self.assertIn(f'<form method="POST" action="/users/stop-following/{self.user.following[0].id}">', html)

            # #check that follow button appears on unfollowed user
            self.assertNotIn(f'<form method="POST" action="/users/follow/{self.user.followers[2].id}">', html)

    def test_users_show(self):
        '''Does the user profile page show everything from our user?'''
        with self.client:
            self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            resp = self.client.get(f'/users/{self.user.id}')
            html = resp.get_data(as_text=True)

            #check for correct status code
            self.assertEqual(resp.status_code, 200)

            #check that header image shows
            self.assertIn(f'<img class="img-fluid" src="{self.user.header_image_url}"', html)

            #check that html shows users messages
            self.assertIn(f'<a href="/messages/{ self.user.messages[0].id }" class="message-link"></a>', html)

            #check that html has correct users message text
            self.assertIn(f'<p>{self.user.messages[0].text}</p>', html)

    def test_user_show_following(self):
        '''Does the server show the users the accounts they follow?'''
        with self.client:
            self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            resp = self.client.get(f'/users/{session["curr_user"]}/following')
            html = resp.get_data(as_text=True)

            #check for correct status code
            self.assertEqual(resp.status_code, 200)

            #check that users following displays
            self.assertIn(f'<a href="/users/{self.user.following[0].id}" class="card-link">', html)

            #check that the unfollow button appears
            self.assertIn(f'<form method="POST" action="/users/stop-following/{self.user.following[0].id}">', html)

    def test_anon_show_following(self):
        '''Does the show following work when there is no logged in user?'''
        with self.client:

            resp = self.client.get(f'/users/{self.user.id}/following')

            #check if we get a redirect
            self.assertEqual(resp.status_code, 302)

            #check the location of the redirect
            self.assertEqual(resp.location, 'http://localhost/')

    def test_user_followers(self):
        '''Does the server show users their followers?'''
        with self.client:
            self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            resp = self.client.get(f'/users/{session["curr_user"]}/followers')
            html = resp.get_data(as_text=True)

            #check for correct status code
            self.assertEqual(resp.status_code, 200)

            #check that users following displays
            self.assertIn(f'<a href="/users/{self.user.followers[0].id}" class="card-link">', html)

            #check that the unfollow button appears
            self.assertIn(f'<form method="POST" action="/users/stop-following/{self.user.following[0].id}">', html)

            #check that the follow button appears
            self.assertIn(f'<form method="POST" action="/users/follow/{self.user.followers[3].id}">', html)

    def test_anon_user_followers(self):
        '''Does the show followers work when there is no logged in user?'''
        with self.client:

            resp = self.client.get(f'/users/{self.user.id}/followers')

            #check if we get a redirect
            self.assertEqual(resp.status_code, 302)

            #check the location of the redirect
            self.assertEqual(resp.location, 'http://localhost/')

    def test_add_follow(self):
        with self.client:
            self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            user_to_follow = User.query.filter(User != self.user, User not in self.user.following).first()

            resp = self.client.post(f'/users/follow/{user_to_follow.id}')

            #check for redirect
            self.assertEqual(resp.status_code, 302)

            #check the location of the redirect
            self.assertEqual(resp.location, f'http://localhost/users/{g.user.id}/following')

            #check that user following increased
            self.assertEqual(len(self.user.following), 2)

            #check that the user to follow is in the users following list
            self.assertIn(user_to_follow, self.user.following)

    def test_anon_add_follow(self):
        with self.client:

            resp = self.client.post(f'/users/follow/3')

            #check if we get a redirect
            self.assertEqual(resp.status_code, 302)

            #check the location of the redirect
            self.assertEqual(resp.location, 'http://localhost/')

    def test_stop_following(self):
         with self.client:
            self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            resp = self.client.post(f'/users/stop-following/{self.user.following[0].id}')

            #check for redirect
            self.assertEqual(resp.status_code, 302)

            #check the location of the redirect
            self.assertEqual(resp.location, f'http://localhost/users/{g.user.id}/following')

            #check that user following increased
            self.assertEqual(len(self.user.following), 0)

    def test_anon_stop_following(self):
        with self.client:

            resp = self.client.post(f'/users/stop-following/3')

            #check if we get a redirect
            self.assertEqual(resp.status_code, 302)

            #check the location of the redirect
            self.assertEqual(resp.location, 'http://localhost/')

    def test_edit_profile_get(self):
        with self.client:
            self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            resp = self.client.get('/users/profile')
            html = resp.get_data(as_text=True)

            #check that we get an ok status code
            self.assertEqual(resp.status_code, 200)

            #check that we get the correct html
            self.assertIn('<form method="POST" id="user_form">', html)

            #check that the html contains fields
            self.assertIn('id="username" name="username"', html)

            #check that the form fields are auto populated
            self.assertIn(self.user.username, html)

    def test_anon_edit_profile_get(self):
        with self.client:

            resp = self.client.get('/users/profile')

            #check if we get a redirect
            self.assertEqual(resp.status_code, 302)

            #check the location of the redirect
            self.assertEqual(resp.location, 'http://localhost/')
        
    def test_edit_profile_post(self):
        with self.client:
            self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            data = {'username': 'new_username', 'password': 'testacct', 'bio': 'test user bio', 'image_url': 'image.jpg', 'header_image_url': 'header.jpg'}
            resp = self.client.post('/users/profile', data=data)
            html = resp.get_data(as_text=True)

            #check that we get redirect status code
            self.assertEqual(resp.status_code, 302)

            #check that the redirect sends users to profile
            self.assertEqual(resp.location, f'http://localhost/users/{self.user.id}')

            #check that user info was updated to new info
            self.assertEqual(self.user.username, data['username'])
            self.assertEqual(self.user.bio, data['bio'])

    def test_anon_edit_profile_post(self):
        with self.client:

            resp = self.client.post('/users/profile')

            #check if we get a redirect
            self.assertEqual(resp.status_code, 302)

            #check the location of the redirect
            self.assertEqual(resp.location, 'http://localhost/')

    def test_delete_user(self):
        with self.client:
            self.client.post('/login', data={'username': 'testuser', 'password': 'testacct'})

            resp = self.client.post('/users/delete')

            #check that we get redirect status code
            self.assertEqual(resp.status_code, 302)

            #check that we get redirected to sign up
            self.assertEqual(resp.location, 'http://localhost/signup')

            #check that user is remove from session cookies
            self.assertIsNone(session.get('curr_user'))

            #check to see that user is deleted from database
            self.assertIsNone(User.query.first(self.user.id))



    