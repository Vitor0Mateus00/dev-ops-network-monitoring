CREATE DATABASE IF NOT EXISTS monitoring;
USE monitoring;

CREATE TABLE IF NOT EXISTS ping_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    rtt_ms FLOAT,
    packet_loss FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_host_timestamp (host, timestamp)
);

CREATE TABLE IF NOT EXISTS http_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    status_code INT,
    load_time_ms FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_host_timestamp (host, timestamp)
);