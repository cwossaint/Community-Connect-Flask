from flask import Flask, render_template, g, request, redirect, url_for, session
import sqlite3

# --- CONFIG ---
DATABASE = "Community Connect.db"  # your SQLite database file
app = Flask(__name__)
app.secret_key = "Jiggery"

# --- DATABASE CONNECTION ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # lets you access results like dicts
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- ROUTES ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/organisations")
def organisations():
    db = get_db()
    cur = db.execute("SELECT * FROM Organisations ORDER BY Name ASC")
    organisations = cur.fetchall()
    return render_template("organisations.html", organisations=organisations)

@app.route("/events", methods=["GET", "POST"])
def events():
    db = get_db()

    # Handle POST requests
    if request.method == "POST":
        if "user_type" not in session or session["user_type"] != "organisation":
            # Only organisations should be able to add/delete events
            return redirect(url_for("events"))

        # Case 1: Delete event
        if "event_id" in request.form:
            event_id = request.form["event_id"]
            db.execute("DELETE FROM Events WHERE Id = ?", (event_id,))
            db.commit()
            return redirect(url_for("events"))

        # Case 2: Add new event
        elif "name" in request.form:
            name = request.form["name"]
            date = request.form["date"]
            location = request.form["location"]
            starttime = request.form["starttime"]
            endtime = request.form["endtime"]

            # Make sure session has organisation id
            organisation_id = session.get("user_id")

            db.execute(
                """
                INSERT INTO Events (Name, Date, Location, StartTime, EndTime, OrganisationID, Description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, date, location, starttime, endtime, organisation_id, request.form.get("description", ""))
            )
            db.commit()
            return redirect(url_for("events"))

    # Handle GET requests — always fetch updated events list
    cur = db.execute("SELECT * FROM Events ORDER BY Date ASC")
    events = cur.fetchall()
    return render_template("events.html", events=events)

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signup/volunteer", methods = ['GET', 'POST'])
def volunteer_signup():
    if request.method == 'POST':
        db = get_db()
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password'] 
        birthdate = request.form['birthdate']
        phone_num = request.form['phone']
        location = request.form['location']
        cur = db.execute("INSERT INTO Volunteers (Password, FirstName, LastName, Email, PhoneNumber, Location, BirthDate) VALUES (?, ?, ?, ?, ?, ?, ?)", (password, first_name, last_name, email, phone_num, location, birthdate))
        db.commit()
        return redirect(url_for('login')) 
    return render_template("volunteer_signup.html")

@app.route("/signup/organisation", methods = ['GET', 'POST'])
def organisation_signup():
    if request.method == 'POST':
            db = get_db()
            org_name = request.form['org_name']
            address = request.form['address']
            email = request.form['email']
            password = request.form['password']
            print("creating organisation record")
            cur = db.execute("INSERT INTO Organisations (Password, Name, Email, Address) VALUES (?, ?, ?, ?)", (password, org_name, email, address))
            db.commit()
            return redirect(url_for('login')) 
    return render_template("organisation_signup.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cur = db.execute("SELECT * FROM Volunteers WHERE Email=? AND Password=?", (email, password))
        volunteer = cur.fetchone()

        if volunteer:
            session['user_type'] = 'volunteer'
            session['user_id'] = volunteer['ID']
            session['first_name'] = volunteer['FirstName']
            return redirect(url_for('index'))    
        else:
            db = get_db()
            cur = db.execute("SELECT * FROM Organisations WHERE Email=? AND Password=?", (email, password))
            org = cur.fetchone()
            if org:
                session['user_type'] = 'organisation'
                session['user_id'] = org['ID']
                session['org_name'] = org['Name']
                return redirect(url_for('index'))
            else:   
                print("invalid credentials")

    return render_template("login.html")

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    db = get_db()

    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        location = request.form.get('location')
        password = request.form.get('password')

        if email:
            print("email")
            db.execute("UPDATE Volunteers SET Email = ? WHERE ID = ?", (email, session['user_id']))
        if phone:
            print("phone")
            db.execute("UPDATE Volunteers SET PhoneNumber = ? WHERE ID = ?", (phone, session['user_id']))
        if location:
            print("location")
            db.execute("UPDATE Volunteers SET Location = ? WHERE ID = ?", (location, session['user_id']))
        if password:
            print("password")
            db.execute("UPDATE Volunteers SET Password = ? WHERE ID = ?", (password, session['user_id']))

        db.commit()
        return redirect('/edit_profile')  # refresh the page to show updates

    # Get updated user info for rendering
    cur = db.execute("SELECT Password, Email, PhoneNumber, Location FROM Volunteers WHERE ID = ?", (session['user_id'],))
    user = cur.fetchone()

    return render_template('edit_profile.html', user=user)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return render_template('index.html')

# --- RUN APP ---
if __name__ == "__main__":
    app.run(debug=True)
