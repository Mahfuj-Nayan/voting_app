from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or 'your-secret-key-here'

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST') or 'localhost',
    'user': os.getenv('DB_USER') or 'root',
    'password': os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('DB_NAME') or 'voting_app'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err.msg}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if user has already voted
    cursor.execute("SELECT has_voted FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    if user['has_voted']:
        # Get the user's vote
        cursor.execute("""
            SELECT c.name, c.description 
            FROM votes v
            JOIN candidates c ON v.candidate_id = c.id
            WHERE v.user_id = %s
        """, (user_id,))
        vote = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template('voted.html', vote=vote)
    
    # Get all candidates
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', candidates=candidates)

@app.route('/vote/<int:candidate_id>', methods=['POST'])
def vote(candidate_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user has already voted
        cursor.execute("SELECT has_voted FROM users WHERE id = %s", (user_id,))
        if cursor.fetchone()[0]:
            flash('You have already voted!', 'warning')
            return redirect(url_for('dashboard'))
        
        # Record the vote
        cursor.execute(
            "INSERT INTO votes (user_id, candidate_id) VALUES (%s, %s)",
            (user_id, candidate_id)
        )
        
        # Update user's voting status
        cursor.execute(
            "UPDATE users SET has_voted = TRUE WHERE id = %s",
            (user_id,)
        )
        
        conn.commit()
        flash('Your vote has been recorded!', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error: {err.msg}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/results')
def results():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get vote counts
    cursor.execute("""
        SELECT c.id, c.name, c.description, COUNT(v.id) as vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.id = v.candidate_id
        GROUP BY c.id
        ORDER BY vote_count DESC
    """)
    results = cursor.fetchall()
    
    # Get total votes
    cursor.execute("SELECT COUNT(*) as total FROM votes")
    total = cursor.fetchone()['total']
    
    cursor.close()
    conn.close()
    
    return render_template('results.html', results=results, total=total)

if __name__ == '__main__':
    app.run(debug=True)