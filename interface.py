import tkinter as tk
from tkinter import messagebox, Toplevel, ttk
import random, os, traceback, spotipy, threading
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image, ImageTk  # If using Tkinter for display
from functools import partial
from spotipy_api_oauth import (
    get_topsongs_by_artist, 
    search_for_track, 
    search_for_artist, 
    search_for_genre, 
    format_duration,
    format_number_display,
    generate_recommendations, 
    get_user_followed_artists,
    follow_artist,
    get_user_tracks,
    get_album_info,
    get_artist_info,
    get_track_info,
    save_track,
    remove_track,
    unfollow_artist,
    fetch_user_profile)


class MainInterface:
    def __init__(self, root, token_manager, get_user_credentials, App):
        self.root = root
        self.root.title("MySpotify 1.0 Beta")
        # Initialize data with categories for demonstration purposes
        # self.all_results = [
        #     {"category": "singer", "record": "Taylor Swift"},
        #     {"category": "singer", "record": "Adele"},
        #     {"category": "Album", "record": "Shake It Off"},
        #     {"category": "Track", "record": "Hello"},
        #     {"category": "Album", "record": "Blank Space"},
        # ]  # Example records
        self.token = os.getenv("ACCESS_TOKEN")
        self.all_results = []
        self.saved_list = get_user_tracks(self.token)
        self.followed_list = get_user_followed_artists(self.token)
        self.current_page = 1
        self.results_per_page = 5
        self.token_manager = token_manager
        print(f"self.token: {self.token}")
        self.sp = spotipy.Spotify(auth=self.token)
        self.prev_button = None
        self.next_button = None
        self.get_user_credentials = get_user_credentials
        self.App = App
        # self.access_token = access_token
    
        # Maintain separate states for followed artists and saved tracks
        self.followed_artists = {}
        self.saved_tracks = {}

        # Initialize category options
        self.categories = ["Not Selected", "Artist", "Track", "Genre"]

        # Sections
        self.create_details_section()
        self.create_search_section()
        self.create_saved_list_section()
        self.create_recommendation_section()
        self.create_topSongs_section()
        self.create_followed_list_section()  # New section for followed singers
        self.create_user_profile()
        self.adjust_grid()
        # self.auto_refresh_recommendations()

    def create_details_section(self):
        """Creates the central frame to display detailed information."""
        self.details_frame = ttk.Frame(self.root, padding=10, borderwidth=2, relief="solid")
        self.details_frame.grid(row=1, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        # Add a default label as a placeholder
        self.details_label = ttk.Label(self.details_frame, text="Details will appear here", anchor="center")
        self.details_label.pack(expand=True, fill="both")

    
    def create_search_section(self):
        self.search_frame = ttk.Frame(self.root)
        self.search_frame.grid(row=0, column=1, padx=20, pady=15, sticky="nsew")

        # Label
        ttk.Label(self.search_frame, text="Search Bar").grid(row=0, column=0, padx=1)

        # Search Entry
        self.search_entry = ttk.Entry(self.search_frame, width=30)
        self.search_entry.grid(row=0, column=1, padx=3)

        # Category Dropdown
        self.category_var = tk.StringVar()
        self.category_var.set(self.categories[0])  # Default to "Not Selected"
        self.category_menu = ttk.OptionMenu(self.search_frame, self.category_var, *self.categories)
        self.category_menu.grid(row=0, column=2, padx=1)

        # Search Button
        self.search_button = ttk.Button(self.search_frame, text="Search", command=self.display_results)
        self.search_button.grid(row=0, column=3, padx=1)

        # Results display area with a canvas and scrollbar
        self.results_canvas = tk.Canvas(self.search_frame, height=300, width=700)
        self.results_canvas.grid(row=1, column=0, columnspan=4, pady=5, sticky="ew")

        # Scrollbar
        self.results_scrollbar = ttk.Scrollbar(self.search_frame, orient="vertical", command=self.results_canvas.yview)
        self.results_scrollbar.grid(row=1, column=4, sticky="ns")
        self.results_canvas.configure(yscrollcommand=self.results_scrollbar.set)

        # Inner frame for results
        self.results_frame = ttk.Frame(self.results_canvas)
        self.results_canvas.create_window((0, 0), window=self.results_frame, anchor="nw")

        # # Pagination controls
        self.prev_button = ttk.Button(self.search_frame, text="<< Prev", command=self.prev_page)
        self.prev_button.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.prev_button.grid_remove()

        self.page_label = ttk.Label(self.search_frame, text="")
        self.page_label.grid(row=2, column=1)

        self.next_button = ttk.Button(self.search_frame, text="Next >>", command=self.next_page)
        self.next_button.grid(row=2, column=2, sticky="e", padx=5, pady=5)
        self.next_button.grid_remove()

        # self.update_navigation_buttons(total_pages=1)

        # Configure scrolling
        self.results_frame.bind("<Configure>", lambda e: self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all")))


    def adjust_grid(self):
        """Ensure rows and columns are resized properly."""
        # Adjust grid row weights for better alignment
        self.root.grid_rowconfigure(0, weight=1)  # Adjust weight of row 0 (topSongs_frame)
        self.root.grid_rowconfigure(1, weight=1)  # Adjust weight of row 1 (save_list_frame)
        self.root.grid_rowconfigure(2, weight=1)  # Adjust weight of row 2 (followed_list_frame)

        self.root.grid_columnconfigure(2, weight=1)  # Ensure column 2 (where frames are placed) expands properly

    def create_user_profile(self):
        # Create a frame to hold the profile information
        frame = ttk.Frame(self.root)  # Changed tk.Frame to ttk.Frame
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")  # Adjust row/column as needed

        # Fetch user profile information
        user_info = fetch_user_profile(self.token)

        if not user_info:
            error_label = ttk.Label(frame, text="Error Fetching user profile.", foreground="red", font=("Arial", 14))  # Changed tk.Label to ttk.Label
            error_label.grid(row=0, column=0, padx=10, pady=10)
            return

        # Display the user's name
        name_label = ttk.Label(frame, text=f"Name: {user_info['display_name']}", font=("Arial", 14))  # Changed tk.Label to ttk.Label
        name_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        email_label = ttk.Label(frame, text=f"Email: {user_info['email']}", font=("Arial", 14))  # Changed tk.Label to ttk.Label
        email_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        # Display the user's followers count
        followers_label = ttk.Label(frame, text=f"Followers: {format_number_display(user_info['followers'])}", font=("Arial", 14))  # Changed tk.Label to ttk.Label
        followers_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)

        # Display the user's profile image
        try:
            # 'image_info' already contains the byte stream (BytesIO)
            image_stream = user_info['image_info']

            # Open the image using Pillow directly from the byte stream
            pil_image = Image.open(image_stream)
            pil_image = pil_image.resize((200, 200))  # Resize image (optional)

            # Convert the image to a format suitable for Tkinter
            tk_image = ImageTk.PhotoImage(pil_image)

            # Display the image in a Label
            image_label = ttk.Label(frame, image=tk_image)  # Changed tk.Label to ttk.Label
            image_label.image = tk_image  # Keep a reference to avoid garbage collection
            image_label.grid(row=0, column=0, pady=10)

        except KeyError:
            # Handle case where 'image_info' is missing
            error_label = ttk.Label(frame, text="Error: No image available", foreground="red")  # Changed tk.Label to ttk.Label
            error_label.grid(row=2, column=0, sticky="w")
        except Exception as e:
            # Handle other exceptions (e.g., image processing errors)
            error_label = ttk.Label(frame, text=f"Error loading image: {e}", foreground="red")  # Changed tk.Label to ttk.Label
            error_label.grid(row=2, column=0, sticky="w")

        logoff_button = ttk.Button(frame, text="Log Off", command=self.log_off)  # Correct usage of ttk.Button
        logoff_button.grid(row=4, column=0, pady=10)


    def log_off(self):
        """Handles logging off the user by clearing authentication data."""
        print("Logging off...")

        # Clear token data
        self.token_manager.access_token = None
        self.token_manager.refresh_token = None
        self.token_manager.expires_at = None
        # self.token_manager.save_tokens_to_env()  # Assuming this method saves the empty token data

        # Optionally, hide the main interface and show the login screen
        self.root.withdraw()  # Hide the main interface
        self.show_login_screen()  # Show login screen

    def show_login_screen(self):
        """Display the login screen (restarting the authentication process)."""
        try:
            app = self.App(self.root)
            app.run()
            self.root.mainloop()
        except Exception as e:
            print(f"Error during login process: {e}")
            self.root.destroy()  # Show the main root window again



    def create_topSongs_section(self):
        """Creates the section to display top 10 popular songs with Frame/Canvas alignment."""
        # Frame for Top Songs Section
        self.topSongs_frame = ttk.Frame(self.root)
        self.topSongs_frame.grid(row=0, column=2, padx=10, pady=(10, 0), sticky="nsew")

        # Configure row/column weights for resizing
        self.topSongs_frame.grid_rowconfigure(1, weight=1)
        self.topSongs_frame.grid_columnconfigure(0, weight=1)

        # Label for Top Songs
        self.topSongs_label = ttk.Label(self.topSongs_frame, text="Top Songs", anchor="center", font=("Arial", 12))
        self.topSongs_label.grid(row=0, column=0, pady=(5, 0), sticky="ew")  # Center the label across two columns

        # Configure column weights to distribute space properly
        self.topSongs_frame.grid_columnconfigure(0, weight=1)  # Give some weight to the first column
        self.topSongs_frame.grid_columnconfigure(1, weight=1)  # Ensure the second column also has weight

        # Canvas for scrollable content
        self.topSongs_canvas = tk.Canvas(self.topSongs_frame)
        self.topSongs_canvas.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # Scrollbar for the Canvas
        scrollbar = ttk.Scrollbar(self.topSongs_frame, orient="vertical", command=self.topSongs_canvas.yview)
        scrollbar.grid(row=2, column=1, sticky="nse")

        # Configure the Canvas to work with the Scrollbar
        self.topSongs_canvas.configure(yscrollcommand=scrollbar.set)

        # Frame inside Canvas for content
        self.topSongs_content_frame = ttk.Frame(self.topSongs_canvas)
        self.topSongs_canvas.create_window((0, 0), window=self.topSongs_content_frame, anchor="nw")

        # Ensure Canvas scroll region updates dynamically
        self.topSongs_content_frame.bind(
            "<Configure>",
            lambda e: self.topSongs_canvas.configure(scrollregion=self.topSongs_canvas.bbox("all"))
        )

        # Initial message
        label = ttk.Label(self.topSongs_content_frame, text="Choose an Artist to View Top Songs!", anchor="center")
        label.pack(pady=10)


    def create_saved_list_section(self):
        # Save List Frame
        self.saved_list_frame = tk.Frame(self.root, width=350, height=250)  # Set fixed size
        self.saved_list_frame.grid(row=1, column=0, padx=10, pady=(5, 5), sticky="nsew")
        self.saved_list_frame.grid_propagate(False)  # Prevent frame from resizing

        # Label for saved songs section
        self.saved_list_label = tk.Label(self.saved_list_frame, text="Saved Songs", font=("Arial", 12, "bold"))
        self.saved_list_label.grid(row=0, column=0, columnspan=2, padx=5, pady=(5, 0), sticky="we")  # Align label at the top

        # Canvas for the scrollable save list
        self.saved_list_canvas = tk.Canvas(self.saved_list_frame, width=300, height=230)  # Set fixed dimensions
        self.saved_list_canvas.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Scrollbar for the canvas
        scrollbar = tk.Scrollbar(self.saved_list_frame, orient=tk.VERTICAL, command=self.saved_list_canvas.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")

        # Link the scrollbar to the canvas
        self.saved_list_canvas.config(yscrollcommand=scrollbar.set)

        # Frame inside the canvas for list content
        self.saved_list_content_frame = tk.Frame(self.saved_list_canvas)
        self.saved_list_canvas.create_window((0, 0), window=self.saved_list_content_frame, anchor="nw")

        # Update scrollable region of the canvas
        self.saved_list_content_frame.bind(
            "<Configure>",
            lambda e: self.saved_list_canvas.configure(scrollregion=self.saved_list_canvas.bbox("all")),
        )

        # Allow canvas to expand
        # self.save_list_frame.grid_rowconfigure(1, weight=1)
        # self.save_list_frame.grid_columnconfigure(0, weight=1)

        # Initialize the save list content
        self.refresh_saved_list()

    
    def create_followed_list_section(self):
        # New section for followed singers
        self.followed_list_frame = tk.Frame(self.root, width=350, height=250)
        self.followed_list_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="nsew")
        self.followed_list_frame.grid_propagate(False)  # Prevent frame from resizing

        # Create the label for the followed singers section
        self.followed_list_label = tk.Label(self.followed_list_frame, text="Followed Singers", font=("Arial", 12, "bold"))
        self.followed_list_label.grid(row=0, column=0, columnspan=2, padx=5, pady=(5, 0), sticky="we")  # Use columnspan to span across both columns

        # Create a canvas widget to hold the followed list
        self.followed_list_canvas = tk.Canvas(self.followed_list_frame, width=300, height=230)  # Set fixed width
        self.followed_list_canvas.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")  # Place canvas on row 1

        # Create a scrollbar for the canvas
        scrollbar = tk.Scrollbar(self.followed_list_frame, orient=tk.VERTICAL, command=self.followed_list_canvas.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")  # Place scrollbar next to canvas in row 1

        # Link the scrollbar to the canvas
        self.followed_list_canvas.config(yscrollcommand=scrollbar.set)

        # Create a frame within the canvas to hold the list of followed singers
        self.followed_list_content_frame = tk.Frame(self.followed_list_canvas)  # Set fixed width
        # Add the content frame to the canvas
        self.followed_list_canvas.create_window((0, 0), window=self.followed_list_content_frame, anchor="nw")

        # Update the scrollable region of the canvas whenever the content changes
        self.followed_list_content_frame.bind(
            "<Configure>",
            lambda e: self.followed_list_canvas.configure(scrollregion=self.followed_list_canvas.bbox("all")),
        )

        # # Allow the frame to resize properly
        # self.followed_list_frame.grid_rowconfigure(1, weight=1)  # Allow canvas to expand vertically
        # self.followed_list_frame.grid_columnconfigure(0, weight=1)  # Allow canvas to expand horizontally

        self.refresh_followed_list()



    def create_recommendation_section(self):
        """Creates the recommendation section with refresh, save, and details features using Canvas and Frame."""
        # Recommendation Frame
        self.recommend_frame = ttk.Frame(self.root)
        self.recommend_frame.grid(row=1, column=2, rowspan=2, columnspan=2, padx=10, pady=(0, 5), sticky="nsew")

        # Configure the row weights for the frame to push the button to the bottom
        self.recommend_frame.grid_rowconfigure(1, weight=1)  # Content will expand
        self.recommend_frame.grid_rowconfigure(2, weight=0)  # Button remains at the bottom
        self.recommend_frame.grid_columnconfigure(0, weight=1)

        # Recommendation Label
        self.recommend_label = ttk.Label(
            self.recommend_frame, text="Track Recommendations For You!!", anchor="center"
        )
        self.recommend_label.grid(row=0, column=0, columnspan=2, pady=(5, 0))

        # Canvas for scrolling content
        self.recommend_canvas = tk.Canvas(self.recommend_frame, width=350, height=300)
        self.recommend_canvas.grid(row=1, column=0, columnspan=2, pady=5, sticky="nsew")

        # Scrollbar for the Canvas
        scrollbar = ttk.Scrollbar(self.recommend_frame, orient=tk.VERTICAL, command=self.recommend_canvas.yview)
        scrollbar.grid(row=1, column=2, sticky="ns")

        # Configure Canvas to work with the Scrollbar
        self.recommend_canvas.configure(yscrollcommand=scrollbar.set)

        # Frame inside the Canvas to hold recommendations
        self.recommend_content_frame = ttk.Frame(self.recommend_canvas)
        self.recommend_content_frame.bind(
            "<Configure>",
            lambda e: self.recommend_canvas.configure(scrollregion=self.recommend_canvas.bbox("all"))
        )

        # Add the frame to the Canvas
        self.recommend_canvas.create_window((0, 0), window=self.recommend_content_frame, anchor="nw")

        # Refresh button
        refresh_button = ttk.Button(self.recommend_frame, text="Refresh", command=self.refresh_recommendations)
        refresh_button.grid(row=2, column=0, columnspan=2, pady=5, sticky="sew")


        # Initial population of recommendations
        # self.refresh_recommendations()

    def refresh_recommendations(self):
        """Refreshes the recommendations with new items and adds Save, Follow, and Details buttons for each."""
        # Clear existing widgets in the recommendation content frame
        for widget in self.recommend_content_frame.winfo_children():
            widget.destroy()

        # Generate recommendations (replace with your actual logic)
        recommendations = generate_recommendations(self.token, self.saved_list, self.followed_list)

        if recommendations is None:
            ttk.Label(
                self.recommend_content_frame, 
                text="No available recommended Songs based on your Favourites.", 
                anchor="center"
            ).grid(row=0, column=0, columnspan=4, pady=10)  # Increase pady for better spacing
            return
        elif not isinstance(recommendations, list):
            print("Recommendations is not a list:", type(recommendations))
            return

        # Sort recommendations by popularity in descending order
        recommendations_sorted = sorted(recommendations, key=lambda x: x["popularity"], reverse=True)

        # Populate the recommendation content frame with new recommendations
        for index, track in enumerate(recommendations_sorted):
            # Display track information
            track_label = ttk.Label(
                self.recommend_content_frame, 
                text=f"Top {index+1}: Track: {track['track_name']}\nPopularity: {track['popularity']}\n"
                    f"Album: '{track['album']}'\nDuration: {format_duration(track['track_duration'])}",
                anchor="w",
                justify="left",
                wraplength=300
            )
            track_label.grid(row=index * 2, column=0, columnspan=3, sticky="w", padx=5, pady=(10 if index == 0 else 5))

            # Add buttons in a new row below the text for better separation
            button_row = index * 2 + 1
            save_button = ttk.Button(
                self.recommend_content_frame, 
                text="Add", 
                command=lambda r=track: self.handle_clicks(r["track_id"], "save", "track")
            )
            save_button.grid(row=button_row, column=0, padx=2, pady=5)

            follow_button = ttk.Button(
                self.recommend_content_frame, 
                text="Follow", 
                command=lambda r=track: self.create_artist_selector(r["artist_list"])
            )
            follow_button.grid(row=button_row, column=1, padx=2, pady=5)

            details_button = ttk.Button(
                self.recommend_content_frame, 
                text="Details", 
                command=lambda r=track: self.show_details(r['track_id'], 'track_details')
            )
            details_button.grid(row=button_row, column=2, padx=2, pady=5)

        # Update the canvas scroll region
        self.recommend_canvas.configure(scrollregion=self.recommend_canvas.bbox("all"))

        # Add a blank row at the bottom for spacing between lists
        self.recommend_content_frame.grid_rowconfigure(len(recommendations_sorted) * 2 + 1, minsize=20)



     
    def auto_refresh_recommendations(self):
        """Automatically refresh recommendations every 30 seconds."""
        self.refresh_recommendations()
        self.root.after(5000, self.auto_refresh_recommendations)  # 5-second interval for presentation


    def update_topSongs(self, artist_id, artist_name):
        """Updates the display of top 10 songs for a specific artist using Frame/Canvas."""
        # Clear existing content in the Canvas
        for widget in self.topSongs_content_frame.winfo_children():
            widget.destroy()

        # Header with artist name and follow button
        header_frame = ttk.Frame(self.topSongs_content_frame)
        header_frame.pack(fill="x", pady=(5, 10))

        songs = get_topsongs_by_artist(self.token, artist_id, "us")

        self.topSongs_label.config(text=f"10 Top Songs From ({artist_name})", anchor="w", font=("Arial", 12, "bold"), foreground="blue")

        # # Static label
        # static_label = ttk.Label(header_frame, text="Top 10 Songs by", font=("Arial", 12))
        # static_label.pack(side="left", padx=(5, 0))

        # # Artist name in bold blue
        # artist_label = ttk.Label(header_frame, text=artist_name, font=("Arial", 12, "bold"), foreground="blue")
        # artist_label.pack(side="left", padx=5)

        # Artist Details button
        artist_details_button = ttk.Button(self.topSongs_frame, text="Artist Details", command=lambda r=artist_id: self.show_details(r, "artist_details"))
        artist_details_button.grid(row=1, column=0, padx=(0, 10), sticky="ew")  # Expand to fill the first column

        # Follow/Unfollow button
        is_followed = any(followed_artist['artist_id'] == artist_id for followed_artist in self.followed_list)
        follow_button_text = "Unfollow" if is_followed else "Follow"

        def toggle_follow():
            nonlocal is_followed
            action = "follow" if not is_followed else "unfollow"
            self.handle_clicks(artist_id, action, "artist")
            is_followed = not is_followed
            follow_button.config(text="Unfollow" if is_followed else "Follow")

        follow_button = ttk.Button(self.topSongs_frame, text=follow_button_text, command=toggle_follow)
        follow_button.grid(row=1, column=1, padx=(10, 0), sticky="ew")  # Expand to fill the second column
        
        # Display top songs
        if songs:
            # Sort and display songs
            songs_sorted = sorted(songs, key=lambda x: x["popularity"], reverse=True)
            for index, song in enumerate(songs_sorted):
                song_frame = ttk.Frame(self.topSongs_content_frame)
                song_frame.pack(fill="x", pady=5)

                # Song details
                song_label = ttk.Label(
                    song_frame,
                    text=f"Top {index + 1}:\n{song['track_name']}\nAlbum: {song['album']}\nPopularity: {song['popularity']}",
                    wraplength=300,
                    anchor="w",
                    width=50  # Fixed width to ensure consistent wrapping
                )
                song_label.pack(side="top", padx=5, anchor="w")

                # Create buttons for Play, Save, and Details underneath each song label
                button_frame = ttk.Frame(song_frame)
                button_frame.pack(fill="x", pady=5)

                # Play button
                play_button = ttk.Button(button_frame, text="Play", command=lambda r=song: self.open_playback_console(r["track_id"]))
                play_button.pack(side="left", padx=(5, 0))

                # Save button
                save_button = ttk.Button(button_frame, text="Save", command=lambda r=song: self.handle_clicks(r["track_id"], "save", "track"))
                save_button.pack(side="left", padx=(5, 0))

                # Track Details button
                track_details_button = ttk.Button(button_frame, text="Track Details", command=lambda r=song: self.show_details(r['track_id'], "track_details"))
                track_details_button.pack(side="left", padx=(5, 0))

        else:
            # No songs found message
            no_songs_label = ttk.Label(self.topSongs_content_frame, text="No top songs available.", anchor="center")
            no_songs_label.pack(pady=10)



    # def display_results(self):
    #     # Clear the results frame
    #     for widget in self.results_frame.winfo_children():
    #         widget.destroy()

    #     keyword = self.search_entry.get().lower()
    #     selected_category = self.category_var.get().lower()

    #     # Fetch results based on category
    #     if selected_category == "track":
    #         raw_results = search_for_track(self.token, keyword)
    #     elif selected_category == "artist":
    #         raw_results = search_for_artist(self.token, keyword)
    #     elif selected_category == "genre":
    #         raw_results = search_for_genre(self.token, keyword)
    #     else:
    #         tk.Label(self.results_frame, text="Select a category and input a keyword for search.").pack(anchor="w")
    #         return

    #     # Filter out empty or invalid results
    #     self.all_results = [result for result in raw_results if result]  # Exclude None or empty results

    #     # Check if there are no valid results after filtering
    #     if not self.all_results:
    #         tk.Label(self.results_frame, text="No valid results found.").pack(anchor="w")
    #         self.page_label.config(text="")  # Clear pagination label
    #         self.update_navigation_buttons()
    #         return
    #     else:
    #         self.all_results_sorted = sorted(self.all_results, key=lambda x: x["popularity"], reverse=True)

    #     # Paginate filtered results
    #     start_idx = (self.current_page - 1) * self.results_per_page
    #     end_idx = start_idx + self.results_per_page
    #     results_to_display = self.all_results_sorted[start_idx:end_idx]

    #     for result in results_to_display:
    #         # Container frame for each result
    #         result_frame = ttk.Frame(self.results_frame, padding=(5, 5))
    #         result_frame.pack(fill="x", pady=5)

    #         # Display text
    #         if selected_category == "track" or selected_category == "genre":
    #             display_text = (
    #                 f"Track: {result['track_name']}\n"
    #                 f"Album: {result['album']}\n"
    #                 f"Popularity: {result['popularity']}\n"
    #                 f"Artist(s): {', '.join(artist['name'] for artist in result['artist_list'])}\n"
    #                 f"Duration: {format_duration(result['track_duration'])}"
    #             )
    #             tk.Label(result_frame, text=display_text, justify="left").pack(anchor="w")

    #             # Save/Remove Button
    #             track_id = result["track_id"]
    #             is_saved = self.saved_tracks.get(track_id, False)
    #             button_text = "Remove" if is_saved else "Add"
    #             save_button = ttk.Button(
    #                 result_frame,
    #                 text=button_text,
    #                 command=partial(
    #                     self.toggle,
    #                     item_id=track_id,
    #                     button=None,  # No need to update button text here
    #                     action_type="save",
    #                     is_active=is_saved,
    #                 ),
    #             )
    #             save_button.pack(side="left", padx=5)

    #             # Play Button
    #             ttk.Button(
    #                 result_frame,
    #                 text="Play",
    #                 command=lambda r=result: self.open_playback_console(r["track_id"]),
    #             ).pack(side="left", padx=5)

    #             # Details Button
    #             ttk.Button(
    #                 result_frame,
    #                 text="Details",
    #                 command=lambda r=result: self.show_details(r, "track_details"),
    #             ).pack(side="left", padx=5)

    #             # Artists to Follow Button
    #             ttk.Button(
    #                 result_frame,
    #                 text="Artists to Follow",
    #                 command=lambda r=result: self.create_artist_selector(r["artist_list"]),
    #             ).pack(side="left", padx=5)

    #         elif selected_category == "artist":
    #             display_text = (
    #                 f"Artist: {result['artist_name']}\n"
    #                 f"Genres: {', '.join(result['genres'])}\n"
    #                 f"Popularity: {result['popularity']}"
    #             )
    #             tk.Label(result_frame, text=display_text, justify="left").pack(anchor="w")

    #             # Follow/Unfollow Button
    #             artist_id = result["artist_id"]
    #             is_followed = self.followed_artists.get(artist_id, False)
    #             button_text = "Unfollow" if is_followed else "Follow"
    #             follow_button = ttk.Button(
    #                 result_frame,
    #                 text=button_text,
    #                 command=partial(
    #                     self.toggle,
    #                     item_id=artist_id,
    #                     button=None,  # No need to update button text here
    #                     action_type="follow",
    #                     is_active=is_followed,
    #                 ),
    #             )
    #             follow_button.pack(side="left", padx=5)

    #             # Details Button
    #             ttk.Button(
    #                 result_frame,
    #                 text="Details",
    #                 command=lambda r=result: self.show_details(r, "artist_details"),
    #             ).pack(side="left", padx=5)

    #             # Top Songs Button
    #             ttk.Button(
    #                 result_frame,
    #                 text="Top Songs",
    #                 command=lambda r=result: self.update_topSongs(r["artist_id"], r["artist_name"]),
    #             ).pack(side="left", padx=5)

    #     # Pagination
    #     total_pages = max(1, (len(self.all_results) + self.results_per_page - 1) // self.results_per_page)
    #     self.page_label.config(text=f"Page {self.current_page}/{total_pages}")
    #     self.update_navigation_buttons(total_pages)

    def display_results(self):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        keyword = self.search_entry.get().lower()
        selected_category = self.category_var.get().lower()

        # Fetch results based on category
        if selected_category == "track":
            raw_results = search_for_track(self.token, keyword)
        elif selected_category == "artist":
            raw_results = search_for_artist(self.token, keyword)
        elif selected_category == "genre":
            raw_results = search_for_genre(self.token, keyword)
        else:
            ttk.Label(self.results_frame, text="Select a category and input a keyword for search.").grid(row=0, column=0, sticky="w")
            return

        # Filter and validate results
        self.all_results = [result for result in raw_results if result]
        if not self.all_results:
            ttk.Label(self.results_frame, text="No results found.").grid(row=0, column=0, sticky="w")
            self.page_label.config(text="")
            self.update_navigation_buttons(total_pages=1)
            return

        self.all_results_sorted = sorted(self.all_results, key=lambda x: x["popularity"], reverse=True)

        # Pagination
        start_idx = (self.current_page - 1) * self.results_per_page
        end_idx = start_idx + self.results_per_page
        results_to_display = self.all_results_sorted[start_idx:end_idx]

        for idx, result in enumerate(results_to_display, start=1):
            result_frame = ttk.Frame(self.results_frame, padding=(5, 5))
            result_frame.grid(row=idx, column=0, sticky="w", pady=5)

            # Display result details
            if selected_category == "track" or selected_category == "genre":
                display_text = (
                    f"Track: {result['track_name']}\n"
                    f"Album: {result['album']}\n"
                    f"Popularity: {result['popularity']}\n"
                    f"Artist(s): {', '.join(artist['name'] for artist in result['artist_list'])}\n"
                    f"Duration: {format_duration(result['track_duration'])}"
                )
            elif selected_category == "artist":
                display_text = (
                    f"Artist: {result['artist_name']}\n"
                    f"Genres: {', '.join(result['genres'])}\n"
                    f"Popularity: {result['popularity']}"
                )
            
            # Display the result text
            ttk.Label(result_frame, text=display_text, anchor="w", justify="left").grid(row=0, column=0, sticky="w", columnspan=5)

            # Add buttons (save, details, etc.)
            button_row = 1  # Start buttons in row 1
            if selected_category == "track" or selected_category == "genre":
                track_id = result["track_id"]
                is_saved = any(track['track_id'] == track_id for track in self.saved_list)
                
                # Create the button first
                button = ttk.Button(result_frame, text="Remove" if is_saved else "Add")
                button.config(command=partial(self.toggle, item_id=track_id, button=button, action_type="save", is_active=is_saved))
                button.grid(row=button_row, column=0, padx=5, sticky="w")

                # Play Button
                play_button = ttk.Button(result_frame, text="Play", command=lambda r=result: self.open_playback_console(r["track_id"]))
                play_button.grid(row=button_row, column=1, padx=5, sticky="w")

                # Details Button
                details_button = ttk.Button(result_frame, text="Details", command=lambda r=result: self.show_details(r['track_id'], "track_details"))
                details_button.grid(row=button_row, column=2, padx=5, sticky="w")

                # Artists to Follow Button
                follow_button = ttk.Button(result_frame, text="Artists to Follow", command=lambda r=result: self.create_artist_selector(r["artist_list"]))
                follow_button.grid(row=button_row, column=3, padx=5, sticky="w")

            elif selected_category == "artist":
                artist_id = result["artist_id"]
                is_followed = any(artist['artist_id'] == artist_id for artist in self.followed_list)
                
                # Create the button first
                follow_button = ttk.Button(result_frame, text="Unfollow" if is_followed else "Follow")
                follow_button.config(command=partial(self.toggle, item_id=artist_id, button=follow_button, action_type="follow", is_active=is_followed))
                follow_button.grid(row=button_row, column=0, padx=5, sticky="w")

                # Details Button
                details_button = ttk.Button(result_frame, text="Details", command=lambda r=result: self.show_details(r['artist_id'], "artist_details"))
                details_button.grid(row=button_row, column=1, padx=5, sticky="w")

                # Top Songs Button
                top_songs_button = ttk.Button(result_frame, text="Top Songs", command=lambda r=result: self.update_topSongs(r["artist_id"], r["artist_name"]))
                top_songs_button.grid(row=button_row, column=2, padx=5, sticky="w")

            button_row += 1

        # Update pagination
        total_pages = max(1, (len(self.all_results) + self.results_per_page - 1) // self.results_per_page)
        self.page_label.config(text=f"Page {self.current_page}/{total_pages}")

         # Show and enable/disable pagination buttons
        if total_pages > 1:
            self.prev_button.grid()  # Show Prev button
            self.next_button.grid()  # Show Next button
            self.prev_button.config(state=tk.NORMAL if self.current_page > 1 else tk.DISABLED)
            self.next_button.config(state=tk.NORMAL if self.current_page < total_pages else tk.DISABLED)
        else:
            self.prev_button.grid_remove()  # Hide Prev button
            self.next_button.grid_remove()  # Hide Next button

        self.update_navigation_buttons(total_pages)


    
    def follow_singer(self, singer):
        if singer not in self.followed_list:
            self.followed_list.append(singer)
            self.update_followed_list()
        else:
            messagebox.showinfo("Followed Artist(s)", f"{singer['artist_name']} is already followed.")

    
    def update_followed_list(self):
        try:
            # Clear the previous followed list content by using grid_forget
            for widget in self.followed_list_content_frame.winfo_children():
                widget.grid_forget()
            
            if not self.followed_list:
                # Display a message if no followed singers are available
                no_followed_label = tk.Label(self.followed_list_content_frame, text="No Followed Singer(s) yet.")
                no_followed_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
                return

            # Update the followed list label with the total count
            self.followed_list_label.config(text=f"Followed Singers ({len(self.followed_list)} in total)")

            # Iterate through the followed singers and display their details
            for row, singer in enumerate(self.followed_list):
                # Create a frame for each followed singer
                singer_frame = ttk.Frame(self.followed_list_content_frame, padding=5)
                singer_frame.grid(row=row, column=0, sticky="w", padx=5, pady=5, columnspan=3)  # Adjust columnspan to fit all buttons

                # Display singer details
                ttk.Label(
                    singer_frame,
                    text=f"Artist Name: {singer['artist_name']}\nGenres: {', '.join(singer['genres'])}\n",
                    anchor="w", justify="left", wraplength=200
                ).grid(row=0, column=0, columnspan=3, sticky="w")

                # Create a "Details" button for each followed singer
                details_button = ttk.Button(singer_frame, text="Details", command=lambda r=singer: self.show_details(r['artist_id'], 'artist_details'))
                details_button.grid(row=1, column=0, padx=5, pady=5)

                # Create an "Unfollow" button for each followed singer
                unfollow_button = ttk.Button(singer_frame, text="Unfollow", command=lambda s=singer: self.handle_clicks(s['artist_id'], "unfollow", "artist"))
                unfollow_button.grid(row=1, column=1, padx=5, pady=5)

                # Create a "Top Song" button for each followed singer
                top_song_button = ttk.Button(singer_frame, text="Top Song", command=lambda s=singer: self.update_topSongs(s['artist_id'], s['artist_name']))
                top_song_button.grid(row=1, column=2, padx=5, pady=5)  # Add the button in the third column

        except Exception as e:
            messagebox.showinfo("Followed Artists", f"Unexpected Error occurred when loading information for 'Followed Artists': {str(e)}")



    def save_record(self, record):
        """Saves a record to the save list."""
        if record not in self.saved_list:
            self.saved_list.append(record)
            self.update_saved_list()
        else:
            messagebox.showinfo("Saved Songs", f"{record['track_name']} is already in the Save List.")


    def update_saved_list(self):
        """Updates the display of saved records in the save list section."""
        # Clear existing content in the frame
        for widget in self.saved_list_content_frame.winfo_children():
            widget.destroy()

        if not self.saved_list:
            # Display a message if no saved songs are available
            no_saved_label = tk.Label(self.saved_list_content_frame, text="No saved songs yet.")
            no_saved_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
            return

        try:
            # Update the save list label with the total count
            self.saved_list_label.config(text=f"Saved Songs ({len(self.saved_list)} in total)")

            # Iterate through saved songs and display details
            for index, record in enumerate(self.saved_list):
                # Validate the presence of required keys
                if 'track_name' not in record or 'artist_list' not in record or 'track_duration' not in record:
                    raise KeyError("A required key ('track_name', 'artist_list', 'track_duration') is missing in the record.")
                
                # Validate that 'artist_name' is a list of strings
                if not isinstance(record['artist_list'], list):
                    raise TypeError("The 'artist_list' field should be a list of strings.")

                # Create a frame for each saved record
                record_frame = tk.Frame(self.saved_list_content_frame)
                record_frame.grid(row=index, column=0, padx=5, pady=10, sticky="w")
                self.saved_list_content_frame.grid_rowconfigure(index, weight=1)  # Ensure row can expand

                # Display song details
                song_details = tk.Label(
                    record_frame, 
                    text=(
                        f"Track: {record['track_name']}\n"
                        f"Artist(s): {', '.join(artist['name'] for artist in record['artist_list'])}\n"
                        f"Duration: {format_duration(record['track_duration'])}"
                    ),
                    anchor="w", justify="left", wraplength=200
                )
                song_details.grid(row=0, column=0, columnspan=3, sticky="w")

                # Add "Details" button for the saved song
                details_button = ttk.Button(record_frame, text="Details", command=lambda r=record: self.show_details(r['track_id'], 'track_details'))
                details_button.grid(row=1, column=0, padx=5, pady=(5, 10), sticky="ew")

                # Add "Remove" button for the saved song
                delete_button = ttk.Button(record_frame, text="Remove", command=lambda r=record: self.handle_clicks(r['track_id'], "remove", "track"))
                delete_button.grid(row=1, column=1, padx=5, pady=(5, 10), sticky="ew")

                # Add "Play" button for the saved song
                play_button = ttk.Button(record_frame, text="Play", command=lambda r=record: self.open_playback_console(r['track_id']))
                play_button.grid(row=1, column=2, padx=5, pady=(5, 10), sticky="ew")

            # # Optional: Add scrollbar if the list grows too large
            # self.add_scrollbar_if_needed()

        except KeyError as ke:
            messagebox.showinfo("Saved Songs", f"KeyError: {str(ke)}")
            traceback.print_exc()
        except TypeError as te:
            messagebox.showinfo("Saved Songs", f"TypeError: {str(te)}")
            traceback.print_exc()
        except Exception as e:
            messagebox.showinfo("Saved Songs", f"Unexpected error occurred: {str(e)}")
            traceback.print_exc()  # Print the full traceback for debugging in the console


    def show_details(self, item_id, category):
        """Displays detailed information about a track or artist in the central details section."""
        # Clear the current content of the details frame
        for widget in self.details_frame.winfo_children():
            widget.destroy()

        # Display the details dynamically
        if category == "track_details":
            record = get_track_info(self.token, item_id)
            artist_list = record.get('artist_list', [])
            print(f"artist_list: {record['artist_list']}")
            artist_names = ', '.join([artist.get('name', 'N/A') for artist in artist_list])
            print(f"artist_names: {artist_names}")
            
            ttk.Label(self.details_frame, text=f"Track Details", font=("Arial", 14, "bold")).grid(row=0, column=0, pady=(0, 10), sticky="w")
            ttk.Label(self.details_frame, text=f"Track Name: {record['track_name']}").grid(row=1, column=0, sticky="w")
            ttk.Label(self.details_frame, text=f"Album: {record['album']}").grid(row=2, column=0, sticky="w")
            ttk.Label(self.details_frame, text=f"Artist(s): {artist_names if artist_names else 'N/A'}").grid(row=3, column=0, sticky="w")
            ttk.Label(self.details_frame, text=f"Popularity of The Track: {record['popularity']}").grid(row=4, column=0, sticky="w")

        elif category == "artist_details":
            record = get_artist_info(self.token, item_id)
            try:
                image_stream = record['image_info']

                # Open the image using Pillow directly from the byte stream
                pil_image = Image.open(image_stream)
                pil_image = pil_image.resize((300, 300))  # Resize image to 300x300

                # Convert the image to a format suitable for Tkinter
                tk_image = ImageTk.PhotoImage(pil_image)

                # Display the image in a Label within the details frame
                image_label = ttk.Label(self.details_frame, image=tk_image)
                image_label.image = tk_image  # Keep a reference to avoid garbage collection
                image_label.grid(row=0, column=0, rowspan=5, padx=10, pady=10, sticky="nw")  # Align image to top-left

            except KeyError:
                # Handle case where 'image_info' is missing
                error_label = ttk.Label(self.details_frame, text="Error: No image available", foreground="red")
                error_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            except Exception as e:
                # Handle other exceptions (e.g., image processing errors)
                error_label = ttk.Label(self.details_frame, text=f"Error loading image: {e}", foreground="red")
                error_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

            # Display artist details to the right of the image
            ttk.Label(self.details_frame, text="Artist Details", font=("Arial", 14, "bold")).grid(
                row=0, column=1, sticky="w", padx=10, pady=(10, 5)
            )
            ttk.Label(self.details_frame, text=f"Artist Name: {record['artist_name']}").grid(
                row=1, column=1, sticky="w", padx=10, pady=2
            )
            ttk.Label(self.details_frame, text=f"Genre: {', '.join(gen for gen in record['genres'])}").grid(
                row=2, column=1, sticky="w", padx=10, pady=2
            )
            ttk.Label(self.details_frame, text=f"Followers: {format_number_display(record['followers'])}").grid(
                row=3, column=1, sticky="w", padx=10, pady=2
            )
            ttk.Label(self.details_frame, text=f"Popularity of the Artist: {record['popularity']}").grid(
                row=4, column=1, sticky="w", padx=10, pady=2
            )

        # Add additional details below
        ttk.Label(self.details_frame, text=f"Additional Info: {record.get('additional_info', 'N/A')}").grid(
            row=5, column=0, sticky="w", padx=10, pady=5
        )


        # # Add additional details if necessary
        # ttk.Label(self.details_frame, text=f"Additional Info: {record.get('additional_info', 'N/A')}").grid(row=7, column=0, sticky="w", padx=5, pady=5)




    # def show_details(self, record, detail_type):
    #     """Shows a popup window with the details of the selected record."""
    #     # Create the details window
    #     details_window = tk.Toplevel(self.root)
    #     details_window.title(detail_type)

    #     # Create a scrollable text widget for displaying the details
    #     details_text = tk.Text(details_window, height=10, width=50)
    #     details_text.config(state=tk.DISABLED)  # Set to disabled so it cannot be edited
    #     # print(f"record: {record}")

    #     if detail_type.lower() == "track_details":
    #         artist_list = record.get('artist_list', [])
    #         artist_names = ', '.join([artist.get('artist_name', 'N/A') for artist in artist_list])
    #         track_details = (
    #             f"Details of the Song:\n"
    #             f"Track: {record.get('track_name', 'N/A')}\n"
    #             f"Track Popularity: {record.get('popularity', 'N/A')}\n"
    #             f"Artist(s): {artist_names if artist_names else 'N/A'}\n"
    #             f"Album: {record.get('album', 'N/A')}\n"
    #             f"Release Date: {record.get('release_date', 'N/A')}\n"
    #         )
    #         # print(f"track_details: {track_details}")
    #         details_text.config(state=tk.NORMAL)  # Enable text widget to insert the details
    #         details_text.insert(tk.END, track_details)
        
    #     elif detail_type.lower() == "artist_details":
    #         # Retrieve artist names from 'artist_list' (a list of dictionaries)
    #         artist_details = (
    #             f"Details of the Artist:\n"
    #             f"Artist: {record['artist_name']}\n"
    #             f"Followers: {record.get('followers', 'N/A')}\n"
    #             f"Genres: {', '.join(record.get('genres', []))}\n"
    #             f"Popularity: {record.get('popularity', 'N/A')}\n"
    #         )
    #         details_text.config(state=tk.NORMAL)  # Enable text widget to insert the details
    #         details_text.insert(tk.END, artist_details)
        
    #     # Pack the details text widget in the window
    #     details_text.pack(padx=10, pady=10)

    #     # Optional: Add a close button for the details window
    #     close_button = tk.Button(details_window, text="Close", command=details_window.destroy)
    #     close_button.pack(pady=5)


    def update_navigation_buttons(self, total_pages):
        """Update the state of the navigation buttons (Previous/Next)."""

        # Disable 'Previous' if we are on the first page
        self.prev_button.config(state=tk.DISABLED if self.current_page == 1 else tk.NORMAL)
        
        # Disable 'Next' if we are on the last page
        self.next_button.config(state=tk.DISABLED if self.current_page == total_pages else tk.NORMAL)


    def prev_page(self, total_pages):
        """Moves to the previous page of search results."""
        if self.current_page > 1:
            self.current_page -= 1
            self.display_results()
            self.update_navigation_buttons(total_pages)

    def next_page(self, total_pages):
        """Moves to the next page of search results."""
        if self.current_page < 10:
            self.current_page += 1
            self.display_results()
            self.update_navigation_buttons(total_pages)

    def handle_clicks(self, id, action_type, obj):
        # Determine whether the action is to "follow", "save", "unfollow" or "remove"
        print(f"action_type: {action_type}, obj = {obj}")
        action = self.get_action(action_type, obj)
        # print(action)


        if action:
            success = action(self.token, id)  # Perform the action (save/follow/unfollow/remove)
            print(f"success: {success}, id: {id}")

            if success:
                print("Waiting for server update...")

                # Refresh the appropriate list based on the action
                if action_type== "follow" or action_type== "unfollow":
                    self.results_frame.after(200, self.refresh_followed_list)  # Refresh save list after 1 second
                elif action_type == "add" or action_type == "remove":
                    self.results_frame.after(200, self.refresh_saved_list)  # Refresh followed list after 1 second
            else:
                print(f"Failed to accomplish the task, the action of {action_type} is not refreshed.")
                messagebox.showerror("Error", "Unexpected error: Failed to save the track")
        else:
            print("Invalid action or type")
            messagebox.showerror("Error", "Invalid action type")


    def get_action(self, action_type, obj):
        """
        Determines the correct action based on the action_type and obj and returns the corresponding function.
        """
        if obj == "artist":
            if action_type == "follow":
                return follow_artist  # Return follow artist function for artist
            elif action_type == "unfollow":
                return unfollow_artist  # Return unfollow artist function for artist
            
        elif obj == "track":
            if action_type == "add":
                return save_track  # Return save track function for non-artist
            elif action_type == "remove":
                return remove_track  # Return remove track function for non-artist

        # Return None if action_type is invalid or obj doesn't match expected values
        return None


    def create_artist_selector(self, artist_list):
        """Opens a new window with a dropdown for selecting an artist to follow."""
        if not artist_list:
            print("No artists available for selection.")
            # Optionally, you could display a message to the user here as well
            return

        # Create a new window
        selector_window = Toplevel(self.topSongs_frame)  # Use topSongs_frame for parent window
        selector_window.title("Select Artist to Follow")
        selector_window.geometry("300x200")

        # Label
        ttk.Label(selector_window, text="Select an artist to follow:").pack(pady=10)

        # Create artist names list, checking if each artist has 'name' and 'id'
        artist_names = []
        for artist in artist_list:
            if 'name' in artist and 'id' in artist:
                artist_names.append(artist['name'])
            else:
                print(f"Warning: Artist data missing 'name' or 'id' for {artist}")

        if not artist_names:
            ttk.Label(selector_window, text="No valid artists to display.").pack(pady=10)
            return

        # Set up the dropdown list for artist names
        selected_artist = tk.StringVar()
        artist_dropdown = ttk.Combobox(selector_window, textvariable=selected_artist, values=artist_names)
        artist_dropdown.pack(pady=10)
        artist_dropdown.set("Choose an artist")  # Placeholder text

        # Add a button to confirm artist selection
        def on_select_artist():
            selected = selected_artist.get()
            if selected != "Choose an artist":
                # Find the artist ID based on the selected name
                selected_artist_data = next(
                    (artist for artist in artist_list if artist['name'] == selected), None)
                if selected_artist_data:
                    self.update_topSongs(selected_artist_data['id'], selected_artist_data['name'])
                    selector_window.destroy()

        select_button = ttk.Button(selector_window, text="Click to View Top Songs", command=on_select_artist)
        select_button.pack(pady=10)


        # Follow button
        def follow_selected_artist():
            artist_index = artist_dropdown.current()
            if artist_index == -1:
                # No artist selected
                messagebox.showwarning("Selection Error", "Please select an artist to follow.")
                return
            
            artist_id = artist_list[artist_index]['id']
            self.handle_clicks(artist_id, "follow", "artist")  # Call the follow function

        ttk.Button(selector_window, text="Follow", command=follow_selected_artist).pack(pady=10)

    def refresh_saved_list(self):
        self.saved_list = get_user_tracks(self.token)  # Update the saved list
        # print("Saved list refreshed:", self.saved_list)
        self.update_saved_list()  # Call method to refresh the UI if needed

    def refresh_followed_list(self):
        self.followed_list = get_user_followed_artists(self.token)  # Update the saved list
        # print("Saved list refreshed:", self.followed_list)
        self.update_followed_list()  # Call method to refresh the UI if needed


    def fetch_playlists(self):
        """Fetches the user's playlists from Spotify."""
        try:
            playlists = self.sp.current_user_playlists()['items']
            if playlists:
                self.playlists = playlists  # Store playlists for later use
                self.display_playlists(playlists)
            else:
                print("No playlists found.")
        except Exception as e:
            print(f"Error fetching playlists: {e}")

    def display_playlists(self, playlists):
        """Displays the fetched playlists in a Tkinter Listbox."""
        self.playlist_window = tk.Toplevel(self)
        self.playlist_window.title("Your Playlists")
        self.playlist_window.geometry("400x300")

        # Listbox to display the playlist names
        playlist_listbox = tk.Listbox(self.playlist_window, height=10)
        playlist_listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Add playlist names to the Listbox
        for idx, playlist in enumerate(playlists):
            playlist_listbox.insert(tk.END, playlist['name'])
        
        # Add button to play selected playlist
        play_button = tk.Button(self.playlist_window, text="Play Playlist", command=lambda: self.play_playlist(playlist_listbox))
        play_button.pack(pady=10)

    def play_playlist(self, playlist_listbox):
        """Plays the selected playlist."""
        selected_index = playlist_listbox.curselection()
        if selected_index:
            playlist = self.playlists[selected_index[0]]
            playlist_id = playlist['id']
            self.play_tracks_from_playlist(playlist_id)
        else:
            print("No playlist selected.")

    def play_tracks_from_playlist(self, playlist_id):
        """Plays the tracks from a selected playlist."""
        try:
            # Fetch the playlist's tracks
            tracks = self.sp.playlist_tracks(playlist_id)['items']
            if tracks:
                track_uris = [track['track']['uri'] for track in tracks]
                self.play_song(track_uris[0])  # Play the first track (you can change this to play any track)
                print(f"Playing first track from playlist {playlist_id}")
            else:
                print("No tracks in the selected playlist.")
        except Exception as e:
            print(f"Error playing tracks from playlist: {e}")

    def open_playback_console(self, track_id=None):
        """Opens the playback console and optionally starts playing a track."""
        if hasattr(self, 'playback_console') and self.playback_console.winfo_exists():
            self.playback_console.focus()  # Bring the console to focus if already open
            return

        # Launch the console
        self.playback_console = tk.Toplevel(self.root)
        self.playback_console.title("Playback Console")
        self.playback_console.geometry("400x300")

        # Add controls for play, pause, next, previous
        tk.Button(self.playback_console, text="Play", command=lambda: self.play_song(track_id)).pack(pady=10)
        tk.Button(self.playback_console, text="Pause", command=self.pause_song).pack(pady=10)
        tk.Button(self.playback_console, text="Next", command=self.next_track).pack(pady=10)
        tk.Button(self.playback_console, text="Previous", command=self.previous_track).pack(pady=10)

        # Optionally start playback if track_id is provided
        if track_id:
            self.play_song(track_id)

    def play_song(self, track_id):
        """Plays the selected song on the user's preferred device."""
        def _play_song():
            try:
                # Construct the track URI from the track_id
                track_uri = f"spotify:track:{track_id}"

                # Get available devices
                devices = self.sp.devices()['devices']
                if devices:
                    # Print the devices available for playback
                    print("Available devices:")
                    for device in devices:
                        print(f"Device: {device['name']} - {device['type']}")

                    # For simplicity, we're selecting the first device here, but you can implement device selection logic
                    selected_device = devices[0]
                    self.sp.start_playback(device_id=selected_device['id'], uris=[track_uri])
                    print(f"Playing song with track ID: {track_id} and URI: {track_uri} on device {selected_device['name']}")
                else:
                    print("No available devices to play the song on.")
            except Exception as e:
                print(f"Error playing song: {e}")

        threading.Thread(target=_play_song, daemon=True).start()
    def pause_song(self):
        """Pauses the current song."""
        try:
            self.sp.pause_playback()
            print("Song paused.")
        except Exception as e:
            print(f"Error pausing song: {e}")

    def next_track(self):
        """Skips to the next track."""
        try:
            self.sp.next_track()
            print("Moved to the next track.")
        except Exception as e:
            print(f"Error skipping to the next track: {e}")

    def previous_track(self):
        """Moves to the previous track."""
        try:
            self.sp.previous_track()
            print("Moved to the previous track.")
        except Exception as e:
            print(f"Error moving to the previous track: {e}")

    def toggle(self, item_id, button, action_type, is_active):
        """
        Toggle follow/unfollow or add/remove for artists and tracks.
        
        Args:
            item_id (int): The unique ID of the artist or track.
            button (tk.Button): The button to update.
            is_active (bool): Current state (True for active, False for inactive).
            action_type (str): The type of action ('follow' or 'save').
        """
        # Determine which dictionary to update
        # state_dict = self.followed_artists if action_type == "follow" else self.saved_tracks
        
        # # Toggle the state
        # is_active = state_dict.get(item_id, False)  # Default to False if not present
        # state_dict[item_id] = new_state

        
        # Update the button text
        if action_type == "follow":
            is_active = any(artist['artist_id'] == item_id for artist in self.followed_list)
            action = "unfollow" if is_active else "follow"
            self.handle_clicks(item_id, action, "artist")
            new_state = not is_active
            button_text = "Unfollow" if new_state else "Follow"
            print(f"{'Followed' if new_state else 'Unfollowed'} artist with ID {item_id}")
        elif action_type == "save":
            is_active = any(track['track_id'] == item_id for track in self.saved_list)
            action = "remove" if is_active else "add"
            self.handle_clicks(item_id, action, "track")
            new_state = not is_active
            button_text = "Remove" if new_state else "Add"
            print(f"{'Added' if new_state else 'Removed'} track with ID {item_id}")
        
        # Update the button
        button.config(text=button_text)


    
        

# def main():
#     root = tk.Tk()
#     app = SearchInterface(root)
#     root.mainloop()

# if __name__ == "__main__":
#     main()
