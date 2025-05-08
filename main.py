from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
import sqlite3
import random
import os
import re
from datetime import datetime
from fuzzywuzzy import fuzz, process
import numpy as np
import re
import difflib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


otp_storage = {}  


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def is_logged_in():
    return 'email' in session
def send_otp_email(recipient_email, otp):
    subject = "Your OTP for Registration"
    body = f"Your OTP is: {otp}. Please enter this to complete your registration."

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print(f"OTP sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send OTP: {e}")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        year = request.form['year']
        semester = request.form['semester']
        academic_year = request.form['academic_year']
        school = request.form['school']
        branch = request.form['branch']

        if not re.match(r'^[a-zA-Z0-9._%+-]+@mahindrauniversity\.edu\.in$', email):
            flash('Invalid email domain. Use @mahindrauniversity.edu.in email.')
            return redirect(url_for('register'))

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user:
            flash('Email already registered. Please login.')
            return redirect(url_for('login'))

        otp = str(random.randint(100000, 999999))
        otp_storage[email] = {
            'otp': otp,
            'data': {
                'email': email,
                'password': password,
                'year': year,
                'semester': semester,
                'academic_year': academic_year,
                'school': school,
                'branch': branch
            }
        }

        send_otp_email(email, otp)
        flash("OTP sent to your Mahindra University email. Please check your inbox.")
        return render_template('verify_otp.html', email=email)

    return render_template('register.html')

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    email = request.form['email']
    entered_otp = request.form['otp']

    if email in otp_storage and otp_storage[email]['otp'] == entered_otp:
        new_user = otp_storage[email]['data']
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO users (email, password, year, semester, academic_year, school, branch)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_user['email'], new_user['password'], new_user['year'], new_user['semester'],
            new_user['academic_year'], new_user['school'], new_user['branch']
        ))
        conn.commit()
        conn.close()
        del otp_storage[email]

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    else:
        flash('Invalid OTP. Please try again.')
        return render_template('verify_otp.html', email=email)


# -------------------- Login / Logout --------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['email'] = user['email']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('attendance', None)
    flash('Logged out successfully.')
    return redirect(url_for('index'))


# -------------------- Home / Index --------------------

@app.route('/')
@app.route('/index')
def index():
    search_query = request.args.get('query', '').lower()
    conn = get_db_connection()

 
    all_professors = conn.execute('SELECT * FROM professors').fetchall()
    all_professors_list = [dict(row) for row in all_professors]

    if search_query:
       
        exact_matches = [prof for prof in all_professors_list if search_query in prof['Name'].lower()]

        
        if len(exact_matches) < 15:
            names = [prof['Name'] for prof in all_professors_list]
            matched_names = process.extract(search_query, names, limit=15, scorer=fuzz.partial_ratio)

            
            matched_profs = exact_matches + [prof for prof in all_professors_list if prof['Name'] in [match[0] for match in matched_names] and prof not in exact_matches]
        else:
            matched_profs = exact_matches
    else:
       
        rated = conn.execute('SELECT * FROM professors WHERE no_ratings > 0 ORDER BY Avg_rating DESC LIMIT 15').fetchall()
        rated_list = [dict(row) for row in rated]
        rated_count = len(rated_list)

        if rated_count < 15:
            needed = 15 - rated_count
            unrated = conn.execute('SELECT * FROM professors WHERE no_ratings = 0 ORDER BY RANDOM() LIMIT ?', (needed,)).fetchall()
            unrated_list = [dict(row) for row in unrated]
            matched_profs = rated_list + unrated_list
        else:
            matched_profs = rated_list

    professors_list = [{
        'Name': prof['Name'],
        'Designation': prof['Designation'],
        'Photo': prof['Photo'],
        'Avg_rating': prof['Avg_rating'],
        'id': prof['id']
    } for prof in matched_profs]

    conn.close()
    return render_template('index.html', professors=professors_list)


