-- 专业考勤系统统计报表 SQL
-- 参数占位符使用 :param_name，后端封装时替换为框架实际语法。

USE attendance_db;

-- 1. 按日期统计专业出勤率
-- 参数：:class_name, :start_time, :end_time
-- 依赖 calendar_date 日期维表，避免递归 CTE 超过 MySQL cte_max_recursion_depth。
WITH date_range AS (
  SELECT stat_date
  FROM calendar_date
  WHERE stat_date BETWEEN DATE(:start_time) AND DATE(:end_time)
),
class_roster AS (
  SELECT
    dr.stat_date,
    :class_name AS class_name,
    COUNT(DISTINCT ceh.student_id) AS total_students
  FROM date_range dr
  LEFT JOIN class_enrollment_history ceh
    ON ceh.class_name = :class_name
    AND ceh.enrolled_at < DATE_ADD(dr.stat_date, INTERVAL 1 DAY)
    AND (ceh.left_at IS NULL OR ceh.left_at > dr.stat_date)
  GROUP BY dr.stat_date
),
daily_present AS (
  SELECT
    DATE(ar.attendance_time) AS attendance_date,
    ar.class_name,
    COUNT(DISTINCT ar.student_id) AS present_students
  FROM attendance_record ar
  WHERE ar.class_name = :class_name
    AND ar.status = 1
    AND ar.attendance_time BETWEEN :start_time AND :end_time
  GROUP BY DATE(ar.attendance_time), ar.class_name
)
SELECT
  cr.stat_date AS attendance_date,
  cr.class_name,
  cr.total_students,
  COALESCE(dp.present_students, 0) AS present_students,
  ROUND(COALESCE(dp.present_students, 0) * 100.0 / NULLIF(cr.total_students, 0), 2) AS attendance_rate
FROM class_roster cr
LEFT JOIN daily_present dp
  ON dp.attendance_date = cr.stat_date
  AND dp.class_name = cr.class_name
ORDER BY cr.stat_date;

-- 2. 查询某学生个人考勤记录
-- 参数：:student_id, :start_time, :end_time
SELECT
  ar.record_id,
  ar.student_id,
  si.name,
  COALESCE(ar.class_name, si.class_name) AS class_name,
  ar.status,
  ar.confidence,
  ar.liveness_passed,
  ar.liveness_score,
  ar.failure_reason,
  ar.emotion,
  ar.emotion_confidence,
  ar.attendance_time
FROM attendance_record ar
LEFT JOIN student_info si ON si.student_id = ar.student_id
WHERE ar.student_id = :student_id
  AND ar.attendance_time BETWEEN :start_time AND :end_time
ORDER BY ar.attendance_time DESC;

-- 3. 按活动统计参与名单
-- 参数：:activity_name
SELECT
  gpr.activity_name,
  gpr.activity_time,
  si.student_id,
  si.name,
  COALESCE(gprd.class_name, si.class_name) AS class_name,
  gprd.confidence,
  gprd.emotion,
  gprd.emotion_confidence
FROM group_photo_record gpr
JOIN group_photo_recognition_detail gprd ON gprd.photo_id = gpr.photo_id
JOIN student_info si ON si.student_id = gprd.student_id
WHERE gpr.activity_name = :activity_name
  AND gprd.status = 1
ORDER BY COALESCE(gprd.class_name, si.class_name), si.student_id;

