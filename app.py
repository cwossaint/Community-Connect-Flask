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

@app.route("/add_event_role", methods=["POST"])
def add_event_role():
    if session.get("user_type") != "organisation":
        return "Unauthorized", 401
    
    try:
        db = get_db()
        event_id = request.form["event_id"]
        role_name = request.form["role_name"]
        role_desc = request.form["role_description"]
        required_skill_id = request.form.get("required_skill")
        
        db.execute(
            "INSERT INTO EventRoles (EventID, Name, Description, SkillID) VALUES (?, ?, ?, ?)",
            (event_id, role_name, role_desc, required_skill_id),
        )
        db.commit()
        return "OK", 200
    except Exception as e:
        print(f"Error adding event role: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

# ------------------- GET EVENT ROLES FOR VOLUNTEERS ------------------- #
@app.route("/get_event_roles", methods=["GET"])
def get_event_roles():
    db = get_db()
    user_type = session.get("user_type")

    if user_type == "volunteer":
        event_id = request.args.get("event_id")
        volunteer_id = session.get("user_id")
        
        # Get all roles for the event, including the required skill name
        cur = db.execute("""
            SELECT 
                er.ID,
                er.Name,
                er.Description,
                s.Name AS required_skill_name
            FROM EventRoles er
            LEFT JOIN Skills s ON er.SkillID = s.Id
            WHERE er.EventID = ?
        """, (event_id,))
        
        roles = [{"id": r["ID"], "name": r["Name"], "description": r["Description"], "required_skill_name": r["required_skill_name"]} for r in cur.fetchall()]

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

# ------------------- GET EVENT ROLES FOR ORGANISATIONS ------------------- #
@app.route("/get_org_event_roles", methods=["GET"])
def get_org_event_roles():
    if session.get("user_type") != "organisation":
        return "Unauthorized", 401

    db = get_db()
    event_id = request.args.get("event_id")

    # Fetch roles for the event, including the required skill name
    cur = db.execute(
        "SELECT er.ID, er.Name, er.Description, s.Name AS required_skill_name FROM EventRoles er LEFT JOIN Skills s ON er.SkillID = s.Id WHERE er.EventID = ?",
        (event_id,)
    )
    roles = [{"id": r["ID"], "name": r["Name"], "description": r["Description"], "required_skill_name": r["required_skill_name"]} for r in cur.fetchall()]

    return jsonify(roles)

# ------------------- GET ALL SKILLS FOR DROPDOWN ------------------- #
@app.route("/get_skills", methods=["GET"])
def get_skills():
    db = get_db()
    cur = db.execute("SELECT Id, Name FROM Skills ORDER BY Name")
    skills = [{"id": s["Id"], "name": s["Name"]} for s in cur.fetchall()]
    return jsonify(skills)

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
    if 'user_id' not in session or 'user_type' not in session:
        return redirect('/login')

    user_id = session['user_id']
    user_type = session['user_type']
    db = get_db()

    if request.method == 'POST':
        field_to_update = request.form.get('field')
        new_value = request.form.get('value')

        if user_type == 'volunteer':
            if field_to_update == 'email':
                db.execute("UPDATE Volunteers SET Email = ? WHERE ID = ?", (new_value, user_id))
            elif field_to_update == 'phone':
                db.execute("UPDATE Volunteers SET PhoneNumber = ? WHERE ID = ?", (new_value, user_id))
            elif field_to_update == 'location':
                db.execute("UPDATE Volunteers SET Location = ? WHERE ID = ?", (new_value, user_id))
            elif field_to_update == 'bio':
                db.execute("UPDATE Volunteers SET Bio = ? WHERE ID = ?", (new_value, user_id))
            elif field_to_update == 'skills':
                # The skills are in a separate table. We need to clear existing skills and add new ones.
                # Assuming a junction table 'VolunteerSkills' and a 'Skills' table.
                skills = new_value.split(',') if new_value else []

                # First, delete all existing skills for the volunteer
                db.execute("DELETE FROM VolunteerSkills WHERE VolunteerID = ?", (user_id,))
                
                # Then, insert the new skills
                for skill_name in skills:
                    # Find the SkillID from the Skills table
                    cur = db.execute("SELECT ID FROM Skills WHERE Name = ?", (skill_name,))
                    skill = cur.fetchone()
                    if skill:
                        skill_id = skill[0]
                        db.execute("INSERT INTO VolunteerSkills (VolunteerID, SkillID) VALUES (?, ?)", (user_id, skill_id))
            elif field_to_update == 'password':
                # Note: In a real app, you would hash the password here
                db.execute("UPDATE Volunteers SET Password = ? WHERE ID = ?", (new_value, user_id))

        elif user_type == 'organisation':
            if field_to_update == 'name':
                db.execute("UPDATE Organisations SET Name = ? WHERE ID = ?", (new_value, user_id))
            elif field_to_update == 'address':
                db.execute("UPDATE Organisations SET Address = ? WHERE ID = ?", (new_value, user_id))
            elif field_to_update == 'website_url':
                db.execute("UPDATE Organisations SET WebsiteURL = ? WHERE ID = ?", (new_value, user_id))
            elif field_to_update == 'bio':
                # Correctly using the 'Description' column name for organisation bio
                db.execute("UPDATE Organisations SET Description = ? WHERE ID = ?", (new_value, user_id))
            elif field_to_update == 'password':
                # Note: In a real app, you would hash the password here
                db.execute("UPDATE Organisations SET Password = ? WHERE ID = ?", (new_value, user_id))

        db.commit()
        return redirect('/edit_profile')

    # GET request: Get user info for rendering the page
    user = {}
    if user_type == 'volunteer':
        # Retrieve volunteer's basic info
        cur = db.execute("SELECT Email, PhoneNumber, Location, Bio FROM Volunteers WHERE ID = ?", (user_id,))
        volunteer_data = cur.fetchone()
        if not volunteer_data:
            return "Volunteer not found.", 404
        user['email'], user['phone_number'], user['location'], user['bio'] = volunteer_data

        # Retrieve volunteer's skills from the separate table
        cur = db.execute("""
            SELECT T2.Name
            FROM VolunteerSkills AS T1
            JOIN Skills AS T2 ON T1.SkillID = T2.ID
            WHERE T1.VolunteerID = ?
        """, (user_id,))
        user['skills'] = [row[0] for row in cur.fetchall()]

    elif user_type == 'organisation':
        # Retrieve organisation's info
        cur = db.execute("SELECT Name, Address, WebsiteURL, Description FROM Organisations WHERE ID = ?", (user_id,))
        org_data = cur.fetchone()
        if not org_data:
            return "Organisation not found.", 404
        user['name'], user['address'], user['website_url'], user['bio'] = org_data
    
    # Store user_type in the dictionary to pass to the template for conditional rendering
    user['user_type'] = user_type

    return render_template('edit_profile.html', user=user)

@app.route('/view_signups')
def view_signups():
    """
    Handles the logic for the signups page, returning different views
    based on the user type.
    """
    user_type = session.get('user_type')
    if not user_type:
        return redirect(url_for('login', user_type='volunteer'))

    db = get_db()
    user_id = session.get('user_id')
    signups = []

    if user_type == "volunteer":
        # SQL query to get all signups for the current volunteer.
        query = """
            SELECT s.id, s.status,
                   e.Name AS event_name, e.Date AS event_date,
                   o.Name AS organisation_name,
                   r.Name AS role_name
            FROM Signups s
            JOIN EventRoles r ON s.roleID = r.id
            JOIN Events e ON r.EventID = e.id
            JOIN Organisations o ON e.organisationID = o.id
            WHERE s.volunteerID = ?
            ORDER BY e.Date ASC;
        """
        signups = db.execute(query, (user_id,)).fetchall()

    elif user_type == "organisation":
        # Use organisation's ID directly
        org_id = user_id
        query = """
            SELECT s.id, s.status,
                   v.FirstName || ' ' || v.LastName AS volunteer_name,
                   e.Name AS event_name,
                   r.Name AS role_name
            FROM Signups s
            JOIN EventRoles r ON s.roleID = r.id
            JOIN Events e ON r.eventID = e.id
            JOIN Volunteers v ON s.volunteerID = v.id
            WHERE e.organisationID = ?
            ORDER BY e.Date ASC;
        """
        signups = db.execute(query, (org_id,)).fetchall()

    return render_template('view_signups.html', signups=signups, session=session)

@app.route('/update_signup_status', methods=['POST'])
def update_signup_status():
    """
    Handles the AJAX request to update a signup's status.
    It now expects a JSON payload.
    """
    # Check if the user is an organization and logged in
    if session.get('user_type') != 'organisation' or not session.get('user_type'):
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    
    # Read data from the JSON body
    data = request.json
    signup_id = data.get('signup_id')
    status = data.get('status')

    # Basic input validation
    if signup_id is None or status not in ["Accepted", "Rejected"]:
        return jsonify({'error': 'Invalid request data. Missing or invalid signup_id or status.'}), 400

    try:
        db.execute(
            "UPDATE Signups SET status = ? WHERE id = ?",
            (status, signup_id)
        )
        db.commit()
        return jsonify({'success': True, 'message': f'Signup {signup_id} updated to {status}'})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return render_template('index.html')



# --- RUN APP ---
if __name__ == "__main__":
    app.run(debug=True)
