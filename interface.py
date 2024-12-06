import tkinter as tk
from tkinter import messagebox, Toplevel, ttk
from playback import PlaybackConsole
import random, os, traceback, spotipy, threading
from spotipy.oauth2 import SpotifyOAuth
from spotipy_api_oauth import (
    get_topsongs_by_artist, 
    search_for_track, 
    search_for_artist, 
    search_for_genre, 
    format_duration, 
    generate_recommendations, 
    get_user_followed_artists,
    follow_artist,
    get_user_tracks,
    save_track,
    remove_track,
    unfollow_artist)


class MainInterface:
    def __init__(self, root, token_manager):
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
        print(f"self.tolen: {self.token}")
        self.sp = spotipy.Spotify(auth=self.token)
        # self.access_token = access_token

        # Initialize category options
        self.categories = ["Not Selected", "Artist", "Track", "Genre"]

        # Sections
        self.create_search_section()
        self.create_save_list_section()
        self.create_recommendation_section()
        self.create_topSongs_section()
        self.create_followed_list_section()  # New section for followed singers
        # self.auto_refresh_recommendations()

    def create_search_section(self):
        self.search_frame = tk.Frame(self.root)
        self.search_frame.grid(row=0, column=1, padx=20, pady=15, sticky="nsew")

        tk.Label(self.search_frame, text="Search Bar").grid(row=0, column=0, padx=3)

        # Search Entry
        self.search_entry = tk.Entry(self.search_frame, width=20)
        self.search_entry.grid(row=0, column=1, padx=4)

        # Category Dropdown
        self.category_var = tk.StringVar()
        self.category_var.set(self.categories[0])  # Default to "Not Selected"
        self.category_menu = tk.OptionMenu(self.search_frame, self.category_var, *self.categories)
        self.category_menu.grid(row=0, column=2, padx=3)

        # Search Button
        self.search_button = tk.Button(self.search_frame, text="Search", command=self.display_results)
        self.search_button.grid(row=0, column=3, padx=3)

        # Results display
        self.results_text = tk.Text(self.search_frame, height=10, width=60)
        self.results_text.insert(tk.END, "Search result is coming on the way.")
        self.results_text.grid(row=1, column=0, columnspan=5, pady=3)

        # Create the Scrollbar widget
        scrollbar = tk.Scrollbar(self.search_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.grid(row=1, column=4, sticky="nsew")  # Use grid instead of pack for the scrollbar

        # Attach the scrollbar to the Text widget
        self.results_text.config(yscrollcommand=scrollbar.set)

        # Pagination controls
        self.prev_button = tk.Button(self.search_frame, text="<< Prev", command=self.prev_page)
        self.prev_button.grid(row=2, column=0, pady=5)


        self.page_label = tk.Label(self.search_frame, text="")
        self.page_label.grid(row=2, column=1)

        self.next_button = tk.Button(self.search_frame, text="Next >>", command=self.next_page)
        self.next_button.grid(row=2, column=2, pady=5)


    def create_save_list_section(self):
        # Save List Frame
        self.save_list_frame = tk.Frame(self.root)
        self.save_list_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.save_list_label = tk.Label(self.save_list_frame, text="Saved Songs")
        self.save_list_label.grid(row=0, column=0, padx=5, sticky="we")

        # Text widget for saved records
        self.save_list_text = tk.Text(self.save_list_frame, height=10, width=30)
        self.save_list_text.grid(row=1, column=0, columnspan=1, pady=5)

        scrollbar = tk.Scrollbar(self.save_list_frame, orient=tk.VERTICAL, command=self.save_list_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")  # Use grid instead of pack for the scrollbar

        self.save_list_text.config(yscrollcommand=scrollbar.set)

        self.update_save_list()

    def create_followed_list_section(self):
        # New section for followed singers
        self.followed_list_frame = tk.Frame(self.root)
        self.followed_list_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.followed_list_label = tk.Label(self.followed_list_frame, text="Followed Singers")
        self.followed_list_label.grid(row=0, column=0, padx=5, sticky="we")

        self.followed_list_text = tk.Text(self.followed_list_frame, height=10, width=30)
        self.followed_list_text.grid(row=1, column=0, columnspan=1, pady=5)

        scrollbar = tk.Scrollbar(self.followed_list_frame, orient=tk.VERTICAL, command=self.followed_list_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")  # Use grid instead of pack for the scrollbar
        self.followed_list_text.config(yscrollcommand=scrollbar.set)

        self.refresh_followed_list()


    def create_recommendation_section(self):
        """Creates the recommendation section with refresh, save, and details features."""
        # Recommendation Frame
        self.recommend_frame = tk.Frame(self.root)
        self.recommend_frame.grid(row=1, column=1, columnspan=1, padx=10, pady=10, sticky="nsew")

        self.recommend_label = tk.Label(self.recommend_frame, text="Recommendations Based on Your Favourite")
        self.recommend_label.pack(pady=1)

        # Frame for the Text widget and Scrollbar
        self.recommend_text_frame = tk.Frame(self.recommend_frame)
        self.recommend_text_frame.pack(pady=5)

        # Create a Text widget for recommendations with enough space to show 5 records
        self.recommend_text = tk.Text(self.recommend_text_frame, height=10, width=45)
        self.recommend_text.pack(side=tk.LEFT, fill=tk.Y)

        # Create the Scrollbar widget
        scrollbar = tk.Scrollbar(self.recommend_text_frame, orient=tk.VERTICAL, command=self.recommend_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Attach the scrollbar to the Text widget
        self.recommend_text.config(yscrollcommand=scrollbar.set)

        # Refresh button
        refresh_button = tk.Button(self.recommend_frame, text="Refresh", command=self.refresh_recommendations)
        refresh_button.pack(pady=5)

        # Initial population of recommendations
        # self.refresh_recommendations()

    def refresh_recommendations(self):
        """Refreshes the recommendations with new items and adds Save and Details buttons for each."""
        self.recommend_text.delete(1.0, tk.END)

        # artist_id_list = [singer['artist_id'] for singer in self.followed_list]
        # track_id_list = [song['track_id'] for song in self.saved_list]
        # genres_list = [gen for singer in self.followed_list if singer['genres'] for gen in singer['genres']]

        # print(track_id_list)
        # print(artist_id_list)
        # print(genres_list)

        recommendations = generate_recommendations(self.token, self.saved_list, self.followed_list)
        if recommendations is None:
            self.recommend_text.insert(tk.END, "No available recommended Songs based on your Favourites.")
        elif not isinstance(recommendations, list):
            print("Recommendations is not a list:", recommendations)
        else:
            print(f"Recommendations: {recommendations}")
            recommendations_sorted = sorted(recommendations, key=lambda x: x["popularity_track"], reverse=True)
        # recommendations = [f"Recommended Record {i+1} - Song {random.randint(100, 999)}" for i in range(10)]

            for index, track in enumerate(recommendations_sorted):
                self.recommend_text.insert(tk.END, f"Top {index+1}:\n Track: {track['track_name']}\n Album - '{track['album']}'\nTrack Duration: {format_duration(track["track_duration"])}\n")

                # Save Button for each recommendation
                save_button = tk.Button(self.recommend_text, text="Save", command=lambda r=track: self.handle_clicks(r["track_id", "save", "non-artist"]))
                self.recommend_text.window_create(tk.END, window=save_button)

                save_button = tk.Button(self.recommend_text, text="Follow", command=lambda r=track: self.create_artist_selector(r["artist_list"]))
                self.recommend_text.window_create(tk.END, window=save_button)


                # Details Button for each recommendation
                details_button = tk.Button(self.recommend_text, text="Details", command=lambda r=track: self.show_details(r, 'track_details'))
                self.recommend_text.window_create(tk.END, window=details_button)

                self.recommend_text.insert(tk.END, "\n")

    def auto_refresh_recommendations(self):
        """Automatically refresh recommendations every 30 seconds."""
        self.refresh_recommendations()
        self.root.after(5000, self.auto_refresh_recommendations)  # 5-second interval for presentation


    def create_topSongs_section(self):
        """Creates the section to display top 10 popular songs."""
        self.topSongs_frame = tk.Frame(self.root)
        self.topSongs_frame.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")

        # Label for Top Songs, will update with the artist's name
        self.topSongs_label = tk.Label(self.topSongs_frame, text="Top Songs")
        self.topSongs_label.grid(row=0, column=0, padx=5, sticky="w")

        # Text widget for displaying top 10 songs
        self.topSongs_text = tk.Text(self.topSongs_frame, height=10, width=30)
        self.topSongs_text.grid(row=1, column=0, columnspan=1, pady=5)

        # Use grid to add a scollbar
        scrollbar = tk.Scrollbar(self.topSongs_frame, orient=tk.VERTICAL, command=self.topSongs_text.yview)
        scrollbar.grid(row=1, column=2, sticky="ns")  
        self.topSongs_text.config(yscrollcommand=scrollbar.set)
        # self.update_topChart()

    def update_topSongs(self, artist_id, artist_name):
        """Updates the display of top chart songs for a specific artist."""
        # Clear the text widget and label before updating
        self.topSongs_text.delete(1.0, tk.END)
        self.topSongs_label.config(text=f"Top 10 Songs by {artist_name}")

        # Retrieve and display the top songs
        songs = get_topsongs_by_artist(self.token, artist_id, "us")
        if songs:
            songs_sorted = sorted(songs, key=lambda x: x["popularity_track"], reverse=True)
            for index, song in enumerate(songs_sorted):
                self.topSongs_text.insert(tk.END, f"Top {index+1}:\n Track: {song['track_name']}\n Album: '{song['album']}'\n Popularity:{song['popularity_track']}\n")

                # Add "Play" button for the saved song
                play_button = tk.Button(self.save_list_text, text="Play", command=lambda r=song: self.open_playback_console(r['track_id']))
                self.save_list_text.window_create(tk.END, window=play_button)


                # Save Button
                self.topSongs_text.window_create(
                    tk.END,
                    window=tk.Button(
                        self.topSongs_text,
                        text="Save",
                        command=lambda r=song: self.handle_clicks(r["track_id"], "save", "track")  # Pass list to save_record function
                    )
                )

                # Follow Button
                self.topSongs_text.window_create(
                    tk.END,
                    window=tk.Button(
                        self.topSongs_text,
                        text="Follow",
                        command=lambda r=song: self.create_artist_selector(r['artist_list'])  # Pass artist list to create_artist_selector
                    )
                )


                # Details Button
                self.topSongs_text.window_create(
                    tk.END,
                    window=tk.Button(
                        self.topSongs_text,
                        text="Details",
                        command=lambda r=song: self.show_details(r, 'track_details')  # Pass list / category to show_details function
                    )
                )

                self.topSongs_text.insert(tk.END, "\n")
        else:
            self.topSongs_text.insert(tk.END, "No top songs available.\n")


    def display_results(self):
        self.results_text.delete(1.0, tk.END)
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
            return self.results_text.insert(tk.END, "Select a category and input a keyword for search.\n")

        # Filter out empty or invalid results
        self.all_results = [result for result in raw_results if result]  # Exclude None or empty results

        # Check if there are no valid results after filtering
        if not self.all_results:
            self.results_text.insert(tk.END, "No valid results found.\n")
            self.page_label.config(text="")  # Clear pagination label
            return

        # Paginate filtered results
        start_idx = (self.current_page - 1) * self.results_per_page
        end_idx = start_idx + self.results_per_page
        results_to_display = self.all_results[start_idx:end_idx]

        for result in results_to_display:
            # Format display text based on category
            if selected_category == "track" or selected_category == "genre":
                display_text = (
                    f"Track: {result['track_name']}\n"
                    f"Album: {result['album']}\n"
                    f"Artist(s): {', '.join(artist['name'] for artist in result['artist_list'])}\n"
                    f"Duration: {format_duration(result['track_duration'])}"
                )
            elif selected_category == "artist":
                display_text = (
                    f"Artist: {result['artist_name']}\n"
                    f"Genres: {', '.join(result['genres'])}\n"
                    f"Popularity: {result['popularity_artist']}"
                )
            else:
                continue

            # Insert formatted text
            self.results_text.insert(tk.END, f"{display_text}\n")

            # Add buttons based on category
            if selected_category == "artist":
                self.results_text.window_create(
                    tk.END,
                    window=tk.Button(
                        self.results_text,
                        text="Details",
                        command=lambda r=result: self.show_details(r, 'artist_details')
                    )
                )
                self.results_text.window_create(
                    tk.END,
                    window=tk.Button(
                        self.results_text,
                        text="Follow",
                        command=lambda r=result: self.handle_clicks(r['artist_id'], "follow", "artist")
                    )
                )
                self.results_text.window_create(
                    tk.END,
                    window=tk.Button(
                        self.results_text,
                        text="Top Songs",
                        command=lambda r=result: self.update_topSongs(r['artist_id'], r['artist_name'])
                    )
                )
            else:
                self.results_text.window_create(
                    tk.END,
                    window=tk.Button(
                        self.results_text,
                        text="Details",
                        command=lambda r=result: self.show_details(r, 'track_details')
                    )
                )
                self.results_text.window_create(
                    tk.END,
                    window=tk.Button(
                        self.results_text,
                        text="Save",
                        command=lambda r=result: self.handle_clicks(r['track_id'], "save", "track")
                    )
                )
                self.results_text.window_create(
                    tk.END,
                    window=tk.Button(
                        self.results_text,
                        text="Artists to Follow",
                        command=lambda r=result: self.create_artist_selector(r['artist_list'])
                    )
                )

            self.results_text.insert(tk.END, "\n")

        # Dynamically calculate total pages based on filtered results
        total_pages = max(1, (len(self.all_results) + self.results_per_page - 1) // self.results_per_page)
        self.page_label.config(text=f"Page {self.current_page}/{total_pages}")



    def follow_singer(self, singer):
        if singer not in self.followed_list:
            self.followed_list.append(singer)
            self.update_followed_list()
        else:
            messagebox.showinfo("Followed Artist(s)", f"{singer['artist_name']} is already followed.")

    def update_followed_list(self):
        self.followed_list_text.delete(1.0, tk.END)
        try:
            # Update the followed list label with the total count
            self.followed_list_label.config(text=f"Followed Singers ({len(self.followed_list)} in total)")

            # Iterate through the followed singers and display their details
            for singer in self.followed_list:
                self.followed_list_text.insert(tk.END, f"Details of the Artist:\n Artist Name: {singer['artist_name']}\n Genres: {', '.join(singer['genres'])}\n")

                # Create a "Details" button for each followed singer
                details_button = tk.Button(self.followed_list_text, text="Details", command=lambda r=singer: self.show_details(r, 'artist_details'))
                self.followed_list_text.window_create(tk.END, window=details_button)

                # Create an "Unfollow" button for each followed singer
                unfollow_button = tk.Button(self.followed_list_text, text="Unfollow", command=lambda s=singer: self.handle_clicks(s['artist_id'], "unfollow", "artist"))
                self.followed_list_text.window_create(tk.END, window=unfollow_button)

                self.followed_list_text.insert(tk.END, "\n")

        except Exception as e:  # Catch specific exception types if needed
            messagebox.showinfo("Followed Artists", f"Unexpected Error occurred when loading information for 'Followed Artists': {str(e)}")



    def save_record(self, record):
        """Saves a record to the save list."""
        if record not in self.saved_list:
            self.saved_list.append(record)
            self.update_save_list()
        else:
            messagebox.showinfo("Saved Songs", f"{record['track_name']} is already in the Save List.")

    def update_save_list(self):
        """Updates the display of saved records."""
        self.save_list_text.delete(1.0, tk.END)
        if not self.saved_list:
            self.save_list_text.insert(tk.END, "No saved songs yet.\n")
            return

        try:
            # Update the save list label with the total count
            self.save_list_label.config(text=f"Saved Songs ({len(self.saved_list)} in total)")

            # Iterate through saved songs and display details
            for record in self.saved_list:
                # Validate the presence of required keys
                if 'track_name' not in record or 'artist_list' not in record or 'track_duration' not in record:
                    raise KeyError("A required key ('track_name', 'artist_list', 'track_duration') is missing in the record.")
                
                # Validate that 'artist_name' is a list of strings
                if not isinstance(record['artist_list'], list):
                    raise TypeError("The 'artist_name' field should be a list of strings.")

                # Format and display the saved record
                self.save_list_text.insert(
                    tk.END,
                    f"Track: {record['track_name']}\n"
                    f"Artist(s): {', '.join(artist['name'] for artist in record['artist_list'])}\n"
                    f"Duration: {format_duration(record['track_duration'])}\n"
                )

                # Add "Details" button for the saved song
                details_button = tk.Button(self.save_list_text, text="Details", command=lambda r=record: self.show_details(r, 'track_details'))
                self.save_list_text.window_create(tk.END, window=details_button)

                # Add "Delete" button for the saved song
                delete_button = tk.Button(self.save_list_text, text="Delete", command=lambda r=record: self.handle_clicks(r['track_id'], "remove", "track"))
                self.save_list_text.window_create(tk.END, window=delete_button)

                # Add "Play" button for the saved song
                play_button = tk.Button(self.save_list_text, text="Play", command=lambda r=record: self.open_playback_console(r['track_id']))
                self.save_list_text.window_create(tk.END, window=play_button)

                self.save_list_text.insert(tk.END, "\n")
        
        except KeyError as ke:
            messagebox.showinfo("Saved Songs", f"KeyError: {str(ke)}")
            traceback.print_exc()
        except TypeError as te:
            messagebox.showinfo("Saved Songs", f"TypeError: {str(te)}")
            traceback.print_exc()
        except Exception as e:
            messagebox.showinfo("Saved Songs", f"Unexpected error occurred: {str(e)}")
            traceback.print_exc()  # Print the full traceback for debugging in the console


    def show_details(self, record, detail_type):
        """Shows a popup window with the details of the selected record."""
        # Create the details window
        details_window = tk.Toplevel(self.root)
        details_window.title(detail_type)

        # Create a scrollable text widget for displaying the details
        details_text = tk.Text(details_window, height=10, width=50)
        details_text.config(state=tk.DISABLED)  # Set to disabled so it cannot be edited
        print(f"record: {record}")

        if detail_type.lower() == "track_details":
            artist_list = record.get('artist_list', [])
            artist_names = ', '.join([artist.get('artist_name', 'N/A') for artist in artist_list])
            track_details = (
                f"Details of the Song:\n"
                f"Track: {record.get('track_name', 'N/A')}\n"
                f"Track Popularity: {record.get('popularity_track', 'N/A')}\n"
                f"Artist(s): {artist_names if artist_names else 'N/A'}\n"
                f"Album: {record.get('album', 'N/A')}\n"
                f"Release Date: {record.get('release_date', 'N/A')}\n"
            )
            print(f"track_details: {track_details}")
            details_text.config(state=tk.NORMAL)  # Enable text widget to insert the details
            details_text.insert(tk.END, track_details)
        
        elif detail_type.lower() == "artist_details":
            # Retrieve artist names from 'artist_list' (a list of dictionaries)
            artist_details = (
                f"Details of the Artist:\n"
                f"Artist: {record['artist_name']}\n"
                f"Followers: {record.get('followers', 'N/A')}\n"
                f"Genres: {', '.join(record.get('genres', []))}\n"
                f"Popularity: {record.get('popularity_artist', 'N/A')}\n"
            )
            details_text.config(state=tk.NORMAL)  # Enable text widget to insert the details
            details_text.insert(tk.END, artist_details)
        
        # Pack the details text widget in the window
        details_text.pack(padx=10, pady=10)

        # Optional: Add a close button for the details window
        close_button = tk.Button(details_window, text="Close", command=details_window.destroy)
        close_button.pack(pady=5)





    def prev_page(self):
        """Moves to the previous page of search results."""
        if self.current_page > 1:
            self.current_page -= 1
            self.display_results()

    def next_page(self):
        """Moves to the next page of search results."""
        if self.current_page < 10:
            self.current_page += 1
            self.display_results()

    def handle_clicks(self, id, action_type, obj):
        # Determine whether the action is to "follow", "save", "unfollow" or "remove"
        print(f"action_type: {action_type}, obj = {obj}")
        action = self.get_action(action_type, obj)
        print(action)


        if action:
            success = action(self.token, id)  # Perform the action (save/follow/unfollow/remove)

            if success:
                print("Waiting for server update...")

                # Refresh the appropriate list based on the action
                if action_type== "follow" or action_type== "unfollow":
                    self.results_text.after(200, self.refresh_followed_list)  # Refresh save list after 1 second
                elif action_type == "save" or action_type == "remove":
                    self.results_text.after(200, self.refresh_saved_list)  # Refresh followed list after 1 second
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
            if action_type == "save":
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
        selector_window = Toplevel(self.topSongs_text)
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
        print("Saved list refreshed:", self.saved_list)
        self.update_save_list()  # Call method to refresh the UI if needed

    def refresh_followed_list(self):
        self.followed_list = get_user_followed_artists(self.token)  # Update the saved list
        print("Saved list refreshed:", self.followed_list)
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


# def main():
#     root = tk.Tk()
#     app = SearchInterface(root)
#     root.mainloop()

# if __name__ == "__main__":
#     main()