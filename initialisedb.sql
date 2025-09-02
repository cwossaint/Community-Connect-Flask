-- Organisations Table
CREATE TABLE IF NOT EXISTS Organisations (
    ID INTEGER PRIMARY KEY,
    Password TEXT NOT NULL CHECK(length(Password) <= 20),
    Name TEXT NOT NULL UNIQUE CHECK(length(Name) <= 20),
    WebsiteURL TEXT CHECK(WebsiteURL LIKE 'http%' AND length(WebsiteURL) <= 50),
    Address TEXT NOT NULL CHECK(length(Address) <= 30),
    Description TEXT CHECK(length(Description) <= 300),
    Email TEXT NOT NULL UNIQUE CHECK(length(Email) <= 30),
    Verified BOOLEAN NOT NULL DEFAULT False
);

-- Volunteers Table
CREATE TABLE IF NOT EXISTS Volunteers (
    ID INTEGER PRIMARY KEY,
    Password TEXT NOT NULL CHECK(length(Password) <= 20),
    FirstName TEXT NOT NULL CHECK(length(FirstName) <= 20),
    LastName TEXT NOT NULL CHECK(length(LastName) <= 20),
    Email TEXT NOT NULL UNIQUE CHECK(length(Email) <= 30),
    PhoneNumber TEXT NOT NULL UNIQUE CHECK(length(PhoneNumber) <= 10),
    Location TEXT NOT NULL CHECK(length(Location) <= 30),
    BirthDate DATE NOT NULL,
    Bio TEXT CHECK(length(Bio) <= 300),
    TotalHoursContributed INTEGER DEFAULT 0
);

-- Skills Table
CREATE TABLE IF NOT EXISTS Skills (
    ID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL UNIQUE CHECK(length(Name) <= 20)
);

-- Events Table
CREATE TABLE IF NOT EXISTS Events (
    ID INTEGER PRIMARY KEY,
    OrganisationID INTEGER NOT NULL,
    Name TEXT NOT NULL CHECK(length(Name) <= 20),
    Date DATE NOT NULL,
    Location TEXT NOT NULL CHECK(length(Location) <= 30),
    Description TEXT CHECK(length(Description) <= 300),
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    Status TEXT NOT NULL CHECK(Status IN ('Upcoming', 'Passed')) DEFAULT 'Upcoming',
    FOREIGN KEY (OrganisationID) REFERENCES Organisations(ID) ON DELETE CASCADE,
    CHECK (EndTime > StartTime)
);

-- EventRoles Table
CREATE TABLE IF NOT EXISTS EventRoles (
    ID INTEGER PRIMARY KEY,
    EventID INTEGER NOT NULL,
    SkillID INTEGER,
    Name TEXT NOT NULL CHECK(length(Name) <= 30),
    Description TEXT CHECK(length(Description) <= 300),
    VolunteersNeeded INTEGER,
    FOREIGN KEY (EventID) REFERENCES Events(ID) ON DELETE CASCADE,
    FOREIGN KEY (SkillID) REFERENCES Skills(ID) ON DELETE CASCADE
);

-- VolunteerSkills Table
CREATE TABLE IF NOT EXISTS VolunteerSkills (
    ID INTEGER PRIMARY KEY,
    SkillID INTEGER NOT NULL,
    VolunteerID INTEGER NOT NULL,
    FOREIGN KEY (SkillID) REFERENCES Skills(ID) ON DELETE CASCADE,
    FOREIGN KEY (VolunteerID) REFERENCES Volunteers(ID) ON DELETE CASCADE
);

-- Signups Table
CREATE TABLE IF NOT EXISTS Signups (
    ID INTEGER PRIMARY KEY,
    VolunteerID INTEGER NOT NULL,
    RoleID INTEGER NOT NULL,
    Status TEXT NOT NULL CHECK(Status IN ('Pending', 'Accepted', 'Rejected')),
    FOREIGN KEY (VolunteerID) REFERENCES Volunteers(ID) ON DELETE CASCADE,
    FOREIGN KEY (RoleID) REFERENCES EventRoles(ID) ON DELETE CASCADE
);

-- Insert data safely (won’t duplicate if PK/UNIQUE already exists)
INSERT OR IGNORE INTO Organisations VALUES
(1, 'orgpass1', 'GreenEarth', 'http://greenearth.org', '123 Eco Street', 'Environmental NGO', 'contact@greenearth.org', 1),
(2, 'orgpass2', 'HelpingHands', 'http://helpinghands.com', '45 Charity Ave', 'Community welfare organisation', 'info@helpinghands.com', 1);

INSERT OR IGNORE INTO Volunteers VALUES
(1, 'pass1', 'Alice', 'Smith', 'alice@gmail.com', '0412345678', 'Sydney', '1990-05-12', 'Environmental science student', 20),
(2, 'pass2', 'Bob', 'Johnson', 'bob@gmail.com', '0498765432', 'Melbourne', '1985-08-21', 'Love working with people', 10),
(3, 'pass3', 'Charlie', 'Brown', 'charlie@gmail.com', '0411222333', 'Brisbane', '1999-01-15', 'Studying social work', 5);

INSERT OR IGNORE INTO Skills VALUES
(1, 'First Aid'),
(2, 'Cooking'),
(3, 'Teaching'),
(4, 'Event Setup'),
(5, 'Cleaning');

INSERT OR IGNORE INTO Events VALUES
(1, 1, 'Tree Planting', '2025-09-10', 'Sydney Park', 'Planting 200 new trees in the park', '09:00', '15:00', 'Upcoming'),
(2, 2, 'Community Kitchen', '2025-08-25', 'Melbourne Hall', 'Cooking and serving meals for the homeless', '10:00', '14:00', 'Upcoming');

INSERT OR IGNORE INTO EventRoles VALUES
(1, 1, 1, 'Safety Officer', 'Provide first aid support during tree planting', 2),
(2, 1, 4, 'Planter', 'Assist in digging and planting trees', 10),
(3, 2, 2, 'Cook', 'Prepare meals for the community kitchen', 5),
(4, 2, 5, 'Cleaner', 'Clean up after the meal service', 3);

INSERT OR IGNORE INTO VolunteerSkills VALUES
(1, 1, 1),
(2, 4, 2),
(3, 2, 3);

INSERT OR IGNORE INTO Signups VALUES
(1, 1, 1, 'Confirmed'),
(2, 2, 2, 'Pending'),
(3, 3, 3, 'Confirmed');
