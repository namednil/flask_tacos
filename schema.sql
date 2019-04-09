DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS talk;

CREATE TABLE user (
  id TEXT PRIMARY KEY NOT NULL,
  email TEXT NOT NULL,
  given_name TEXT  NOT NULL,
  surname TEXT NOT NULL,
  nutrition TEXT NOT NULL
);

CREATE TABLE talk (
  id TEXT PRIMARY KEY NOT NULL,
  paper TEXT,
  topic TEXT NOT NULL,
  type TEXT NOT NULL,
  shortDescription TEXT,
  notes TEXT
);
