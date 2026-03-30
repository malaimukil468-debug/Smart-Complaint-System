import unittest
from unittest.mock import patch
import app

class FlaskAppTests(unittest.TestCase):
    def setUp(self):
        # Set up a test client
        self.app = app.app.test_client()
        self.app.testing = True

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    @patch('app.get_db_connection')
    def test_register(self, mock_get_db_connection):
        # Mock the db connection to not actually write to database.db
        mock_conn = mock_get_db_connection.return_value
        
        response = self.app.post('/register', data=dict(
            name='Test User',
            email='test@example.com',
            password='password123'
        ), follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        # Check if execute was called to insert user
        mock_conn.execute.assert_called_once()
        self.assertTrue('INSERT INTO users' in mock_conn.execute.call_args[0][0])
        
    @patch('app.get_db_connection')
    def test_login_success(self, mock_get_db_connection):
        mock_conn = mock_get_db_connection.return_value
        # Mock the fetchone to return a user
        mock_conn.execute.return_value.fetchone.return_value = {'user_id': 1, 'email': 'test@example.com', 'is_approved': 1}
        
        response = self.app.post('/login', data=dict(
            email='test@example.com',
            password='password123'
        ))
        
        self.assertEqual(response.status_code, 302) # Redirects to /select_technician
        self.assertEqual(response.location, '/select_technician')

    @patch('app.get_db_connection')
    def test_login_unapproved(self, mock_get_db_connection):
        mock_conn = mock_get_db_connection.return_value
        mock_conn.execute.return_value.fetchone.return_value = {'user_id': 1, 'email': 'unapproved@example.com', 'is_approved': 0}
        
        response = self.app.post('/login', data=dict(
            email='unapproved@example.com',
            password='password123'
        ))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account pending approval by admin', response.data)

    @patch('app.get_db_connection')
    def test_login_failure(self, mock_get_db_connection):
        mock_conn = mock_get_db_connection.return_value
        # Mock the fetchone to return None
        mock_conn.execute.return_value.fetchone.return_value = None
        
        response = self.app.post('/login', data=dict(
            email='wrong@example.com',
            password='wrongpassword'
        ))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid Login', response.data)

    @patch('app.get_db_connection')
    def test_admin_login_success(self, mock_get_db_connection):
        mock_conn = mock_get_db_connection.return_value
        mock_conn.execute.return_value.fetchone.return_value = {'user_id': 99, 'role': 'admin'}
        
        response = self.app.post('/admin_login', data=dict(
            username='admin@example.com',
            password='adminpassword'
        ))
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/admin_dashboard')

    @patch('app.get_db_connection')
    def test_technician_login_success(self, mock_get_db_connection):
        mock_conn = mock_get_db_connection.return_value
        mock_conn.execute.return_value.fetchone.return_value = {'technician_id': 2}
        
        response = self.app.post('/technician_login', data=dict(
            email='tech@example.com',
            password='techpassword'
        ))
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/technician_dashboard')

if __name__ == '__main__':
    unittest.main()
