-- 班级考勤系统数据库物理模型
-- MySQL 8.0+
-- 字符集：utf8mb4
-- 设计说明：
-- 1. attendance_record 与 group_photo_recognition_detail 保留 emotion/emotion_confidence，
--    同时 emotion_record 汇聚情绪明细。这是有意的反范式设计，用少量冗余换取报表查询效率。
-- 2. emotion_record 使用真实外键关联 attendance_record 或 group_photo_recognition_detail，
--    避免 source_type/source_id 多态关联无法级联删除导致幽灵数据。
-- 3. 后端写入考勤或合照识别结果时，主表/明细表与 emotion_record 必须放在同一个数据库事务中。
--    要求要么全部提交，要么全部回滚，避免主业务记录与情绪汇总记录不一致。
-- 4. class_enrollment_history 保存班级归属历史，报表分母按历史归属计算，避免学生退学后历史出勤率失真。
-- 5. calendar_date 用于报表日期范围展开，避免递归 CTE 触发 cte_max_recursion_depth 上限。
-- 6. user_info 使用 active_username/active_student_id 生成列实现“仅活跃账号唯一”，避免软删除记录占住用户名。
-- 7. MySQL 不承担在线人脸向量检索。face_feature 仅作持久化备份，在线识别必须由算法服务加载到内存/Redis/FAISS等向量索引。
-- 8. user_info.token_version 用于 JWT 主动失效。用户停用、删除或重置密码时必须递增该字段。
-- 9. image_path/photo_path 为服务器内部存储键，不允许作为静态 URL 直接暴露给前端。

