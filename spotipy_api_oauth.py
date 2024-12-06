from dotenv import load_dotenv
import os, base64, json, random, requests, asyncio, threading
from requests import post, get, put
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from tkinter import ttk, messagebox
import tkinter as tk
from flask import Flask, request, jsonify, session
import requests, webbrowser, threading, urllib, os, queue
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import set_key, load_dotenv
from datetime import datetime
from time import sleep

load_dotenv()

CLIENT_ID = "122ec5036ce84b249e67cfe3300e0808"
CLIENT_SECRET = "0ad7a7f6b2bb4d898b5acaa5ceb7cb85"
REDIRECT_URI = "http://localhost:5000/callback"
SCOPES = "user-read-private user-read-email playlist-read-private user-follow-read user-follow-modify user-library-read user-library-modify"
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

#get token by sending id and secrets following Spotify authorization Code Flow
# def get_token(client_id, client_secret):
#     auth_string = client_id + ":" + client_secret
#     auth_bytes = auth_string.encode("utf-8")
#     auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
#     #
#     url = "https://accounts.spotify.com/api/token"
#     headers = {
#         "Authorization": "Basic " + auth_base64,
#         "Content-Type": "application/x-www-form-urlencoded"
#     }

#     data = {"grant_type": "client_credentials"}

#     result = post(url, headers=headers, data=data)
#     #recevei the json data
#     json_result = json.loads(result.content)
#     print(json_result)
#     try:
#         token = json_result["access_token"]
#         os.environ["ACCESS_TOKEN"] = token
#         return token
#     except KeyError:
#         return None

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def search_for_track(token, track_name, limit=50):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q=track:{track_name}&type=track&limit={limit}&market=US"
    query_url = url + query
    result = get(query_url, headers=headers)
    try:
        json_result = json.loads(result.content)["tracks"]["items"]
        # print(json_result)  # Add this line to inspect the response structure
        revised_json_result = []
        for i in range(len(json_result)):
            track_data = {
                "track_id": json_result[i]["id"],
                "track_name": json_result[i]["name"],
                "track_duration" : json_result[i]["duration_ms"],
                "album": json_result[i]["album"]["name"],
                "release_date": json_result[i]["album"]["release_date"],
                "popularity_track": json_result[i]["popularity"],
                "artist_list":json_result[i]["artists"],  # Collect all artist id
                "genres": []
                }
            revised_json_result.append(track_data)  # Append the track data to the revised list
        return revised_json_result  # Check if "tracks" exists here
    except KeyError:
        print("Error: 'tracks' key not found in response")
        return []

def search_for_artist(token, artist_name, limit=50):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q=artist:{artist_name}&type=artist&limit={limit}&market=US"
    query_url = url + query
    result = get(query_url, headers=headers)
    try:
        json_result = json.loads(result.content)["artists"]["items"]
        # print(json_result)  # Add this line to inspect the response structure
        revised_json_result = []
        for i in range(len(json_result)):
            artist_data = {
                "artist_id": json_result[i]["id"],
                "artist_name": json_result[i]["name"],
                "followers": json_result[i]["followers"]['total'],
                "genres": [genres for genres in json_result[i]["genres"]],  # Collect all genres
                "popularity_artist": json_result[i]["popularity"]
            }
            revised_json_result.append(artist_data)  # Append the track data to the revised list
        return revised_json_result  # Check if "tracks" exists here
    except KeyError:
        print("Error: 'artist' key not found in response")
        return []


def search_for_genre(token, genre, limit=50):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q=genre:{genre}&type=track&limit={limit}&market=US"
    query_url = url + query
    result = get(query_url, headers=headers)
    try:
        json_result = json.loads(result.content)["tracks"]["items"]
        # print(json_result)  # Add this line to inspect the response structure
        revised_json_result = []
        for i in range(len(json_result)):
            genre_data = {
                "track_id": json_result[i]["id"],
                "track_name": json_result[i]["name"],
                "track_duration" : json_result[i]["duration_ms"],
                "album": json_result[i]["album"]["name"],
                "release_date": json_result[i]["album"]["release_date"],
                "popularity_track": json_result[i]["popularity"],
                "artist_list":json_result[i]["artists"],  # Collect all artist id
                "genres": []
            }
            revised_json_result.append(genre_data)  # Append the track data to the revised list
        return revised_json_result  # Check if "tracks" exists here
    except KeyError:
        print("Error: 'genre' key not found in response")
        return []


