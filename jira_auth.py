"""
JIRA OAuth 2.0 Authentication Module
Handles OAuth 2.0 flow for JIRA authentication
"""
import requests
import webbrowser
import urllib.parse
import json
import os
from typing import Dict, Optional
from config import Config

class JIRAAuth:
    """Handles JIRA OAuth 2.0 authentication"""
    
    def __init__(self):
        self.client_id = Config.JIRA_CLIENT_ID
        self.client_secret = Config.JIRA_CLIENT_SECRET
        self.redirect_uri = Config.JIRA_REDIRECT_URI
        self.server_url = Config.JIRA_SERVER_URL
        self.token_file = "jira_tokens.json"
        
    def get_authorization_url(self) -> str:
        """Generate the OAuth 2.0 authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'read:jira-work read:jira-user offline_access',  # Added offline_access for refresh tokens
            'state': 'jira_duplicate_detection',
            'audience': f'api.atlassian.com'
        }
        
        # Use the correct Atlassian OAuth endpoint
        auth_url = f"https://auth.atlassian.com/authorize?" + urllib.parse.urlencode(params)
        return auth_url
    
    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, str]:
        """Exchange authorization code for access token"""
        token_url = "https://auth.atlassian.com/oauth/token"
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': authorization_code
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresh the access token using refresh token"""
        token_url = "https://auth.atlassian.com/oauth/token"
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def save_tokens(self, tokens: Dict[str, str]) -> None:
        """Save tokens to file for reuse"""
        try:
            with open(self.token_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            print("✅ Tokens saved for future use")
        except Exception as e:
            print(f"⚠️  Could not save tokens: {e}")
    
    def load_tokens(self) -> Optional[Dict[str, str]]:
        """Load saved tokens from file"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
                print("✅ Loaded saved tokens")
                return tokens
        except Exception as e:
            print(f"⚠️  Could not load saved tokens: {e}")
        return None
    
    def is_token_valid(self, tokens: Dict[str, str]) -> bool:
        """Check if the access token is still valid"""
        try:
            # Test the token by making a simple API call to Atlassian Cloud API
            headers = {
                'Authorization': f'Bearer {tokens["access_token"]}',
                'Accept': 'application/json'
            }
            cloud_id = Config.JIRA_CLOUD_ID
            response = requests.get(f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself", headers=headers)
            return response.status_code == 200
        except:
            return False
    
    def get_valid_tokens(self) -> Optional[Dict[str, str]]:
        """Get valid tokens, either from file or by refreshing"""
        # Try to load saved tokens
        tokens = self.load_tokens()
        
        if tokens and self.is_token_valid(tokens):
            return tokens
        
        # If tokens are invalid or expired, try to refresh
        if tokens and 'refresh_token' in tokens:
            try:
                print("🔄 Refreshing expired tokens...")
                refreshed_tokens = self.refresh_access_token(tokens['refresh_token'])
                self.save_tokens(refreshed_tokens)
                return refreshed_tokens
            except Exception as e:
                print(f"⚠️  Could not refresh tokens: {e}")
        
        return None
    
    def authenticate_interactive(self) -> Dict[str, str]:
        """Interactive authentication flow with automatic callback handling"""
        print("Starting JIRA OAuth 2.0 authentication...")
        
        # Get authorization URL
        auth_url = self.get_authorization_url()
        print(f"Please visit this URL to authorize the application:")
        print(auth_url)
        print("\nAfter authorization, you'll be redirected to a localhost URL.")
        print("The application will automatically capture the authorization code.")
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Start local server to capture callback
        auth_code = self._capture_callback()
        
        # Exchange code for token
        tokens = self.exchange_code_for_token(auth_code)
        
        # Save tokens for future use
        self.save_tokens(tokens)
        
        print("Authentication successful!")
        return tokens
    
    def _capture_callback(self) -> str:
        """Capture the OAuth callback automatically"""
        from urllib.parse import urlparse, parse_qs
        import threading
        import time
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        # Parse the redirect URI to get host and port
        parsed_uri = urlparse(self.redirect_uri)
        host = parsed_uri.hostname or 'localhost'
        port = parsed_uri.port or 8080
        
        # Shared variable to store the auth code
        auth_code = [None]
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse the query parameters
                query_params = parse_qs(urlparse(self.path).query)
                
                if 'code' in query_params:
                    auth_code[0] = query_params['code'][0]
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'''
                    <html>
                    <body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                    </body>
                    </html>
                    ''')
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'''
                    <html>
                    <body>
                    <h1>Authentication Error</h1>
                    <p>No authorization code received.</p>
                    </body>
                    </html>
                    ''')
            
            def log_message(self, format, *args):
                # Suppress default logging
                pass
        
        # Start the server
        server = HTTPServer((host, port), CallbackHandler)
        
        print(f"Waiting for OAuth callback on {host}:{port}...")
        print("Please complete the authorization in your browser.")
        
        # Run server in a separate thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for the callback
        timeout = 300  # 5 minutes timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if auth_code[0]:
                server.shutdown()
                return auth_code[0]
            time.sleep(0.1)
        
        server.shutdown()
        raise TimeoutError("Authentication timeout - no callback received within 5 minutes")