CREATE DATABASE IF NOT EXISTS attendance_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE attendance_db;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS emotion_record;
DROP TABLE IF EXISTS group_photo_recognition_detail;
DROP TABLE IF EXISTS attendance_record;
DROP TABLE IF EXISTS group_photo_record;
DROP TABLE IF EXISTS user_info;
DROP TABLE IF EXISTS class_enrollment_history;
DROP TABLE IF EXISTS calendar_date;
DROP TABLE IF EXISTS student_info;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE student_info (
  student_id VARCHAR(20) NOT NULL COMMENT '学号',
  name VARCHAR(50) NOT NULL COMMENT '姓名',
  class_name VARCHAR(50) NOT NULL COMMENT '班级',
  face_feature JSON NULL COMMENT '人脸特征向量JSON持久化备份，不用于在线全库扫描比对',
  face_feature_hash VARCHAR(64) NULL COMMENT '人脸特征哈希，用于缓存刷新和一致性校验',
  feature_version INT NOT NULL DEFAULT 1 COMMENT '人脸特征版本号，更新人脸时递增',
  feature_updated_at DATETIME NULL COMMENT '人脸特征更新时间',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0停用，1正常',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (student_id),
  INDEX idx_student_class_name (class_name),
  INDEX idx_student_class_status (class_name, status),
  INDEX idx_student_name (name),
  INDEX idx_student_feature_version (feature_version),
  CHECK (status IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生信息表';

CREATE TABLE calendar_date (
  stat_date DATE NOT NULL COMMENT '日期',
  year_num SMALLINT NOT NULL COMMENT '年份',
  month_num TINYINT NOT NULL COMMENT '月份',
  day_num TINYINT NOT NULL COMMENT '日',
  PRIMARY KEY (stat_date),
  INDEX idx_calendar_year_month (year_num, month_num)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报表日期维表';

CREATE TABLE class_enrollment_history (
  enrollment_id BIGINT NOT NULL AUTO_INCREMENT COMMENT '班级归属历史ID',
  student_id VARCHAR(20) NOT NULL COMMENT '学号',
  class_name VARCHAR(50) NOT NULL COMMENT '班级',
  enrolled_at DATETIME NOT NULL COMMENT '进入该班级时间',
  left_at DATETIME NULL COMMENT '离开该班级时间，NULL表示当前仍在该班',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (enrollment_id),
  INDEX idx_enrollment_class_time (class_name, enrolled_at, left_at),
  INDEX idx_enrollment_student_time (student_id, enrolled_at, left_at),
  UNIQUE KEY uk_enrollment_student_class_start (student_id, class_name, enrolled_at),
  CONSTRAINT fk_enrollment_student
    FOREIGN KEY (student_id) REFERENCES student_info(student_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CHECK (left_at IS NULL OR left_at > enrolled_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级归属历史表';

CREATE TABLE user_info (
  user_id VARCHAR(20) NOT NULL COMMENT '用户ID',
  username VARCHAR(50) NOT NULL COMMENT '用户名',
  password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
  role ENUM('teacher', 'student', 'admin') NOT NULL COMMENT '角色',
  student_id VARCHAR(20) NULL COMMENT '学生账号关联学号',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0停用，1正常',
  token_version INT NOT NULL DEFAULT 1 COMMENT '令牌版本号，递增后旧JWT立即失效',
  active_username VARCHAR(50) GENERATED ALWAYS AS (CASE WHEN status = 1 THEN username ELSE NULL END) STORED COMMENT '活跃账号用户名唯一索引用',
  active_student_id VARCHAR(20) GENERATED ALWAYS AS (CASE WHEN status = 1 AND role = 'student' THEN student_id ELSE NULL END) STORED COMMENT '活跃学生账号唯一索引用',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (user_id),
  INDEX idx_user_username (username),
  INDEX idx_user_role (role),
  UNIQUE KEY uk_user_active_username (active_username),
  UNIQUE KEY uk_user_active_student_id (active_student_id),
  CONSTRAINT fk_user_student
    FOREIGN KEY (student_id) REFERENCES student_info(student_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CHECK (status IN (0, 1)),
  CONSTRAINT chk_user_role_student_link CHECK (
    (role = 'student' AND student_id IS NOT NULL)
    OR (role IN ('teacher', 'admin') AND student_id IS NULL)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户信息表';

CREATE TABLE attendance_record (
  record_id BIGINT NOT NULL AUTO_INCREMENT COMMENT '考勤记录ID',
  student_id VARCHAR(20) NULL COMMENT '识别成功时关联学号',
  class_name VARCHAR(50) NULL COMMENT '考勤发生时的班级快照',
  status TINYINT NOT NULL COMMENT '考勤状态：0失败，1成功',
  confidence DECIMAL(5,2) NULL COMMENT '人脸匹配置信度，0-100',
  liveness_passed TINYINT NOT NULL DEFAULT 0 COMMENT '活体检测是否通过：0否，1是',
  liveness_score DECIMAL(5,2) NULL COMMENT '活体检测分数，0-100',
  spoof_type VARCHAR(30) NULL COMMENT '攻击类型：photo_attack/video_replay/screen_replay/unknown',
  failure_reason VARCHAR(50) NULL COMMENT '失败原因：no_face/multiple_faces/liveness_failed/face_not_matched/recognition_timeout等',
  emotion VARCHAR(20) NULL COMMENT '情绪类型',
  emotion_confidence DECIMAL(5,2) NULL COMMENT '情绪置信度，0-100',
  attendance_time DATETIME NOT NULL COMMENT '考勤时间',
  image_path VARCHAR(255) NULL COMMENT '考勤图片内部存储键，不允许直接作为公开URL',
  request_id VARCHAR(64) NULL COMMENT '请求追踪ID',
  idempotency_key VARCHAR(64) NULL COMMENT '前端幂等键，防止重复提交',
  device_id VARCHAR(64) NULL COMMENT '采集设备ID',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (record_id),
  INDEX idx_attendance_student_time (student_id, attendance_time),
  INDEX idx_attendance_class_time (class_name, attendance_time),
  INDEX idx_attendance_status_time (status, attendance_time),
  INDEX idx_attendance_emotion_time (emotion, attendance_time),
  INDEX idx_attendance_request_id (request_id),
  UNIQUE KEY uk_attendance_idempotency (idempotency_key),
  CONSTRAINT fk_attendance_student
    FOREIGN KEY (student_id) REFERENCES student_info(student_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CHECK (status IN (0, 1)),
  CHECK (liveness_passed IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='考勤记录表';

CREATE TABLE group_photo_record (
  photo_id BIGINT NOT NULL AUTO_INCREMENT COMMENT '合照记录ID',
  photo_name VARCHAR(255) NOT NULL COMMENT '照片名称',
  photo_path VARCHAR(255) NOT NULL COMMENT '照片内部存储键，不允许直接作为公开URL',
  activity_name VARCHAR(100) NULL COMMENT '活动名称',
  activity_time DATETIME NULL COMMENT '活动时间',
  total_faces INT NOT NULL DEFAULT 0 COMMENT '检测到的人脸数量',
  recognized_count INT NOT NULL DEFAULT 0 COMMENT '识别成功人数',
  unrecognized_count INT NOT NULL DEFAULT 0 COMMENT '未识别人数',
  created_by VARCHAR(20) NULL COMMENT '上传用户ID',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (photo_id),
  INDEX idx_group_photo_activity_time (activity_name, activity_time),
  INDEX idx_group_photo_created_at (created_at),
  INDEX idx_group_photo_created_by (created_by),
  CONSTRAINT fk_group_photo_user
    FOREIGN KEY (created_by) REFERENCES user_info(user_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合照识别记录表';

CREATE TABLE group_photo_recognition_detail (
  detail_id BIGINT NOT NULL AUTO_INCREMENT COMMENT '合照识别明细ID',
  photo_id BIGINT NOT NULL COMMENT '合照记录ID',
  student_id VARCHAR(20) NULL COMMENT '识别成功时关联学号',
  class_name VARCHAR(50) NULL COMMENT '活动发生时的班级快照',
  status TINYINT NOT NULL COMMENT '识别状态：0失败，1成功',
  confidence DECIMAL(5,2) NULL COMMENT '识别置信度，0-100',
  face_box JSON NULL COMMENT '人脸框坐标：x/y/width/height',
  emotion VARCHAR(20) NULL COMMENT '情绪类型',
  emotion_confidence DECIMAL(5,2) NULL COMMENT '情绪置信度，0-100',
  failure_reason VARCHAR(50) NULL COMMENT '失败原因',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (detail_id),
  INDEX idx_group_detail_photo (photo_id),
  INDEX idx_group_detail_student (student_id),
  INDEX idx_group_detail_class (class_name),
  INDEX idx_group_detail_emotion (emotion),
  UNIQUE KEY uk_group_detail_photo_student (photo_id, student_id),
  CONSTRAINT fk_group_detail_photo
    FOREIGN KEY (photo_id) REFERENCES group_photo_record(photo_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_group_detail_student
    FOREIGN KEY (student_id) REFERENCES student_info(student_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CHECK (status IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合照识别明细表';

CREATE TABLE emotion_record (
  emotion_id BIGINT NOT NULL AUTO_INCREMENT COMMENT '情绪记录ID',
  student_id VARCHAR(20) NULL COMMENT '学号',
  class_name VARCHAR(50) NULL COMMENT '业务发生时的班级快照',
  source_type ENUM('attendance', 'group_photo') NOT NULL COMMENT '来源类型',
  attendance_record_id BIGINT NULL COMMENT '考勤记录ID，source_type=attendance时必填',
  group_detail_id BIGINT NULL COMMENT '合照识别明细ID，source_type=group_photo时必填',
  emotion VARCHAR(20) NOT NULL COMMENT '情绪类型',
  confidence DECIMAL(5,2) NULL COMMENT '情绪置信度，0-100',
  detected_at DATETIME NOT NULL COMMENT '检测时间',
  face_box JSON NULL COMMENT '人脸框坐标',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (emotion_id),
  INDEX idx_emotion_student_time (student_id, detected_at),
  INDEX idx_emotion_class_time (class_name, detected_at),
  INDEX idx_emotion_type_time (emotion, detected_at),
  INDEX idx_emotion_source (source_type, attendance_record_id, group_detail_id),
  CONSTRAINT fk_emotion_student
    FOREIGN KEY (student_id) REFERENCES student_info(student_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CONSTRAINT fk_emotion_attendance
    FOREIGN KEY (attendance_record_id) REFERENCES attendance_record(record_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_emotion_group_detail
    FOREIGN KEY (group_detail_id) REFERENCES group_photo_recognition_detail(detail_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT chk_emotion_source CHECK (
    (source_type = 'attendance' AND attendance_record_id IS NOT NULL AND group_detail_id IS NULL)
    OR (source_type = 'group_photo' AND attendance_record_id IS NULL AND group_detail_id IS NOT NULL)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='情绪记录表';
