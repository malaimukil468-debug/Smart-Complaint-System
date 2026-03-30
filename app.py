from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret_key'

# Database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
            (name, email, password)
        )
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('register.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE email = ? AND password = ?',
        (email, password)
    ).fetchone()
    conn.close()

    if user:
        if not user['is_approved']:
            return 'Account pending approval by admin'
        session['user_id'] = user['user_id']
        return redirect('/select_technician')

    return 'Invalid Login'


@app.route('/select_technician')
def select_technician():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    technicians = conn.execute('SELECT * FROM technicians').fetchall()
    conn.close()

    return render_template('select_technician.html', technicians=technicians)



@app.route('/complaint/<int:technician_id>')
def complaint_page(technician_id):
    session['technician_id'] = technician_id
    return render_template('user_dashboard.html')


@app.route('/dashboard')
def dashboard():
    return render_template('user_dashboard.html')



@app.route('/add_complaint', methods=['POST'])
def add_complaint():
    if 'user_id' not in session or 'technician_id' not in session:
        return redirect('/')

    category = request.form['category']
    description = request.form['description']
    user_id = session['user_id']
    technician_id = session['technician_id']

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO complaints (user_id, technician_id, category, description) VALUES (?, ?, ?, ?)',
        (user_id, technician_id, category, description)
    )
    conn.commit()
    conn.close()

    return redirect('/my_complaints')



@app.route('/my_complaints')
def my_complaints():
    user_id = session['user_id']

    conn = get_db_connection()
    complaints = conn.execute(
        'SELECT * FROM complaints WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    conn.close()

    return render_template('my_complaints.html', complaints=complaints)

# ---------- ADMIN LOGIN ----------

@app.route('/admin')
def admin_login():
    return render_template('admin_login.html')


@app.route('/admin_login', methods=['POST'])
def admin_login_post():
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    admin = conn.execute(
        "SELECT * FROM users WHERE email = ? AND password = ? AND role = 'admin'",
        (username, password)
    ).fetchone()
    conn.close()

    if admin:
        session['admin'] = True
        return redirect('/admin_dashboard')

    return 'Invalid Admin Login'


# ---------- ADMIN DASHBOARD ----------

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin')

    conn = get_db_connection()
    complaints = conn.execute(
       '''
       SELECT complaints.*, users.name AS user_name
       FROM complaints
       JOIN users ON complaints.user_id = users.user_id
       '''
    ).fetchall()
    
    pending_users = conn.execute(
        "SELECT * FROM users WHERE is_approved = 0 AND role != 'admin'"
    ).fetchall()
    conn.close()

    return render_template('admin_dashboard.html', complaints=complaints, pending_users=pending_users)

@app.route('/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    if 'admin' not in session:
        return redirect('/admin')

    conn = get_db_connection()
    conn.execute('UPDATE users SET is_approved = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    return redirect('/admin_dashboard')


# ---------- UPDATE STATUS ----------

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    status = request.form['status']

    conn = get_db_connection()
    conn.execute(
        'UPDATE complaints SET status = ? WHERE complaint_id = ?',
        (status, id)
    )
    conn.commit()
    conn.close()

    return redirect('/admin_dashboard')


@app.route('/submit_feedback/<int:complaint_id>', methods=['POST'])
def submit_feedback(complaint_id):
    if 'user_id' not in session:
        return redirect('/')

    rating = request.form['rating']
    feedback = request.form['feedback']

    conn = get_db_connection()
    conn.execute(
        'UPDATE complaints SET rating = ?, feedback = ? WHERE complaint_id = ?',
        (rating, feedback, complaint_id)
    )
    conn.commit()
    conn.close()

    return redirect('/my_complaints')


@app.route('/technician')
def technician_login():
    return render_template('technician_login.html')



@app.route('/technician_login', methods=['POST'])
def technician_login_post():
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    tech = conn.execute(
        'SELECT * FROM technicians WHERE email=? AND password=?',
        (email, password)
    ).fetchone()
    conn.close()

    if tech:
        session['technician_id'] = tech['technician_id']
        return redirect('/technician_dashboard')

    return 'Invalid Technician Login'


@app.route('/technician_dashboard')
def technician_dashboard():
    if 'technician_id' not in session:
        return redirect('/technician')

    tech_id = session['technician_id']

    conn = get_db_connection()
    complaints = conn.execute("""
        SELECT complaints.*, users.name AS user_name
        FROM complaints
        JOIN users ON complaints.user_id = users.user_id
        WHERE complaints.technician_id = ?
    """, (tech_id,)).fetchall()
    conn.close()

    return render_template('technician_dashboard.html', complaints=complaints)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
