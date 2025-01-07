from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

# Initialize the Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Database setup (initial connection and table creation)
def init_db():
    with sqlite3.connect('database/workouts.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                weight INTEGER,
                reps INTEGER,
                sets INTEGER,
                date TEXT
            )
        ''')
        conn.commit()

# Home route (basic test)
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Gym Progress Tracker API!"})

# Start the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
