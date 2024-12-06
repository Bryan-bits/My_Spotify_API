
import tkinter as tk
from interface import MainInterface
from tkinter import messagebox
import threading, queue, os, requests, spotipy
from flask import Flask, request, jsonify
from spotipy.oauth2 import SpotifyOAuth
from requests import post
from datetime import datetime
from dotenv import set_key


# CLIENT_ID = "122ec5036ce84b249e67cfe3300e0808"
# CLIENT_SECRET = "0ad7a7f6b2bb4d898b5acaa5ceb7cb85"

REDIRECT_URI = "http://localhost:5000/callback"
TOKEN_URL = "https://accounts.spotify.com/api/token"
AUTH_URL = 'https://accounts.spotify.com/authorize'
API_BASE_URL = 'https://api.spotify.com/v1'

SCOPES = (
    "user-read-private "
    "user-read-email "
    "playlist-read-private "
    "user-follow-read "
    "user-follow-modify "
    "user-library-read "
    "user-library-modify "
    "user-modify-playback-state "
    "user-read-playback-state "
)


import os
import requests
import webbrowser
import urllib.parse
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

class TokenManager:
    def __init__(self, message_queue=None):
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None
        self.sp = None
        self.message_queue = message_queue

    def get_auth_header(self):
        """Return the authorization header for API requests."""
        if not self.access_token or self.is_token_expired():
            print("Access token is missing or expired. Refreshing token.")
            self.refresh_access_token()
        
        if not self.access_token:
            return None
        
        return {'Authorization': f"Bearer {self.access_token}"}

    def is_token_expired(self):
        """Check if the token has expired based on the expiration timestamp."""
        return datetime.now().timestamp() > float(self.expires_at)

    def refresh_access_token(self):
        """Attempt to refresh the access token using the refresh token."""
        if not self.refresh_token:
            print("No refresh token available.")
            return None

        if self.is_token_expired():
            print("Access token expired. Trying to refresh.")
            req_body = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            response = requests.post(TOKEN_URL, data=req_body)
            if response.status_code == 200:
                data = response.json()
                self.set_tokens(data['access_token'], self.refresh_token, datetime.now().timestamp() + data['expires_in'])
            else:
                print(f"Failed to refresh access token: {response.text}")
                self.message_queue.put("error:Failed to refresh access token")
        else:
            print("Access token is still valid.")

    def validate_user(self, client_id, client_secret):
        """Validate user credentials by performing the OAuth flow."""
        auth_url = "https://accounts.spotify.com/api/token"
        response = requests.post(auth_url, data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        })
        return response.status_code == 200

    def start_authorization_flow(self):
        """Initiate the OAuth flow to get an authorization code."""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': SCOPES,
            'redirect_uri': REDIRECT_URI,
            'show_dialog': True
        }
        auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
        webbrowser.open(auth_url)

    def set_tokens(self, access_token, refresh_token, expires_at):
        """Set the tokens and expiration time."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.save_tokens_to_env()

    def save_tokens_to_env(self):
        """Store the tokens and expiration in environment variables."""
        os.environ["ACCESS_TOKEN"] = self.access_token
        os.environ["REFRESH_TOKEN"] = self.refresh_token
        os.environ["EXPIRES_AT"] = self.expires_at

    def get_tokens_from_env(self):
        """Retrieve tokens from environment variables."""
        self.access_token = os.getenv("ACCESS_TOKEN")
        self.refresh_token = os.getenv("REFRESH_TOKEN")
        self.expires_at = os.getenv("EXPIRES_AT")

def get_user_credentials(root, token_manager):
    """Prompt the user to enter their credentials via a pop-up."""
    credentials_window = tk.Toplevel(root)
    credentials_window.title("MySpotify Beta 1.0")
    credentials_window.geometry("300x250")
    credentials_window.grab_set()

    tk.Label(credentials_window, text="Welcome to My Spotify API", font=("Helvetica", 14), fg="blue").pack(pady=10)
    tk.Label(credentials_window, text="User ID:").pack(pady=5)
    user_id_entry = tk.Entry(credentials_window, width=30)
    user_id_entry.pack()

    tk.Label(credentials_window, text="Password:").pack(pady=5)
    password_entry = tk.Entry(credentials_window, width=30, show="*")
    password_entry.pack()

    error_label = tk.Label(credentials_window, text="", fg="red", font=("Helvetica", 10))
    error_label.pack(pady=5)

    def submit_credentials():
        token_manager.client_id = user_id_entry.get()
        token_manager.client_secret = password_entry.get()
        if not token_manager.client_id or not token_manager.client_secret:
            error_label.config(text="Both fields are required!")
        elif not token_manager.validate_user(token_manager.client_id, token_manager.client_secret):
            error_label.config(text="Invalid ID or password!")
        else:
            print(f"token_manager.client_id: {token_manager.client_id}")
            os.environ["CLIENT_ID"] = token_manager.client_id
            print(f"envi var 'CLIENT_ID': {os.getenv("CLIENT_ID")} ")
            print(f"token_manager.client_secret: {token_manager.client_secret}")
            os.environ["CLIENT_SECRET"] = token_manager.client_secret
            print(f"envi var 'CLIENT_SECRET': {os.getenv("CLIENT_SECRET")} ")
            token_manager.start_authorization_flow()
            credentials_window.destroy()  # Close on success

    tk.Button(credentials_window, text="Submit", command=submit_credentials).pack(pady=10)
    credentials_window.wait_window()


class SpotifyAuth:
    """Handles the OAuth flow and token management for Spotify."""

    REDIRECT_URI = "http://localhost:5000/callback"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    AUTH_URL = 'https://accounts.spotify.com/authorize'
    API_BASE_URL = 'https://api.spotify.com/v1'
    SCOPES = (
        "user-read-private "
        "user-read-email "
        "playlist-read-private "
        "user-follow-read "
        "user-follow-modify "
        "user-library-read "
        "user-library-modify "
        "user-modify-playback-state "
        "user-read-playback-state "
    )

    def __init__(self, message_queue):
        self.message_queue = message_queue
        self.app = Flask(__name__) 
        self.app.add_url_rule('/callback', 'callback', self.callback)

    def run_flask_app(self):
        """Run Flask app to handle OAuth callback."""
        try:
            self.app.run(port=5000, debug=True, use_reloader=False)
        except Exception as e:
            self.message_queue.put(f"error:Flask app failed to start: {str(e)}")

    # @self.app.route('/callback')
    def callback(self):
        """Handle the callback from Spotify OAuth."""
        if 'error' in request.args:
            error_message = request.args["error"]
            self.message_queue.put(f"error:{error_message}")
            return jsonify({"error": error_message}), 400

        auth_code = request.args.get('code')

        if not auth_code:
            self.message_queue.put("error:No authorization code provided")
            return "Authorization failed. No code provided.", 400

        # Exchange authorization code for tokens
        return self.exchange_code_for_tokens(auth_code)

    def exchange_code_for_tokens(self, auth_code):
        """Exchange authorization code for access and refresh tokens."""
        try:
            req_body = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.REDIRECT_URI,
                'client_id': os.getenv("CLIENT_ID"),
                'client_secret': os.getenv("CLIENT_SECRET"),
            }
            response = requests.post(self.TOKEN_URL, data=req_body)
            if response.status_code == 200:
                data = response.json()
                self.save_tokens(data)
                self.message_queue.put("success")
                return self.success_response()
            else:
                error_message = f"Authorization failed: {response.text}"
                self.message_queue.put(f"error:{error_message}")
                return error_message, 400
        except requests.exceptions.RequestException as e:
            self.message_queue.put(f"error:Request failed: {str(e)}")
            return "Authorization failed due to network error.", 500

    def save_tokens(self, data):
        """Save the access and refresh tokens to environment variables."""
        try:
            expires_at = str(datetime.now().timestamp() + data['expires_in'])
            os.environ["ACCESS_TOKEN"] = data['access_token']
            os.environ["REFRESH_TOKEN"] = data['refresh_token']
            os.environ["EXPIRES_AT"] = expires_at
            # set_key('.env', 'ACCESS_TOKEN', data['access_token'])
            # set_key('.env', 'REFRESH_TOKEN', data['refresh_token'])
            # set_key('.env', 'EXPIRES_AT', expires_at)
        except Exception as e:
            self.message_queue.put(f"error:Failed to save tokens: {str(e)}")
            

    def success_response(self):
        """Returns success message for successful OAuth callback."""
        return """
        <html>
        <body>
        <h1>Authorization successful!</h1>
        <p>You can now close this tab.</p>
        </body>
        </html>
        """


class AuthManager:
    """Handles the flow of authentication and starts the main interface."""

    def __init__(self):
        self.message_queue = queue.Queue()
        self.token_manager = TokenManager(self.message_queue)
        self.spotify_auth = SpotifyAuth(self.message_queue)

    def authenticate_user(self, root):
        """Start the user authentication process."""
        # Start Flask app in a separate thread
        flask_thread = threading.Thread(target=self.spotify_auth.run_flask_app)
        flask_thread.daemon = True  # Allow Flask thread to exit when main thread exits
        flask_thread.start()

        # Start the process to get user credentials
        get_user_credentials(root, self.token_manager)

        # Wait for successful authentication or error
        self.wait_for_authentication(root)

    def wait_for_authentication(self, root):
        """Wait until authentication is complete or an error occurs."""
        while True:
            try:
                message = self.message_queue.get(timeout=1)
                if message.startswith("success"):
                    messagebox.showinfo("Authentication", "Authentication successful!")
                    break
                elif message.startswith("error"):
                    error_message = message.split(":", 1)[1]
                    messagebox.showerror("Authentication Error", error_message)
                    get_user_credentials(root, self.token_manager)  # Retry login
            except queue.Empty:
                continue


class App:
    """Main application that initializes the interface and handles user flow."""

    def __init__(self, root):
        self.root = root
        self.auth_manager = AuthManager()

    def run(self):
        """Runs the application."""
        self.root.withdraw()  # Hide the root window while getting credentials

        # Authenticate user
        self.auth_manager.authenticate_user(self.root)

        # Initialize main interface after authentication
        self.launch_main_interface()

    def launch_main_interface(self):
        """Launch the main interface after successful authentication."""
        print("Launching main interface.......")
        app = MainInterface(self.root, self.auth_manager.token_manager)

        # Show the main window
        self.root.deiconify()

        # Run Tkinter main loop
        self.root.mainloop()


def main():
    """Main function to initialize the Tkinter app and start the user flow."""
    root = tk.Tk()  # Create the Tkinter root window
    app = App(root)
    app.run()


if __name__ == "__main__":
    main()