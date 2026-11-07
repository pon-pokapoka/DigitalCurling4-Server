-- Basic authentication, previously in src/basic_certification.sqlite3.
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR PRIMARY KEY,
    hash_password VARCHAR,
    salt VARCHAR
);

CREATE TABLE IF NOT EXISTS basic_authentication (
    id SERIAL PRIMARY KEY,
    username VARCHAR,
    hash_password VARCHAR,
    match_team_name VARCHAR,
    match_id UUID,
    created_at TIMESTAMP NOT NULL,
    expired_at TIMESTAMP NOT NULL
);

-- check_match_data runs on every shot.
CREATE INDEX IF NOT EXISTS idx_basic_authentication_username_match
  ON basic_authentication (username, match_id);

CREATE INDEX IF NOT EXISTS idx_basic_authentication_expired_at
  ON basic_authentication (expired_at);
