DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS talk;

CREATE TABLE user (
  id TEXT PRIMARY KEY NOT NULL,
  email TEXT NOT NULL,
  given_name TEXT  NOT NULL,
  surname TEXT NOT NULL,
  nutrition TEXT NOT NULL,
  busticket INTEGER NOT NULL
);

CREATE TABLE talk (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  uid TEXT NOT NULL,
  title TEXT,
  subtitle TEXT NOT NULL,
  type TEXT NOT NULL,
  abstract TEXT,
  notes TEXT
);
