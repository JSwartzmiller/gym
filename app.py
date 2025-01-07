import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

# ✅ Load environment variables from .env
load_dotenv()

# ✅ Fetch SECRET_KEY and DATABASE_URL from .env
SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

# ✅ Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app)


# ✅ Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print("Database connection failed:", str(e))
        raise


# ✅ Home route
@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Gym Progress Tracker API!"})


# ✅ Test database connection
@app.route('/test-db')
def test_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT version();')
            version = cursor.fetchone()
        conn.close()
        return jsonify({"message": "Database connected successfully", "version": version})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Add a workout
@app.route('/add-workout', methods=['POST'])
def add_workout():
    try:
        data = request.get_json()
        date = data.get('date')
        label = data.get('label')
        exercises = data.get('exercises')

        if not date or not label or not exercises:
            return jsonify({"error": "Missing required workout data"}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Insert workout
            cursor.execute(
                "INSERT INTO workouts (date, label) VALUES (%s, %s) RETURNING id",
                (date, label)
            )
            workout_id = cursor.fetchone()['id']

            # Insert exercises
            for ex in exercises:
                cursor.execute(
                    "INSERT INTO exercises (workout_id, name, weight) VALUES (%s, %s, %s) RETURNING id",
                    (workout_id, ex['name'], ex['weight'])
                )
                exercise_id = cursor.fetchone()['id']

                # Insert exercise sets
                for reps in ex['sets']:
                    cursor.execute(
                        "INSERT INTO exercise_sets (exercise_id, reps) VALUES (%s, %s)",
                        (exercise_id, reps)
                    )
        conn.commit()
        conn.close()
        return jsonify({"message": "Workout added successfully!"}), 201
    except Exception as e:
        print("Error adding workout:", str(e))
        return jsonify({"error": str(e)}), 500


# ✅ Fetch all workouts
@app.route('/get-workouts', methods=['GET'])
def get_workouts():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT w.id, w.date, w.label,
                    json_agg(
                        json_build_object(
                            'name', e.name,
                            'weight', e.weight,
                            'sets', (
                                SELECT array_agg(es.reps)
                                FROM exercise_sets es
                                WHERE es.exercise_id = e.id
                            )
                        )
                    ) AS exercises
                FROM workouts w
                LEFT JOIN exercises e ON w.id = e.workout_id
                GROUP BY w.id
                ORDER BY w.date DESC;
            """)
            workouts = cursor.fetchall()
        conn.close()
        return jsonify(workouts)
    except Exception as e:
        print("Error fetching workouts:", str(e))
        return jsonify({"error": str(e)}), 500


# ✅ Run the app in debug mode for development
if __name__ == '__main__':
    app.run(debug=True)