@app.route('/api/top-professors')
def top_professors():
    conn = get_db_connection()
    rated = conn.execute('SELECT * FROM professors WHERE no_ratings > 0 ORDER BY Avg_rating DESC LIMIT 15').fetchall()
    rated_list = [dict(row) for row in rated]
    rated_count = len(rated_list)

    if rated_count < 15:
        needed = 15 - rated_count
        unrated = conn.execute('SELECT * FROM professors WHERE no_ratings = 0 ORDER BY RANDOM() LIMIT ?', (needed,)).fetchall()
        unrated_list = [dict(row) for row in unrated]
        final_list = rated_list + unrated_list
    else:
        final_list = rated_list

    result = [dict(prof) for prof in final_list]
    conn.close()
    return jsonify(result)


# -------------------- Professor Profile Page --------------------
@app.route('/professor/<name>')
def professor_by_name(name):
    conn = get_db_connection()
    prof = conn.execute('SELECT * FROM professors WHERE Name = ?', (name,)).fetchone()

    if not prof:
        flash("Professor not found.")
        conn.close()
        return redirect(url_for('index'))

    reviews = conn.execute('SELECT * FROM reviews WHERE professor_id = ? ORDER BY timestamp DESC', (prof['id'],)).fetchall()

    professor_info = {
        'id': prof['id'],
        'Name': prof['Name'],
        'Designation': prof['Designation'],
        'Photo': prof['Photo'],
        'Avg_rating': prof['Avg_rating'],
        'No_ratings': prof['no_ratings'],
        'Profile_link': prof['Profile']
    }

    conn.close()
    return render_template('professor.html', professor=professor_info, reviews=reviews)


#----route for uploading the attendance
@app.route('/upload_attendance', methods=['GET', 'POST'])
def upload_attendance():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            image_bytes = file.read()
            percentage = extract_attendance_percentage(image_bytes)

            try:
                percentage = float(percentage)
                session['attendance'] = percentage
                if percentage >= 75:
                    flash(f'Attendance verified: {percentage}%', 'success')
                    return redirect(url_for('index'))
                else:
                    flash(f'Attendance too low ({percentage}%). Must be at least 75%.', 'danger')
                    return redirect(url_for('upload_attendance'))
            except ValueError:
                flash("Could not extract a valid attendance percentage.", 'danger')
                return redirect(url_for('upload_attendance'))

    return render_template('upload.html')

def extract_attendance_percentage(image_bytes):
    api_key = os.getenv("OCR_API_KEY")  
    response = requests.post(
        'https://api.ocr.space/parse/image',
        files={'filename': ('image.jpg', image_bytes)},
        data={
            'apikey': api_key,
            'language': 'eng',
            'isOverlayRequired': False
        }
    )

    result = response.json()
    try:
        text = result['ParsedResults'][0]['ParsedText']
    except (KeyError, IndexError):
        return "Could not extract text."

    match = re.search(r'(\d+)\s*/\s*(\d+)\s*=\s*(\d+(\.\d+)?)', text)
    if match:
        return float(match.group(3))
    return "Could not extract attendance percentage."

# -------------------- Rating Submission --------------------
@app.route('/questionnaire/<int:prof_id>')
def questionnaire(prof_id):
    if not is_logged_in():
        flash("Please log in to rate a professor.")
        return redirect(url_for('login'))
    
    attendance = session.get('attendance')
    if attendance is None:
        flash("Please verify your attendance before rating.")
        return redirect(url_for('upload_attendance'))
    elif attendance < 75:
        flash("Your attendance is below 75%. You cannot rate professors.")
        return redirect(url_for('index'))

    return render_template('questionnaire.html', prof_id=prof_id)


