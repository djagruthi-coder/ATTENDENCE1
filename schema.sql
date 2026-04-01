CREATE TABLE IF NOT EXISTS students (
    roll_no TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    dob TEXT NOT NULL,
    branch TEXT NOT NULL,
    section TEXT NOT NULL,
    role TEXT DEFAULT 'student',
    email TEXT
);

CREATE TABLE IF NOT EXISTS attendance (
    roll_no TEXT,
    subject TEXT,
    attended INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    PRIMARY KEY (roll_no, subject),
    FOREIGN KEY (roll_no) REFERENCES students(roll_no)
);

CREATE TABLE IF NOT EXISTS attendance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT,
    subject TEXT,
    date TEXT,
    present BOOLEAN,
    FOREIGN KEY (roll_no) REFERENCES students(roll_no)
);

CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch TEXT NOT NULL,
    section TEXT NOT NULL,
    UNIQUE(branch, section)
);

-- Insert dummy teacher data
INSERT OR IGNORE INTO students (roll_no, name, dob, branch, section, role) VALUES ('TEACHER01', 'Admin Teacher', '1990-01-01', 'ALL', 'ALL', 'teacher');
