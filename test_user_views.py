"""Message View tests.
    Be sure to add all new views to test_views_without_user and test_views_with_user
"""

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

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

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
        db.session.commit()

        self.testmessage = Message(text="Test_Message_013")
        self.testmessage2 = Message(text="Test2_Message_014")
        self.testmessage3 = Message(text="Test3_Message_015")
        self.testmessage4 = Message(text="Test4_Message_016")
        db.session.commit()

        self.testuser.messages.append(self.testmessage)
        self.testuser.messages.append(self.testmessage2)
        self.testuser2.messages.append(self.testmessage3)
        self.testuser2.messages.append(self.testmessage4)
        db.session.commit()

        self.testuser.following.append(self.testuser2)
        self.testuser.likes.append(self.testmessage3)
        self.testuser2.likes.append(self.testmessage2)
        db.session.commit()

        self.user_id = self.testuser.id
        self.user2_id = self.testuser2.id

        self.msg_id = self.testmessage.id
        self.msg2_id = self.testmessage2.id
        self.msg3_id = self.testmessage3.id
        self.msg4_id = self.testmessage4.id

    def tearDown(self):
        db.session.rollback()

    def test_views_without_user(self):
        with self.client as c:

            user_id = self.user_id
            msg_id = self.testmessage.id

            def check_homepage_redirect(routes):
                for route in routes:
                    resp = c.get(route, follow_redirects=True)
                    self.assertEqual(resp.status_code, 200)
                    self.assertIn(b'<h4>New to Warbler?</h4>', resp.data)
                    return resp

            def check_routes_with_asserts(routes):
                for route, _assert in routes:

                    resp = c.get(route)
                    self.assertEqual(resp.status_code, 200)
                    self.assertIn(_assert, resp.data)
                    return resp

            # add routes that should redirect to home
            check_homepage_redirects = [
                '/',
                '/logout',
                '/users/profile'
                f'/users/{user_id}/following',
                f'/users/{user_id}/followers',
                f'/users/{user_id}/likes',
                '/users/profile',
                '/messages/new'
            ]
            check_homepage_redirect(check_homepage_redirects)

            # add routes and their expected return
            check_and_asserts = [
                ('/signup', b'>Join Warbler today.</h2>'),
                ('/login', b'>Welcome back.</h2>'),
                ('/users', b'<div class="card user-card">'),
                (f'/users/{user_id}', b'>@testuser</h4>'),
                (f'/messages/{msg_id}', b'>Test_Message_013.</p>')
            ]
            check_routes_with_asserts(check_and_asserts)

    def test_views_with_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            user_id = self.user_id
            user2_id = self.user2_id
            msg_id = self.msg_id

            def check_routes_with_asserts(routes):
                for route, _assert in routes:
                    resp = c.get(route, follow_redirects=True)
                    self.assertEqual(resp.status_code, 200)
                    self.assertIn(_assert, resp.data)
                    return resp

            # add routes and their expected return
            check_and_asserts = [
                ('/', b'<p>@testuser</p>'),
                ('/signup', b'<p>@testuser</p>'),
                ('/login', b'<p>@testuser</p>'),
                ('/logout', b'>Welcome back.</h2>'),
                ('/users', b'<div class="card user-card">'),
                ('/users/profile', b'>Edit Your Profile.</h2>'),
                (f'/users/{user_id}', b'>@testuser</h4>'),
                (f'/users/{user_id}/following', b'<p>testuser2</p>'),
                (f'/users/{user2_id}/followers', b'<p>testuser</p>'),
                (f'/users/{user_id}/likes', b'<p>"Test3_Message_015"</p>'),
                ('/messages/new', b'>Add my message!</button>'),
                (f'/messages/{msg_id}', b'>Test_Message_013.</p>')
            ]
            check_routes_with_asserts(check_and_asserts)

    def test_delete_posts(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            # check if valid user can delete a message
            resp = c.post(
                f'/messages/{self.msg_id}/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(Message.query.get(self.msg_id), None)

            # check if invalid user can delete a message
            resp = c.post(
                f'/messages/{self.msg3_id}/delete', follow_redirects=True)
            self.assertEqual(Message.query.get(
                self.msg3_id).text, "Test3_Message_015")
