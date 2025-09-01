from flask import Flask, render_template, g, request, redirect, url_for, session, flash, jsonify
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

    if request.method == "POST":
        user_type = session.get("user_type")
        if user_type == "organisation":
            event_id = request.form.get("event_id")
            if event_id:
                db.execute("DELETE FROM Events WHERE Id = ?", (event_id,))
                db.commit()
                flash("Event deleted.", "info")
        return redirect(url_for("events"))

    cur = db.execute("SELECT * FROM Events ORDER BY Date ASC")
    events = cur.fetchall()
    return render_template("events.html", events=events)


# ------------------- ADD EVENT ------------------- #
@app.route("/add_event", methods=["POST"])
def add_event():
    if session.get("user_type") != "organisation":
        return "Unauthorized", 401

    db = get_db()
    db.execute(
        """INSERT INTO Events (Name, Date, Location, StartTime, EndTime, OrganisationID, Description)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            request.form["name"],
            request.form["date"],
            request.form["location"],
            request.form["starttime"],
            request.form["endtime"],
            session["user_id"],
            request.form.get("description", "")
        ),
    )
    db.commit()
    return "OK", 200


# ------------------- EDIT EVENT ------------------- #
@app.route("/edit_event", methods=["POST"])
def edit_event():
    if session.get("user_type") != "organisation":
        return "Unauthorized", 401

    db = get_db()
    event_id = request.form["event_id"]
    desc = request.form["description"]
    db.execute("UPDATE Events SET Description = ? WHERE Id = ?", (desc, event_id))
    db.commit()
    return "OK", 200


# ------------------- ADD EVENT ROLE ------------------- #
@app.route("/add_event_role", methods=["POST"])
def add_event_role():
    if session.get("user_type") != "organisation":
        return "Unauthorized", 401

    db = get_db()
    event_id = request.form["event_id"]
    role_name = request.form["role_name"]
    role_desc = request.form["role_description"]
    db.execute(
        "INSERT INTO EventRoles (EventID, Name, Description) VALUES (?, ?, ?)",
        (event_id, role_name, role_desc),
    )
    db.commit()
    return "OK", 200


# ------------------- GET EVENT ROLES ------------------- #
@app.route("/get_event_roles", methods=["GET"])
def get_event_roles():
    db = get_db()
    user_type = session.get("user_type")

    if user_type == "volunteer":
        event_id = request.args.get("event_id")
        volunteer_id = session.get("user_id")
        
        # Get all roles for the event
        cur = db.execute("SELECT ID, Name, Description FROM EventRoles WHERE EventID = ?", (event_id,))
        roles = [{"id": r["ID"], "name": r["Name"], "description": r["Description"]} for r in cur.fetchall()]

        # Check signup status for each role
        for role in roles:
            signup_status = db.execute(
                "SELECT Status FROM Signups WHERE VolunteerID = ? AND RoleID = ?",
                (volunteer_id, role["id"])
            ).fetchone()
            if signup_status:
                role["signup_status"] = signup_status["Status"]
        
        return jsonify(roles)

    return ("Unauthorized", 401)

@app.route("/get_org_event_roles", methods=["GET"])
def get_org_event_roles():
    if session.get("user_type") != "organisation":
        return "Unauthorized", 401

    db = get_db()
    event_id = request.args.get("event_id")

    # Fetch roles for the event
    cur = db.execute(
        "SELECT ID, Name, Description FROM EventRoles WHERE EventID = ?", (event_id,)
    )
    roles = [{"id": r["ID"], "name": r["Name"], "description": r["Description"]} for r in cur.fetchall()]

    return jsonify(roles)

# ------------------- REGISTER FOR ROLE ------------------- #
@app.route("/register_for_role", methods=["POST"])
def register_for_role():
    if session.get("user_type") != "volunteer":
        return "Unauthorized", 401

    db = get_db()
    role_id = request.form["role_id"]

    cur = db.execute(
        "SELECT * FROM Signups WHERE VolunteerID = ? AND RoleID = ?",
        (session["user_id"], role_id),
    )
    if cur.fetchone():
        return "Already signed up", 400

    db.execute(
        "INSERT INTO Signups (VolunteerID, RoleID, Status) VALUES (?, ?, 'Pending')",
        (session["user_id"], role_id),
    )
    db.commit()
    return "OK", 200

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
