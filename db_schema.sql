-- -- Drop existing tables if they exist (for fresh install)
-- DROP TABLE IF EXISTS votes;
-- DROP TABLE IF EXISTS users;
-- DROP TABLE IF EXISTS candidates;

-- Create new tables with userid as primary key
CREATE TABLE users (
    userid VARCHAR(20) PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    has_voted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE votes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    userid VARCHAR(20) NOT NULL,
    candidate_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    UNIQUE (userid),
    INDEX (userid),
    INDEX (candidate_id)
);

-- Insert sample candidates
INSERT INTO candidates (name, description) VALUES 
('Candidate A', 'Experienced leader with 10 years in public service'),
('Candidate B', 'Young innovator with fresh ideas'),
('Candidate C', 'Community organizer focused on local issues');