def get_topsongs_by_artist(token, artist_id, country="us"):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market={country}"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)['tracks']

    try:
        # print(json_result)  # Add this line to inspect the response structure
        revised_json_result = []
        for i in range(len(json_result)):
            track_data = {
                "track_id": json_result[i]["id"],
                "track_name": json_result[i]["name"],
                "track_duration" : json_result[i]["duration_ms"],
                "album": json_result[i]["album"]["name"],
                "release_date": json_result[i]["album"]["release_date"],
                "popularity_track": json_result[i]["popularity"],
                "artist_list":json_result[i]["artists"],  # Collect all artist id
                "genres": []
            }
            revised_json_result.append(track_data)  # Append the track data to the revised list
        return revised_json_result  # Check if "tracks" exists here
    except KeyError:
        print("Error: 'tracks' key not found in response")
        return []
    
def get_artist_info(token, artist_id):
    url = API_BASE_URL + f"/artists/{artist_id}"
    headers = get_auth_header(token)
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching artist info: {response.status_code}")
        return None

    artist_data = response.json()
    return {
        "artist_id": artist_data["id"],
        "artist_name": artist_data["name"],
        "genres": artist_data.get("genres", []),
    }

def generate_recommendations(token, save_list, follow_list, limit=10):
    """
    Optimized function to generate music recommendations.
    """
    genre_pool = set()
    save_track_ids = {track["track_id"] for track in save_list}
    unique_artist_ids = set()

    # Cache artist info to avoid duplicate API calls
    artist_cache = {}

    def fetch_artist_info(artist_id):
        if artist_id not in artist_cache:
            artist_cache[artist_id] = get_artist_info(token, artist_id)  # API call
        return artist_cache[artist_id]

    # Collect artist IDs and genres from save_list and follow_list
    for track in save_list:
        for artist in track["artist_list"]:
            artist_id = artist["id"]
            unique_artist_ids.add(artist_id)
            artist_info = fetch_artist_info(artist_id)
            if artist_info and "genres" in artist_info:
                genre_pool.update(artist_info["genres"])

    for artist in follow_list:
        artist_id = artist["artist_id"]
        unique_artist_ids.add(artist_id)
        if "genres" in artist:
            genre_pool.update(artist["genres"])

    # Fetch top tracks for each artist
    def fetch_top_tracks(artist_id):
        return get_topsongs_by_artist(token, artist_id)

    # Fetch tracks by genres
    def fetch_tracks_by_genre(token, genre, limit=10):
        """
        Fetch tracks by genre with a specified limit to reduce processing time.
        
        :param token: The API authorization token.
        :param genre: The genre to search for tracks.
        :param limit: The maximum number of tracks to fetch (default is 10).
        :return: A list of tracks for the given genre.
        """
        try:
            # Call the API to search tracks by genre with a limit
            response = search_for_genre(token, genre, limit=limit)
            if response and isinstance(response, list):
                return response  # Return the list of tracks directly
            else:
                print(f"No tracks found for genre: {genre}")
                return []
        except Exception as e:
            print(f"Error fetching tracks for genre {genre}: {e}")
            return []

    # Asynchronous fetching
    async def gather_recommendations():
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()

            # Fetch top tracks by artist
            artist_tasks = [
                loop.run_in_executor(executor, fetch_top_tracks, artist_id)
                for artist_id in unique_artist_ids
            ]

            # Fetch tracks by genre
            genre_tasks = [
                loop.run_in_executor(executor, fetch_tracks_by_genre, genre, 10)
                for genre in genre_pool
            ]

            # Gather all results
            artist_tracks = await asyncio.gather(*artist_tasks)
            genre_tracks = await asyncio.gather(*genre_tasks)

            # Flatten the lists
            all_tracks = [
                track
                for track_list in artist_tracks + genre_tracks
                for track in track_list
            ]

            return all_tracks

    # Run the async function to fetch recommendations
    all_tracks = asyncio.run(gather_recommendations())

    # Filter out duplicates and tracks already in save_list
    unique_recommendations = {
        track["track_id"]: track for track in all_tracks if track["track_id"] not in save_track_ids
    }

    # Shuffle and limit results
    final_recommendations = list(unique_recommendations.values())
    random.shuffle(final_recommendations)

    return final_recommendations[:limit]

