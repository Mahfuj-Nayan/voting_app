CREATE DATABASE voting_app;

USE voting_app;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    has_voted BOOLEAN DEFAULT FALSE
);

CREATE TABLE candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE votes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    candidate_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id),
    UNIQUE (user_id)
);

-- Insert some sample candidates
INSERT INTO candidates (name, description) VALUES 
('Candidate A', 'Experienced leader with 10 years in public service'),
('Candidate B', 'Young innovator with fresh ideas'),
('Candidate C', 'Community organizer focused on local issues');