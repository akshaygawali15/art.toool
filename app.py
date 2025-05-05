from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
import jwt
import datetime
import os

app = Flask(__name__)
CORS(app)
SECRET_KEY = "your-secret-key"  # Change in production

# API Keys
PEXELS_API_KEY = "72SJlspsG0YT3nhoRXkhdoKcCyiC7Th283lK5fIic16AMFhHmXfFKqIj"
PIXABAY_API_KEY = "7015670-cf5a815b0ad62fcc79ced3d28"
GIPHY_API_KEY = "hO2Vbyk5a8XupcOMnvA3VlDQAkFPeJuo"
FREESOUND_API_KEY = "ZwChteggbrxPdIOuXRp0ZwChteggbrxPdIOuXRp0"

# Database setup
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# API Routes for Downloads
@app.route('/api/pexels', methods=['GET'])
def get_pexels():
    query = request.args.get('query', 'nature')
    headers = {"Authorization": PEXELS_API_KEY}
    response = requests.get(f"https://api.pexels.com/v1/search?query={query}&per_page=10", headers=headers)
    return jsonify(response.json())

@app.route('/api/pixabay', methods=['GET'])
def get_pixabay():
    query = request.args.get('query', 'nature')
    response = requests.get(f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&per_page=10")
    return jsonify(response.json())

@app.route('/api/giphy', methods=['GET'])
def get_giphy():
    query = request.args.get('query', 'funny')
    response = requests.get(f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={query}&limit=10")
    return jsonify(response.json())

@app.route('/api/freesound', methods=['GET'])
def get_freesound():
    query = request.args.get('query', 'music')
    headers = {"Authorization": f"Token {FREESOUND_API_KEY}"}
    response = requests.get(f"https://freesound.org/apiv2/search/text/?query={query}&page_size=10", headers=headers)
    return jsonify(response.json())

# User Authentication
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return jsonify({"message": "Registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username exists"}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    if user:
        token = jwt.encode({
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY)
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401

# Art Upload
@app.route('/api/upload', methods=['POST'])
def upload():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        payload = jwt.decode(token.split()[1], SECRET_KEY, algorithms=["HS256"])
        username = payload['username']
        data = request.json
        art_link = data['art_link']
        upi_id = data.get('upi_id', '')
        conn = get_db()
        conn.execute("INSERT INTO uploads (username, art_link, upi_id) VALUES (?, ?, ?)", (username, art_link, upi_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Uploaded successfully"}), 201
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

@app.route('/api/uploads', methods=['GET'])
def get_uploads():
    conn = get_db()
    uploads = conn.execute("SELECT * FROM uploads").fetchall()
    conn.close()
    return jsonify([dict(upload) for upload in uploads])

if __name__ == '__main__':
    if not os.path.exists('database.db'):
        with open('schema.sql', 'r') as f:
            conn = sqlite3.connect('database.db')
            conn.executescript(f.read())
            conn.close()
    app.run(debug=True)