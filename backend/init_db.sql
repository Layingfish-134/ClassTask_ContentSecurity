CREATE DATABASE IF NOT EXISTS attendance_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE attendance_db;

CREATE TABLE IF NOT EXISTS student_info (
    student_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    face_feature JSON DEFAULT NULL,
    face_feature_hash VARCHAR(64) DEFAULT NULL,
    feature_version INT NOT NULL DEFAULT 1,
    feature_updated_at DATETIME DEFAULT NULL,
    status SMALLINT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_info (
    user_id VARCHAR(20) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('teacher','student','admin') NOT NULL,
    student_id VARCHAR(20) DEFAULT NULL,
    status SMALLINT NOT NULL DEFAULT 1,
    token_version INT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_student FOREIGN KEY (student_id) REFERENCES student_info(student_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS attendance_record (
    record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) DEFAULT NULL,
    class_name VARCHAR(50) DEFAULT NULL,
    status SMALLINT NOT NULL,
    confidence DECIMAL(5,2) DEFAULT NULL,
    liveness_passed SMALLINT NOT NULL DEFAULT 0,
    liveness_score DECIMAL(5,2) DEFAULT NULL,
    spoof_type VARCHAR(30) DEFAULT NULL,
    failure_reason VARCHAR(50) DEFAULT NULL,
    emotion VARCHAR(20) DEFAULT NULL,
    emotion_confidence DECIMAL(5,2) DEFAULT NULL,
    attendance_time DATETIME NOT NULL,
    image_path VARCHAR(255) DEFAULT NULL,
    request_id VARCHAR(64) DEFAULT NULL,
    idempotency_key VARCHAR(64) DEFAULT NULL UNIQUE,
    device_id VARCHAR(64) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_attendance_student FOREIGN KEY (student_id) REFERENCES student_info(student_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS group_photo_record (
    photo_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    photo_name VARCHAR(255) NOT NULL,
    photo_path VARCHAR(255) NOT NULL,
    activity_name VARCHAR(100) DEFAULT NULL,
    activity_time DATETIME DEFAULT NULL,
    total_faces INT NOT NULL DEFAULT 0,
    recognized_count INT NOT NULL DEFAULT 0,
    unrecognized_count INT NOT NULL DEFAULT 0,
    created_by VARCHAR(20) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_photo_creator FOREIGN KEY (created_by) REFERENCES user_info(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS group_photo_recognition_detail (
    detail_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    photo_id BIGINT NOT NULL,
    student_id VARCHAR(20) DEFAULT NULL,
    class_name VARCHAR(50) DEFAULT NULL,
    status SMALLINT NOT NULL,
    confidence DECIMAL(5,2) DEFAULT NULL,
    face_box JSON DEFAULT NULL,
    emotion VARCHAR(20) DEFAULT NULL,
    emotion_confidence DECIMAL(5,2) DEFAULT NULL,
    failure_reason VARCHAR(50) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_detail_photo FOREIGN KEY (photo_id) REFERENCES group_photo_record(photo_id) ON DELETE CASCADE,
    CONSTRAINT fk_detail_student FOREIGN KEY (student_id) REFERENCES student_info(student_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS emotion_record (
    emotion_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) DEFAULT NULL,
    class_name VARCHAR(50) DEFAULT NULL,
    source_type ENUM('attendance','group_photo') NOT NULL,
    attendance_record_id BIGINT DEFAULT NULL,
    group_detail_id BIGINT DEFAULT NULL,
    emotion VARCHAR(20) NOT NULL,
    confidence DECIMAL(5,2) DEFAULT NULL,
    detected_at DATETIME NOT NULL,
    face_box JSON DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_emotion_student FOREIGN KEY (student_id) REFERENCES student_info(student_id) ON DELETE SET NULL,
    CONSTRAINT fk_emotion_attendance FOREIGN KEY (attendance_record_id) REFERENCES attendance_record(record_id) ON DELETE CASCADE,
    CONSTRAINT fk_emotion_group_detail FOREIGN KEY (group_detail_id) REFERENCES group_photo_recognition_detail(detail_id) ON DELETE CASCADE
);

CREATE INDEX idx_attendance_time ON attendance_record(attendance_time);
CREATE INDEX idx_attendance_student ON attendance_record(student_id);
CREATE INDEX idx_attendance_class ON attendance_record(class_name);
CREATE INDEX idx_attendance_liveness ON attendance_record(liveness_passed);
CREATE INDEX idx_attendance_idempotency ON attendance_record(idempotency_key);
CREATE INDEX idx_student_class ON student_info(class_name);
CREATE INDEX idx_student_status ON student_info(status);
CREATE INDEX idx_username ON user_info(username);
CREATE INDEX idx_user_role ON user_info(role);
CREATE INDEX idx_detail_photo ON group_photo_recognition_detail(photo_id);
CREATE INDEX idx_detail_student ON group_photo_recognition_detail(student_id);
CREATE INDEX idx_emotion_student ON emotion_record(student_id);
CREATE INDEX idx_emotion_source ON emotion_record(source_type);
CREATE INDEX idx_emotion_detected ON emotion_record(detected_at);
CREATE INDEX idx_photo_activity ON group_photo_record(activity_name);
