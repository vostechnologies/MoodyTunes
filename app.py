import json
from flask import Flask, render_template, session, jsonify, Response, request
from dotenv import load_dotenv
import os
import base64
from requests import post, get
import sqlite3
import time
from camera import *

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

app = Flask(__name__)
global token, emotion

# Database Connection
connect = sqlite3.connect('database.db')
connect.execute('CREATE TABLE IF NOT EXISTS EMOTIONS(user TEXT, emotion TEXT)')

# Detection Section
headings = ("Name", "Album", "Artist")
df1 = music_rec()
df1 = df1.head(15)


# Video Camera Functions
def gen(camera):
    while True:
        global df1
        frame, df1, emotion = camera.get_frame()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def genFrame(camera):
    global df1
    frame, df1, emotion = camera.get_frame()
    camera.stop_feed()
    yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


# Spotify Fetching
def get_token():
    auth_string = f"{client_id}:{client_secret}"
    auth_base64 = str(base64.b64encode(auth_string.encode("utf-8")), "utf-8")
    url = "https://accounts.spotify.com/api/token"
    headers ={
        "Authorization":"Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }

    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_headers(token):
    return {"Authorization": "Bearer " + token}

def get_user_details():
    url="https://api.spotify.com/v1/search"
    headers = {"Authorization": "Bearer " + get_token()}
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result

def get_songs_for_category(category, limit):
    url="https://api.spotify.com/v1/search"
    headers = {"Authorization": "Bearer " + get_token()}
    query = f"?q={category}+songs&type=track&limit={limit}"
    url = url + query
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result

@app.route('/')
def index():
    if cam_status():
        response = get_songs_for_category("happy songs", 8)
        tracks = response["tracks"]["items"]
        track_data = []
        for track in tracks:
            track_info = {
                'name': track['name'],
                'image_url': track['album']['images'][0]['url'],
                'image_height': track['album']['images'][0]['height'],
                'image_width': track['album']['images'][0]['width'],
                'song_url': f"http://open.spotify.com/track/{track['id']}"
            }
            track_data.append(track_info)
        return render_template('index.html', track_data=track_data, access_token = get_token())
    else:
        return render_template('error.html')
@app.route('/playlists')
def playlists():
    if cam_status():
        response = get_songs_for_category("happy songs", 4)
        tracks = response["tracks"]["items"]
        happy_songs = []
        for track in tracks:
            track_info = {
                'name': track['name'],
                'image_url': track['album']['images'][0]['url'],
                'image_height': track['album']['images'][0]['height'],
                'image_width': track['album']['images'][0]['width'],
                'song_url': f"http://open.spotify.com/track/{track['id']}"
            }
            happy_songs.append(track_info)
        response = get_songs_for_category("sad songs", 4)
        tracks = response["tracks"]["items"]
        sad_songs = []
        for track in tracks:
            track_info = {
                'name': track['name'],
                'image_url': track['album']['images'][0]['url'],
                'image_height': track['album']['images'][0]['height'],
                'image_width': track['album']['images'][0]['width'],
                'song_url': f"http://open.spotify.com/track/{track['id']}"
            }
            sad_songs.append(track_info)
        response = get_songs_for_category("fearful songs", 4)
        tracks = response["tracks"]["items"]
        fear_songs = []
        for track in tracks:
            track_info = {
                'name': track['name'],
                'image_url': track['album']['images'][0]['url'],
                'image_height': track['album']['images'][0]['height'],
                'image_width': track['album']['images'][0]['width'],
                'song_url': f"http://open.spotify.com/track/{track['id']}"

            }
            fear_songs.append(track_info)
        response = get_songs_for_category("fearful songs", 4)
        tracks = response["tracks"]["items"]
        surprised_songs = []
        for track in tracks:
            track_info = {
                'name': track['name'],
                'image_url': track['album']['images'][0]['url'],
                'image_height': track['album']['images'][0]['height'],
                'image_width': track['album']['images'][0]['width'],
                'song_url': f"http://open.spotify.com/track/{track['id']}"
            
            }
            surprised_songs.append(track_info)
        return render_template('playlists.html', happy_songs=happy_songs, surprised_songs=surprised_songs, sad_songs=sad_songs, fear_songs=fear_songs, access_token = get_token())
    else:
        return render_template('error.html')


@app.route('/search', methods=['POST', 'GET'])
def search():
    if cam_status():
        songs = []
        search_term = "Search for songs"
        if request.method == 'POST':
            search_term = request.form.get('searchTerm')
            response = get_songs_for_category(f"{search_term} songs", 20)
            tracks = response["tracks"]["items"]
            for track in tracks:
                track_info = {
                    'name': track['name'],
                    'image_url': track['album']['images'][0]['url'],
                    'image_height': track['album']['images'][0]['height'],
                    'image_width': track['album']['images'][0]['width'],
                    'song_url': f"http://open.spotify.com/track/{track['id']}"
                }
                songs.append(track_info)
        return render_template('search.html', songs=songs, search_term=search_term)
    else:
        return render_template('error.html')

    
@app.route('/detect')
def detect():
    if cam_status():
        return render_template('detect.html')
    else:
        return render_template('error.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_frame')
def video_frame():
    return Response(genFrame(VideoCamera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/emotion')
def emotion():
    emotion = get_emotion()
    return emotion

@app.route('/music_recom')
def music_recom():
    emotion = request.args.get('emotion')
    response = get_songs_for_category(f"{emotion} songs that can fix current {emotion} ", 20)
    print("Fetching songs for EMOTION..............", request.args.get('emotion'))
    tracks = response["tracks"]["items"]
    total = response["tracks"]["total"]
    track_data = []
    for track in tracks:
        track_info = {
            'name': track['name'],
            'image_url': track['album']['images'][0]['url'],
            'image_height': track['album']['images'][0]['height'],
            'image_width': track['album']['images'][0]['width'],
            'duration': track['duration_ms'],
            'song_url': f"http://open.spotify.com/track/{track['id']}",
            'artist': track['artists'][0]['name'],
        }
        track_data.append(track_info)
    return track_data
    
if __name__ == '__main__':
    app.run(debug=True)
