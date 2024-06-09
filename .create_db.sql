CREATE TABLE user (
    id INTEGER PRIMARY KEY
);

CREATE TABLE pills_reminder (
    id INTEGER PRIMARY KEY,
    time TIME NOT NULL,
    name TEXT NOT NULL,
    taken INTEGER DEFAULT 0
);

ALTER TABLE pills_reminder
ADD COLUMN user_id INTEGER REFERENCES user(id);
