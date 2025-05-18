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
@app.route('/register', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])

# Register a new user
def register():
    if request.method == 'POST':
        userid = request.form['userid'].strip()
        username = request.form['username'].strip()
        email = request.form.get('email', '').strip() or None
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validation
        if len(userid) < 4 or len(userid) > 20:
            flash('User ID must be between 4-20 characters', 'danger')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if userid already exists
            cursor.execute("SELECT userid FROM users WHERE userid = %s", (userid,))
            if cursor.fetchone():
                flash('User ID already taken!', 'danger')
                return redirect(url_for('register'))

            # Insert new user
            cursor.execute(
                "INSERT INTO users (userid, username, email, password) VALUES (%s, %s, %s, %s)",
                (userid, username, email, hashed_password)
            )
                
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err.msg}', 'danger')
            return redirect(url_for('register'))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form['userid'].strip()
        password = request.form['password']

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE userid = %s", (userid,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session['userid'] = user['userid']
                session['username'] = user['username']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid User ID or password', 'danger')
        except mysql.connector.Error as err:
            flash(f'Database error: {err.msg}', 'danger')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('login.html')

# Logout user
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Display dashboard with candidates
@app.route('/dashboard')
def dashboard():
    if 'userid' not in session:
        return redirect(url_for('login'))

    userid = session['userid']
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user has already voted
        cursor.execute("SELECT has_voted FROM users WHERE userid = %s", (userid,))
        user = cursor.fetchone()
        
        if user['has_voted']:
            # Get the user's vote
            cursor.execute("""
                SELECT c.name, c.description 
                FROM votes v
                JOIN candidates c ON v.candidate_id = c.id
                WHERE v.userid = %s
            """, (userid,))
            vote = cursor.fetchone()
            return render_template('voted.html', vote=vote)
        
        # Get all candidates
        cursor.execute("SELECT * FROM candidates")
        candidates = cursor.fetchall()
        return render_template('dashboard.html', candidates=candidates)
    
    except mysql.connector.Error as err:
        flash(f'Database error: {err.msg}', 'danger')
        return redirect(url_for('home'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Vote for a candidate
@app.route('/vote/<int:candidate_id>', methods=['POST'])
def vote(candidate_id):
    if 'userid' not in session:
        return redirect(url_for('login'))

    userid = session['userid']
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user has already voted
        cursor.execute("SELECT has_voted FROM users WHERE userid = %s", (userid,))
        if cursor.fetchone()[0]:
            flash('You have already voted!', 'warning')
            return redirect(url_for('dashboard'))
        
        # Record the vote
        cursor.execute(
            "INSERT INTO votes (userid, candidate_id) VALUES (%s, %s)",
            (userid, candidate_id)
        )
        
        # Update user's voting status
        cursor.execute(
            "UPDATE users SET has_voted = TRUE WHERE userid = %s",
            (userid,)
        )
        
        conn.commit()
        flash('Your vote has been recorded!', 'success')
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        flash(f'Error: {err.msg}', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return redirect(url_for('dashboard'))

# Display voting results
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