-- 4. 按学生统计活动参与次数
-- 参数：:class_name, :activity_name, :start_time, :end_time
-- 统计主体是学生本人，专业快照只用于筛选，不参与最终分组，避免转班学生被拆成多行。
WITH participation AS (
  SELECT
    gprd.student_id,
    COUNT(DISTINCT gpr.photo_id) AS activity_count,
    MAX(gpr.activity_time) AS latest_activity_time
  FROM group_photo_recognition_detail gprd
  JOIN group_photo_record gpr ON gpr.photo_id = gprd.photo_id
  WHERE gprd.status = 1
    AND gprd.student_id IS NOT NULL
    AND (:class_name IS NULL OR gprd.class_name = :class_name)
    AND (:activity_name IS NULL OR gpr.activity_name = :activity_name)
    AND (:start_time IS NULL OR gpr.activity_time >= :start_time)
    AND (:end_time IS NULL OR gpr.activity_time <= :end_time)
  GROUP BY gprd.student_id
),
scoped_students AS (
  SELECT DISTINCT ceh.student_id
  FROM class_enrollment_history ceh
  WHERE :class_name IS NOT NULL
    AND ceh.class_name = :class_name
    AND (:start_time IS NULL OR ceh.left_at IS NULL OR ceh.left_at >= :start_time)
    AND (:end_time IS NULL OR ceh.enrolled_at <= :end_time)
)
SELECT
  si.student_id,
  si.name,
  CASE WHEN :class_name IS NULL THEN si.class_name ELSE :class_name END AS class_name,
  COALESCE(p.activity_count, 0) AS activity_count,
  p.latest_activity_time
FROM student_info si
LEFT JOIN participation p ON p.student_id = si.student_id
LEFT JOIN scoped_students ss ON ss.student_id = si.student_id
WHERE si.status = 1
  AND (
    :class_name IS NULL
    OR si.class_name = :class_name
    OR ss.student_id IS NOT NULL
    OR p.student_id IS NOT NULL
  )
ORDER BY activity_count DESC, latest_activity_time DESC, si.student_id;

-- 5. 按时间段统计情绪分布
-- 参数：:class_name, :student_id, :source_type, :start_time, :end_time
SELECT
  er.emotion,
  COUNT(*) AS emotion_count,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0), 2) AS emotion_ratio
FROM emotion_record er
WHERE (:class_name IS NULL OR er.class_name = :class_name)
  AND (:student_id IS NULL OR er.student_id = :student_id)
  AND (:source_type IS NULL OR er.source_type = :source_type)
  AND er.detected_at BETWEEN :start_time AND :end_time
GROUP BY er.emotion
ORDER BY emotion_count DESC;

-- 6. 按筛选条件统计每日情绪变化趋势
-- 参数：:class_name, :student_id, :source_type, :start_time, :end_time
SELECT
  DATE(er.detected_at) AS stat_date,
  SUM(CASE WHEN er.emotion = 'happy' THEN 1 ELSE 0 END) AS happy_count,
  SUM(CASE WHEN er.emotion = 'neutral' THEN 1 ELSE 0 END) AS neutral_count,
  SUM(CASE WHEN er.emotion = 'sad' THEN 1 ELSE 0 END) AS sad_count,
  SUM(CASE WHEN er.emotion = 'angry' THEN 1 ELSE 0 END) AS angry_count,
  SUM(CASE WHEN er.emotion = 'tired' THEN 1 ELSE 0 END) AS tired_count,
  SUM(CASE WHEN er.emotion = 'surprised' THEN 1 ELSE 0 END) AS surprised_count,
  SUM(CASE WHEN er.emotion = 'unknown' THEN 1 ELSE 0 END) AS unknown_count
FROM emotion_record er
WHERE (:class_name IS NULL OR er.class_name = :class_name)
  AND (:student_id IS NULL OR er.student_id = :student_id)
  AND (:source_type IS NULL OR er.source_type = :source_type)
  AND er.detected_at BETWEEN :start_time AND :end_time
GROUP BY DATE(er.detected_at)
ORDER BY stat_date;