@app.route('/submit_rating/<int:prof_id>', methods=['POST'])
def submit_rating(prof_id):
    if not is_logged_in():
        flash("You must be logged in to submit a rating.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    professor = cursor.execute('SELECT * FROM professors WHERE id = ?', (prof_id,)).fetchone()
    if professor is None:
        flash("Professor not found.")
        conn.close()
        return redirect(url_for('index'))

    try:
        
        teaching_effectiveness = [
            int(request.form['explain_concepts']),
            int(request.form['clear_lectures']),
            int(request.form['encourages_participation']),
            int(request.form['responsiveness'])
        ]
        course_content_materials = [
            int(request.form['helpful_materials']),
            int(request.form['manageable_workload']),
            int(request.form['fair_grading'])
        ]
        overall_rating = int(request.form['overall_rating'])
        comment = request.form.get('comment', '').strip()

        teaching_avg = sum(teaching_effectiveness) / len(teaching_effectiveness)
        content_avg = sum(course_content_materials) / len(course_content_materials)
        weighted_avg = (teaching_avg * 0.4) + (content_avg * 0.3) + (overall_rating * 0.3)
        weighted_avg = round(weighted_avg, 2)

        old_no_ratings = professor['no_ratings']
        old_avg_rating = professor['Avg_rating']
        new_no_ratings = old_no_ratings + 1
        new_avg_rating = ((old_avg_rating * old_no_ratings) + weighted_avg) / new_no_ratings
        new_avg_rating = round(new_avg_rating, 2)

        cursor.execute('''
            UPDATE professors
            SET Avg_rating = ?, no_ratings = ?
            WHERE id = ?
        ''', (new_avg_rating, new_no_ratings, prof_id))

        cursor.execute('''
            INSERT INTO ratings (
                professor_id,
                user_email,
                teaching_rating,
                content_rating,
                overall_rating,
                rating,
                comment,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prof_id,
            session['email'],
            int(teaching_avg),
            int(content_avg),
            overall_rating,
            weighted_avg,
            comment,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        conn.commit()
        flash("Your rating has been submitted successfully!", "success")

    except Exception as e:
        print("Error during rating submission:", e)
        flash("An error occurred while submitting your rating.", "danger")
    finally:
        conn.close()

    return redirect(url_for('professor_by_name', name=professor['Name']))


# -------------------- Review Submission --------------------
@app.route('/write_review/<int:professor_id>', methods=['GET'])
def write_review(professor_id):
    if not is_logged_in():
        flash("You must be logged in to write a review.")
        return redirect(url_for('login'))

    attendance = session.get('attendance')
    if attendance is None:
        flash("Please verify your attendance before submitting a review.")
        return redirect(url_for('upload_attendance'))  
    elif attendance < 75:
        flash("Your attendance is below 75%. You cannot review professors.")
        return redirect(url_for('index')) 

    conn = get_db_connection()
    professor = conn.execute('SELECT * FROM professors WHERE id = ?', (professor_id,)).fetchone()
    conn.close()

    if professor is None:
        flash("Professor not found.")
        return redirect(url_for('index'))

    return render_template('write_review.html', professor_id=professor_id, professor_name=professor['Name'])


@app.route('/submit_review/<int:professor_id>', methods=['POST', 'GET'])
def submit_review(professor_id):
    if not is_logged_in():
        flash('You must be logged in to submit a review.', 'warning')
        return redirect(url_for('login'))


    if request.method == 'POST':
        review_text = request.form['review_text']
        user_email = session['email']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT Name FROM professors WHERE id = ?", (professor_id,))
        prof = cursor.fetchone()
        if not prof:
            flash('Professor not found.', 'danger')
            return redirect(url_for('index'))

        professor_name = prof['Name']

        cursor.execute(''' 
            INSERT INTO reviews (
                user_email, professor_id, professor_name, 
                review_text, timestamp
            ) VALUES (?, ?, ?, ?, ?)
        ''', (user_email, professor_id, professor_name, review_text, datetime.now()))

        conn.commit()
        conn.close()

        flash('Your review has been submitted!', 'success')
        return redirect(url_for('professor_by_name', name=professor_name))

    return render_template('write_review.html', professor_id=professor_id)


# -------------------- User Profile --------------------
@app.route('/profile')
def profile():
    if not is_logged_in():
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_email = session['email']

    user = conn.execute('SELECT * FROM users WHERE email = ?', (user_email,)).fetchone()

    ratings = conn.execute('''
        SELECT r.rating, r.comment, r.timestamp, p.Name AS professor_name, p.id AS professor_id
        FROM ratings r
        JOIN professors p ON r.professor_id = p.id
        WHERE r.user_email = ?
        ORDER BY r.timestamp DESC
    ''', (user_email,)).fetchall()

    reviews = conn.execute('''
        SELECT rv.review_text, rv.timestamp, p.Name AS professor_name, p.id AS professor_id
        FROM reviews rv
        JOIN professors p ON rv.professor_id = p.id
        WHERE rv.user_email = ?
        ORDER BY rv.timestamp DESC
    ''', (user_email,)).fetchall()

    conn.close()

    return render_template('profile.html', user=user, ratings=ratings, reviews=reviews)

# -------------------- Community Page --------------------


@app.route('/join_community', methods=['GET', 'POST'])
def join_community():
    if 'email' not in session:
        flash('Please log in first.')
        return redirect('/login')

    email = session['email']
    conn = get_db_connection()
    cursor = conn.cursor()

    existing_user = cursor.execute("SELECT * FROM community_users WHERE email = ?", (email,)).fetchone()
    if existing_user:
        conn.close()
        flash('You already have a community username.')
        return redirect('/community')

    if request.method == 'POST':
        username = request.form['username'].strip()

        taken = cursor.execute("SELECT * FROM community_users WHERE username = ?", (username,)).fetchone()
        if taken:
            conn.close()
            flash('Username already taken. Please choose another.')
            return redirect('/join_community')

        cursor.execute("INSERT INTO community_users (email, username) VALUES (?, ?)", (email, username))
        conn.commit()
        conn.close()
        flash('Welcome to the community!')
        return redirect('/community')

    conn.close()
    return render_template('join_community.html')


@app.route('/community', methods=['GET', 'POST'])
def community():
    if 'email' not in session:
        flash('Please log in first.')
        return redirect('/login')

    email = session['email']
    conn = get_db_connection()
    cursor = conn.cursor()

    user = cursor.execute("SELECT username FROM community_users WHERE email = ?", (email,)).fetchone()

    if not user:
        conn.close()
        flash("You must join the community first.")
        return redirect('/join_community')

    username = user['username']

    if request.method == 'POST':
        message = request.form['message']
        cursor.execute(
            'INSERT INTO community_posts (username, message) VALUES (?, ?)',
            (username, message)
        )
        conn.commit()

    posts = cursor.execute('SELECT * FROM community_posts ORDER BY timestamp DESC').fetchall()
    all_replies = cursor.execute('SELECT * FROM community_replies ORDER BY timestamp ASC').fetchall()
    conn.close()

    post_reply_map = {}
    for reply in all_replies:
        post_id = reply['post_id']
        post_reply_map.setdefault(post_id, []).append(reply)

    enriched_posts = []
    for post in posts:
        enriched_posts.append({
            **dict(post),
            'replies': post_reply_map.get(post['id'], [])
        })

    return render_template('community.html', username=username, posts=enriched_posts)




@app.route('/reply', methods=['POST'])
def reply():
    if not is_logged_in():
        flash("You must be logged in to access the community.", "warning")
        return redirect(url_for('login'))

    email = session['email']  
    username = session.get('username')

    if not username:
        conn = get_db_connection()
        user = conn.execute('SELECT username FROM community_users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user:
            username = user['username']
        else:
            flash("Unable to retrieve username from the database.", "danger")
            return redirect(url_for('login'))

    post_id = request.form['post_id']
    message = request.form['message'].strip()
    parent_reply_id = request.form.get('parent_reply_id') 


    if parent_reply_id == '' or parent_reply_id is None:
        parent_reply_id = None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO community_replies (post_id, parent_reply_id, username, message, timestamp)
        VALUES (?, ?, ?, ?, datetime('now'))
        ''',
        (post_id, parent_reply_id, username, message)
    )
    conn.commit()
    conn.close()

    return redirect('/community')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    if not is_logged_in():
        flash('You must be logged in to delete your account.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = session['email']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM ratings WHERE user_email = ?', (email,))
        cursor.execute('DELETE FROM reviews WHERE user_email = ?', (email,))
        cursor.execute('DELETE FROM community_users WHERE email = ?', (email,))
        cursor.execute('DELETE FROM users WHERE email = ?', (email,))

        conn.commit()
        conn.close()

        session.pop('email', None)
        flash('Your account and all associated data have been deleted.', 'success')
        return redirect(url_for('index'))

    return render_template('delete.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

