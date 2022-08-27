"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from sqlalchemy.exc import IntegrityError
import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test users model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        users = [
            User.signup(email="test@test.com", username="testuser",
                        password="HASHED_PASSWORD", image_url="https://randomuser.me/api/portraits/men/15.jpg"),
            User.signup(email="test2@test.com", username="testuser2",
                        password="HASHED_PASSWORD", image_url="https://randomuser.me/api/portraits/men/15.jpg")
        ]

        db.session.add_all(users)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        testuser = User.query.filter_by(username='testuser').first()

        # User should have no messages & no followers
        self.assertEqual(len(testuser.messages), 0)
        self.assertEqual(len(testuser.followers), 0)

    def test_user_create(self):
        """Check proper account creation inputs"""

        good_user = {
            'email': 'test10@test.com',
            'username': 'testuser10',
            'password': 'HASHED_PASSWORD',
            'image_url': 'https://randomuser.me/api/portraits/men/15.jpg'}

        repeat_user = {
            'email': 'test10@test.com',
            'username': 'testuser10',
            'password': 'HASHED_PASSWORD',
            'image_url': 'https://randomuser.me/api/portraits/men/15.jpg'}

        user1 = User.signup(**good_user)
        db.session.commit()
        self.assertIsInstance(user1, User)

        with self.assertRaises(IntegrityError):
            user2 = User.signup(**repeat_user)
            db.session.commit()

    def test_auth(self):
        """Check good and bad auth logins"""

        # good login
        testuser = User.authenticate(
            username='testuser', password='HASHED_PASSWORD')
        # bad password
        testuser2 = User.authenticate(
            username='testuser2', password='HASHeD_PASSWORD')
        # bad username
        testuser3 = User.authenticate(
            username='testuser3', password='HASHED_PASSWORD')

        self.assertIsInstance(testuser, User)
        self.assertNotIsInstance(testuser2, User)
        self.assertNotIsInstance(testuser3, User)

    def test_following(self):
        """Test adding a user to a users following"""

        user1 = User.query.filter_by(username='testuser').first()
        user2 = User.query.filter_by(username='testuser2').first()

        user1.following.append(user2)
        db.session.commit()

        self.assertIn(user2, user1.following)
        self.assertIn(user1, user2.followers)

        user1.following.remove(user2)
        db.session.commit()

        self.assertNotIn(user2, user1.following)
        self.assertNotIn(user1, user2.followers)

    def test_followers(self):
        """Test adding a user to a users followers."""

        user1 = User.query.filter_by(username='testuser').first()
        user2 = User.query.filter_by(username='testuser2').first()

        user1.followers.append(user2)
        db.session.commit()

        self.assertIn(user2, user1.followers)
        self.assertIn(user1, user2.following)

        user1.followers.remove(user2)
        db.session.commit()

        self.assertNotIn(user2, user1.followers)
        self.assertNotIn(user1, user2.following)
