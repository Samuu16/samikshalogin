from flask import Flask, request, render_template, redirect, session, url_for, jsonify
import bcrypt
import pymssql

app = Flask(__name__)
app.secret_key = 'secret_key'

server = 'mydemo121.database.windows.net'
database = 'sampledb'
username = 'samiksha'
password = 'Sneha@16'

def get_db_connection():
    return pymssql.connect(server, username, password, database)

class User:
    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

class Crud:
    def __init__(self, vehicle, type, fuel_consumption):
        self.vehicle = vehicle
        self.type = type
        self.fuel_consumption = fuel_consumption

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='login' AND xtype='U')
            CREATE TABLE dbo.login (
                name VARCHAR(50) NOT NULL,
                email VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        """)
        conn.commit()

        cursor.execute("SELECT * FROM dbo.login WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            error = 'Email is already registered.'
        else:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("INSERT INTO dbo.login (name, email, password) VALUES (%s, %s, %s)",
                           (name, email, hashed_password))
            conn.commit()
            return redirect('/login')

        conn.close()

    return render_template('signup.html', error=error)

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({"message": "Please provide name, email, and password"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dbo.login WHERE email = %s", (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return jsonify({"message": "Email already registered"}), 400

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO dbo.login (name, email, password) VALUES (%s, %s, %s)",
                       (name, email, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        conn.close()
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email, password FROM dbo.login WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            session['email'] = user[0]
            conn.close()
            return redirect('/dashboard')
        else:
            error = 'Please provide valid credentials to login.'

        conn.close()

    return render_template('login.html', error=error)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data['email']
    password = data['password']

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        session['email'] = user.email
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        email = session['email']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dbo.login WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()
        print("User:", user)
        return render_template('dashboard.html', user=user)
    
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('email', None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dbo.login WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if user:
        cursor.execute("DELETE FROM dbo.login WHERE id = %s", (user_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        conn.close()
        return jsonify({"message": "User not found"}), 404

# CRUD operations for the 'crud' table
@app.route('/crud/create', methods=['POST'])
def crud_create():
    vehicle = request.form['vehicle']
    type = request.form['type']
    fuel_consumption = request.form['fuel_consumption']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO dbo.crud (vehicle, type, fuel_consumption) VALUES (%s, %s, %s)",
                   (vehicle, type, fuel_consumption))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/crud/update/<int:id>', methods=['POST'])
def crud_update(id):
    update_vehicle = request.form['update_vehicle']
    update_type = request.form['update_type']
    update_fuel_consumption = request.form['update_fuel_consumption']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE dbo.crud SET vehicle=%s, type=%s, fuel_consumption=%s WHERE id=%s",
                   (update_vehicle, update_type, update_fuel_consumption, id))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/add_crud', methods=['POST'])
def add_crud():
    vehicle = request.form['vehicle']
    type = request.form['type']
    fuel_consumption = request.form['fuel_consumption']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO dbo.crud (vehicle, type, fuel_consumption) VALUES (%s, %s, %s)",
                   (vehicle, type, fuel_consumption))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/crud/delete/<int:id>', methods=['POST'])
def crud_delete(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM dbo.crud WHERE id = %s", (id,))
    entry = cursor.fetchone()

    if entry:
        cursor.execute("DELETE FROM dbo.crud WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    else:
        conn.close()
        return "Entry not found", 404

@app.route('/api/crud', methods=['GET'])
def api_get_all_crud_entries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, vehicle, type, fuel_consumption FROM dbo.crud")
    entries = cursor.fetchall()
    conn.close()

    entries_data = [{"id": entry[0], "vehicle": entry[1], "type": entry[2], "fuel_consumption": entry[3]} for entry in entries]
    return jsonify(entries_data), 200

@app.route('/api/crud/create', methods=['POST'])
def api_create_crud_entry():
    data = request.json
    vehicle = data.get('vehicle')
    type = data.get('type')
    fuel_consumption = data.get('fuel_consumption')

    # Check if all required fields are present
    if not vehicle or not type or not fuel_consumption:
        return jsonify({"message": "Please provide vehicle, type, and fuel_consumption"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Execute SQL INSERT command to add a new entry
        cursor.execute("INSERT INTO dbo.crud (vehicle, type, fuel_consumption) VALUES (%s, %s, %s)",
                       (vehicle, type, fuel_consumption))
        conn.commit()
        conn.close()

        return jsonify({"message": "Entry created successfully"}), 201
    except Exception as e:
        conn.close()
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/api/crud/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_crud_entry(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the entry exists in the database
    cursor.execute("SELECT * FROM dbo.crud WHERE id = %s", (id,))
    entry = cursor.fetchone()

    if not entry:
        conn.close()
        return jsonify({"message": "Entry not found"}), 404

    if request.method == 'GET':
        entry_data = {"id": entry[0], "vehicle": entry[1], "type": entry[2], "fuel_consumption": entry[3]}
        conn.close()
        return jsonify(entry_data), 200

    elif request.method == 'PUT':
        data = request.json
        vehicle = data.get('vehicle', entry[1])
        type = data.get('type', entry[2])
        fuel_consumption = data.get('fuel_consumption', entry[3])

        try:
            # Execute SQL UPDATE command to update the entry
            cursor.execute("UPDATE dbo.crud SET vehicle=%s, type=%s, fuel_consumption=%s WHERE id=%s",
                           (vehicle, type, fuel_consumption, id))
            conn.commit()
            conn.close()
            return jsonify({"message": "Entry updated successfully"}), 200
        except Exception as e:
            conn.close()
            return jsonify({"message": f"Error: {str(e)}"}), 500

    elif request.method == 'DELETE':
        try:
            # Execute SQL DELETE command to delete the entry
            cursor.execute("DELETE FROM dbo.crud WHERE id=%s", (id,))
            conn.commit()
            conn.close()
            return jsonify({"message": "Entry deleted successfully"}), 200
        except Exception as e:
            conn.close()
            return jsonify({"message": f"Error: {str(e)}"}), 500
    return jsonify({"message": "Entry deleted successfully"}), 200



if __name__ == '__main__':
    app.run(debug=True)