# def get_recommendations(token, seed_artist=None, seed_genre=None, seed_track=None):
#     url = "https://api.spotify.com/v1/recommendations?"

#     # Pick a random seed from the lists if provided
#     limited_seed_artist = random.sample(seed_artist, 1) if seed_artist else []
#     limited_seed_genre = random.sample(seed_genre, 1) if seed_genre else []
#     limited_seed_track = random.sample(seed_track, 1) if seed_track else []

#     # Check if all seed inputs are empty
#     if not (limited_seed_artist or limited_seed_genre or limited_seed_track):
#         print("All seeds are empty!")
#         return False

#     # Append query parameters for the API request
#     # if limited_seed_artist:
#     #     url += f"&seed_artists={','.join(limited_seed_artist)}"
#     if limited_seed_genre:
#         url += f"&seed_genres={','.join(limited_seed_genre)}"
#     # if limited_seed_track:
#     #     url += f"&seed_tracks={','.join(limited_seed_track)}"

#     headers = get_auth_header(token)
#     print(f"url: {url}")
#     # Send the GET request to Spotify API
#     result = requests.get(url, headers=headers)  # Assuming `get` is a wrapper for `requests.get`
    
#     # Debugging: Print status code and raw response content
#     print(f"Response Status Code: {result.status_code}")
#     print(f"Response Content: {result.content}")
    
#     # Check if the response is successful
#     if result.status_code != 200:
#         print("Error: API request failed!")
#         return False
    
#     try:
#         # Attempt to parse the response JSON
#         json_result = json.loads(result.content)['tracks']
#         print(json_result)  # Debugging: Print the raw JSON data

#         revised_json_result = []
#         for track in json_result:
#             recommended_data = {
#                 "track_id": track["id"],
#                 "track_name": track["name"],
#                 "track_duration": track["duration_ms"],
#                 "album": track["album"]["name"],
#                 "release_date": track["album"]["release_date"],
#                 "popularity_track": track["popularity"],
#                 "artist_list": track["artists"]  # Collect all artist IDs and names
#             }
#             revised_json_result.append(recommended_data)
        
#         print(f"revised_json_result: {revised_json_result}")
#         return revised_json_result
#     except KeyError:
#         print("Error: 'tracks' key not found in response")
#         return False
#     except json.JSONDecodeError:
#         print("Error: Invalid JSON response")
#         return False

# Helper function to get authorization header (for reference)
def get_auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def get_user_tracks(token):
    headers = get_auth_header(token)
    response = requests.get(API_BASE_URL+"/me/tracks", headers=headers)
    try:
        user_tracks = response.json()["items"]
        # print(json_result)  # Add this line to inspect the response structure
        print(f"user_tracks:\n{user_tracks}")
        revised_json_result = []
        for track in user_tracks:
            print("Starting track loop")
            track_data = {
                "track_id": track["track"]["id"],
                "track_name": track["track"]["name"],
                "track_duration" : track["track"]["duration_ms"],
                "album": track["track"]["album"]["name"],
                "release_date": track["track"]["album"]["release_date"],
                "popularity_track": track["track"]["popularity"],
                "artist_list":track["track"]["artists"],  # Collect all artist id
                "genres": []
                }
            revised_json_result.append(track_data)  # Append the track data to the revised list
            print(f"revised_json_result: {revised_json_result}")
        return revised_json_result  # Check if "tracks" exists here
    except KeyError:
        print("Error: 'tracks' key not found in response")
        return []


def get_user_followed_artists(token):
    headers = get_auth_header(token)
    response = requests.get(API_BASE_URL+"/me/following?type=artist", headers=headers)
    
    try:
        followed_artists = response.json()["artists"]["items"]
        print(f"followed Artist: {followed_artists}")
        # print(json_result)  # Add this line to inspect the response structure
        revised_json_result = []
        for artist in followed_artists:
            artist_data = {
                "artist_id": artist["id"],
                "artist_name": artist["name"],
                "followers": artist["followers"]['total'],
                "genres": [genres for genres in artist["genres"]],  # Collect all genres
                "popularity_artist": artist["popularity"]
            }
            revised_json_result.append(artist_data)  # Append the track data to the revised list
        return revised_json_result  # Check if "tracks" exists here
    except KeyError:
        print("Error: 'artists' key not found in response")
        return []
    

