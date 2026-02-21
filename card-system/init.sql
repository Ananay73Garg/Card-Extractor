CREATE DATABASE IF NOT EXISTS card_system;
USE card_system;

CREATE TABLE IF NOT EXISTS card_records (
    id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    card_type VARCHAR(50),
    card_number VARCHAR(50),
    dob VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS failure_logs (
    id VARCHAR(10) PRIMARY KEY,
    blur_score FLOAT DEFAULT NULL,
    brightness_std FLOAT DEFAULT NULL,
    mean_intensity FLOAT DEFAULT NULL,
    file_size INT DEFAULT NULL,
    name_mismatch CHAR(1) DEFAULT NULL,
    reason VARCHAR(255)
);

INSERT INTO failure_logs 
(id, blur_score, brightness_std, mean_intensity, file_size, name_mismatch, reason)
VALUES 
('FTHRS', 50, 50, 200, 2*1024*1024, 'Y', 'thresholds');