-- 7. 导出考勤 Excel 明细查询
-- 参数：:class_name, :start_time, :end_time
SELECT
  COALESCE(ar.class_name, si.class_name) AS 专业,
  si.student_id AS 学号,
  si.name AS 姓名,
  CASE ar.status WHEN 1 THEN '成功' ELSE '失败' END AS 考勤状态,
  ar.confidence AS 人脸匹配置信度,
  CASE ar.liveness_passed WHEN 1 THEN '通过' ELSE '未通过' END AS 活体检测,
  ar.liveness_score AS 活体分数,
  ar.failure_reason AS 失败原因,
  ar.emotion AS 情绪,
  ar.emotion_confidence AS 情绪置信度,
  ar.attendance_time AS 考勤时间
FROM attendance_record ar
LEFT JOIN student_info si ON si.student_id = ar.student_id
WHERE (:class_name IS NULL OR COALESCE(ar.class_name, si.class_name) = :class_name)
  AND ar.attendance_time BETWEEN :start_time AND :end_time
ORDER BY COALESCE(ar.class_name, si.class_name), si.student_id, ar.attendance_time;

-- 8. 活体检测失败类型汇总
-- 参数：:start_time, :end_time
SELECT
  COALESCE(ar.spoof_type, ar.failure_reason, 'unknown') AS failure_type,
  COUNT(*) AS failure_count
FROM attendance_record ar
WHERE ar.status = 0
  AND ar.attendance_time BETWEEN :start_time AND :end_time
GROUP BY COALESCE(ar.spoof_type, ar.failure_reason, 'unknown')
ORDER BY failure_count DESC;

-- 9. 考勤记录游标分页查询（Keyset Pagination）
-- 参数：:class_name, :student_id, :status, :start_time, :end_time, :cursor_time, :cursor_id, :size
-- cursor_time/cursor_id 为空表示第一页；后端用最后一条记录生成 next_cursor。
SELECT
  ar.record_id,
  ar.student_id,
  si.name,
  COALESCE(ar.class_name, si.class_name) AS class_name,
  ar.status,
  ar.confidence,
  ar.liveness_passed,
  ar.liveness_score,
  ar.emotion,
  ar.emotion_confidence,
  ar.attendance_time
FROM attendance_record ar
LEFT JOIN student_info si ON si.student_id = ar.student_id
WHERE (:class_name IS NULL OR COALESCE(ar.class_name, si.class_name) = :class_name)
  AND (:student_id IS NULL OR ar.student_id = :student_id)
  AND (:status IS NULL OR ar.status = :status)
  AND (:start_time IS NULL OR ar.attendance_time >= :start_time)
  AND (:end_time IS NULL OR ar.attendance_time <= :end_time)
  AND (
    :cursor_time IS NULL
    OR ar.attendance_time < :cursor_time
    OR (ar.attendance_time = :cursor_time AND ar.record_id < :cursor_id)
  )
ORDER BY ar.attendance_time DESC, ar.record_id DESC
LIMIT :size;

-- 10. 合照记录游标分页查询（Keyset Pagination）
-- 参数：:activity_name, :class_name, :start_time, :end_time, :cursor_time, :cursor_id, :size
SELECT
  gpr.photo_id,
  gpr.photo_name,
  gpr.activity_name,
  gpr.activity_time,
  gpr.total_faces,
  gpr.recognized_count,
  gpr.unrecognized_count,
  gpr.created_at
FROM group_photo_record gpr
WHERE (:activity_name IS NULL OR gpr.activity_name = :activity_name)
  AND (:start_time IS NULL OR gpr.activity_time >= :start_time)
  AND (:end_time IS NULL OR gpr.activity_time <= :end_time)
  AND (
    :class_name IS NULL
    OR EXISTS (
      SELECT 1
      FROM group_photo_recognition_detail gprd
      WHERE gprd.photo_id = gpr.photo_id
        AND gprd.class_name = :class_name
    )
  )
  AND (
    :cursor_time IS NULL
    OR gpr.activity_time < :cursor_time
    OR (gpr.activity_time = :cursor_time AND gpr.photo_id < :cursor_id)
  )
ORDER BY gpr.activity_time DESC, gpr.photo_id DESC
LIMIT :size;