def follow_artist(token, artist_id):
    print("Launching follow_artist()")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "type": "artist"
    }
    data = {
        "ids": [artist_id]  # Corrected from set to list
    }
    try:
        response = requests.put(API_BASE_URL + "/me/following", headers=headers, params=params, json=data)
        print(f"HTTP response received: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error during requests.put: {e}")
        return {"status": "error", "message": "Request failed."}

    if response.status_code == 204:
        print("Followed artist successfully.")
        return True
    elif response.status_code == 401:
        print("Invalid or expired token.")
        # return {"status": "error", "message": "Invalid or expired token."}
    elif response.status_code == 403:
        print("Permission denied.")
        # return {"status": "error", "message": "Permission denied. Check your token's scope."}
    else:
        print(f"Failed to follow artist. Response: {response.text}")
    
    return False

def unfollow_artist(token, artist_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "type": "artist"
    }
    data = {
        "ids": [artist_id]  # Corrected from set to list
    }
    try:
        response = requests.delete(API_BASE_URL + "/me/following", headers=headers, params=params, json=data)
        print(f"HTTP response received: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error during requests.put: {e}")
        return {"status": "error", "message": "Request failed."}

    if response.status_code == 204:
        print("Unfollowed artist successfully.")
        return True
    elif response.status_code == 401:
        print("Invalid or expired token.")
        # return {"status": "error", "message": "Invalid or expired token."}
    elif response.status_code == 403:
        print("Permission denied.")
        # return {"status": "error", "message": "Permission denied. Check your token's scope."}
    else:
        print(f"Failed to unfollow artist. Response: {response.text}")
    
    return False


def save_track(token, track_id):
    print("Launching save_track()")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "ids": [track_id]  # Corrected from set to list
    }
    
    try:
        response = requests.put(API_BASE_URL + "/me/tracks", headers=headers, json=data)
        print(f"HTTP response received: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error during requests.put: {e}")
        return {"status": "error", "message": "Request failed."}

    if response.status_code == 200:
        print("Track saved successfully.")
        return True
    elif response.status_code == 401:
        print("Invalid or expired token.")
        # return {"status": "error", "message": "Invalid or expired token."}
    elif response.status_code == 403:
        print("Permission denied.")
        # return {"status": "error", "message": "Permission denied. Check your token's scope."}
    else:
        print(f"Failed to save track. Response: {response.text}")
    
    return False

def remove_track(token, track_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "ids": [track_id]  # Corrected from set to list
    }
    
    try:
        response = requests.delete(API_BASE_URL + "/me/tracks", headers=headers, json=data)
    except requests.exceptions.RequestException as e:
        print(f"Error during requests.put: {e}")
        return {"status": "error", "message": "Request failed."}

    if response.status_code == 200:
        print("Track deleted successfully.")
        return True
    elif response.status_code == 401:
        print("Invalid or expired token.")
        # return {"status": "error", "message": "Invalid or expired token."}
    elif response.status_code == 403:
        print("Permission denied.")
        # return {"status": "error", "message": "Permission denied. Check your token's scope."}
    else:
        print(f"Failed to save track. Response: {response.text}")
    
    return False

def format_duration(duration_ms):
    # Convert milliseconds to seconds
    total_seconds = duration_ms // 1000
    # Calculate minutes and seconds
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    # Format as "xx minutes xx seconds"
    return f"{minutes}(m):{seconds}(s)"

# token = get_token()
# result = get_recommendations(token, seed_artist="4NHQUGzhtTLFvgF5SZesLK", seed_genre=None, seed_track=None)
# print(result.status_code)
# print(result.text)

# for i in range(10):
#     song = result[i]
#     for j in range(len(song["artists"])):
#         print(f"{i + 1}. {song["artists"][j]["name"]} from Album - '{song["album"]["name"]}'")

# for i in range(10):
#     artist_id = result[i]["id"]
#     songs = get_topsongs_by_artist(token, artist_id, "US")

# for index, song in enumerate(songs):
#     print(f"{index + 1}. {song["name"]} from Album - '{song["album"]["name"]}'")