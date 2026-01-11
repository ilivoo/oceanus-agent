-- Oceanus Agent Database Initialization Script
-- Run this script to create the required tables

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS oceanus_agent
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE oceanus_agent;

-- Flink job exceptions table
CREATE TABLE IF NOT EXISTS flink_job_exceptions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    job_id VARCHAR(64) NOT NULL COMMENT 'Flink job ID',
    job_name VARCHAR(256) COMMENT 'Job name',
    job_type VARCHAR(32) COMMENT 'Job type (streaming/batch)',
    job_config JSON COMMENT 'Job configuration',
    error_message TEXT NOT NULL COMMENT 'Error message',
    error_type VARCHAR(64) COMMENT 'Classified error type',
    status VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT 'Diagnosis status: pending, in_progress, completed, failed',
    suggested_fix TEXT COMMENT 'Suggested fix (JSON format)',
    diagnosis_confidence FLOAT COMMENT 'Diagnosis confidence (0-1)',
    diagnosed_at DATETIME COMMENT 'Diagnosis completion time',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time',
    INDEX idx_status (status),
    INDEX idx_job_id (job_id),
    INDEX idx_error_type (error_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Flink job exception records';

-- Knowledge cases table
CREATE TABLE IF NOT EXISTS knowledge_cases (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    case_id VARCHAR(32) NOT NULL UNIQUE COMMENT 'Unique case identifier',
    error_type VARCHAR(64) NOT NULL COMMENT 'Error type',
    error_pattern TEXT COMMENT 'Generalized error pattern',
    root_cause TEXT NOT NULL COMMENT 'Root cause description',
    solution TEXT NOT NULL COMMENT 'Solution description',
    source_exception_id BIGINT COMMENT 'Source exception ID if auto-generated',
    source_type ENUM('manual', 'auto') NOT NULL DEFAULT 'manual' COMMENT 'Source type',
    verified BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Human verified flag',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time',
    INDEX idx_error_type (error_type),
    INDEX idx_source_type (source_type),
    INDEX idx_verified (verified),
    FOREIGN KEY (source_exception_id) REFERENCES flink_job_exceptions(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Knowledge base cases';

-- Insert some sample test data (optional)
-- Uncomment to add test data

/*
INSERT INTO flink_job_exceptions (job_id, job_name, job_type, error_message, error_type)
VALUES
('job-001', 'ETL Pipeline', 'streaming',
 'Checkpoint expired before completing. If you see this error consistently, consider increasing the checkpoint interval or timeout.',
 'checkpoint_failure'),

('job-002', 'Kafka Consumer', 'streaming',
 'java.io.NotSerializableException: org.example.MyClass at org.apache.flink.api.java.typeutils.runtime.kryo.KryoSerializer',
 'deserialization_error'),

('job-003', 'Data Aggregation', 'streaming',
 'High backpressure detected in operator window-aggregate. Task is running at 100% for extended period.',
 'backpressure');
*/
