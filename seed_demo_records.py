"""Generate phase-two demo attendance, emotion, and group-photo SQL.

Run seed_basic.sql first so referenced students and users exist:

    python seed_demo_records.py --output seed_demo_records.sql
    mysql -u root -p attendance_db < seed_demo_records.sql
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable, Sequence


RANDOM_SEED = 20260506
TRANSFER_AT = datetime(2026, 4, 20, 0, 0, 0)
ATTENDANCE_START = date(2026, 4, 7)
ATTENDANCE_END = date(2026, 5, 6)
HOLIDAYS = {date(2026, 5, 1), date(2026, 5, 2), date(2026, 5, 3)}

CLASSES = [
    ("网安2401班", 34),
    ("网安2402班", 33),
    ("信安2401班", 33),
]

TRANSFER_OLD_CLASS = {
    "20240012": "信安2401班",
    "20240036": "网安2401班",
    "20240055": "信安2401班",
    "20240082": "网安2402班",
    "20240099": "网安2401班",
}

HABITUAL_STUDENTS = ["20240098", "20240099", "20240100"]
HABITUAL_WEIGHTS = {"20240098": 3, "20240099": 4, "20240100": 3}
DEVICE_ID = "seed_web_camera_001"

NORMAL_EMOTION_WEIGHTS = [
    ("neutral", 0.70),
    ("happy", 0.20),
    ("tired", 0.03),
    ("surprised", 0.02),
    ("sad", 0.02),
    ("angry", 0.01),
    ("unknown", 0.02),
]

LOW_DAY_EMOTION_WEIGHTS = [
    ("neutral", 0.45),
    ("tired", 0.30),
    ("sad", 0.15),
    ("happy", 0.05),
    ("surprised", 0.02),
    ("angry", 0.01),
    ("unknown", 0.02),
]

ACTIVITIES = [
    ("春季运动会合影", datetime(2026, 4, 10, 10, 0, 0)),
    ("实验课合照", datetime(2026, 4, 16, 15, 0, 0)),
    ("安全教育讲座", datetime(2026, 4, 23, 10, 0, 0)),
    ("课程设计讨论", datetime(2026, 4, 29, 15, 0, 0)),
    ("班级团日活动", datetime(2026, 5, 6, 16, 0, 0)),
]


@dataclass(frozen=True)
class Student:
    student_id: str
    name: str
    class_name: str


@dataclass(frozen=True)
class AttendanceEvent:
    student_id: str
    class_name: str
    attendance_time: datetime
    low_day: bool


def sql_string(value: str | date | datetime | None) -> str:
    if value is None:
        return "NULL"
    text = value.strftime("%Y-%m-%d %H:%M:%S") if isinstance(value, datetime) else value.isoformat() if isinstance(value, date) else value
    return "'" + text.replace("\\", "\\\\").replace("'", "''") + "'"


def sql_number(value: float | int | None) -> str:
    return "NULL" if value is None else str(value)


def chunked(rows: Sequence[str], size: int = 500) -> Iterable[Sequence[str]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


def insert_batches(
    table: str,
    columns: Sequence[str],
    rows: Sequence[str],
    update_columns: Sequence[str],
    batch_size: int = 500,
) -> list[str]:
    if not rows:
        return [f"-- No seed rows for {table}."]

    lines: list[str] = []
    column_sql = ", ".join(columns)
    update_sql = ",\n  ".join(f"{column} = incoming.{column}" for column in update_columns)
    for index, batch in enumerate(chunked(rows, batch_size), start=1):
        lines.extend(
            [
                f"-- {table} batch {index}",
                f"INSERT INTO {table} ({column_sql}) VALUES",
                ",\n".join(batch),
                "AS incoming",
                "ON DUPLICATE KEY UPDATE",
                f"  {update_sql};",
                "",
            ]
        )
    return lines


def student_roster() -> list[Student]:
    students: list[Student] = []
    student_index = 1
    for class_name, count in CLASSES:
        for _ in range(count):
            student_id = f"2024{student_index:04d}"
            students.append(Student(student_id=student_id, name=f"学生{student_index:03d}", class_name=class_name))
            student_index += 1
    return students


def class_at(student: Student, happened_at: datetime) -> str:
    old_class = TRANSFER_OLD_CLASS.get(student.student_id)
    if old_class and happened_at < TRANSFER_AT:
        return old_class
    return student.class_name


def is_low_day(day: date) -> bool:
    return day.weekday() >= 5 or day in HOLIDAYS


def random_business_time(rng: random.Random, day: date) -> datetime:
    start = datetime.combine(day, time(8, 0, 0))
    return start + timedelta(minutes=rng.randint(0, 599), seconds=rng.randint(0, 59))


def choose_emotion(rng: random.Random, low_day: bool) -> str:
    weights = LOW_DAY_EMOTION_WEIGHTS if low_day else NORMAL_EMOTION_WEIGHTS
    roll = rng.random()
    total = 0.0
    for emotion, weight in weights:
        total += weight
        if roll <= total:
            return emotion
    return "neutral"


def emotion_confidence(rng: random.Random, emotion: str) -> float:
    if emotion == "unknown":
        return round(rng.uniform(48, 68), 2)
    if emotion in {"tired", "sad", "angry"}:
        return round(rng.uniform(70, 91), 2)
    return round(rng.uniform(80, 98), 2)


def face_box(rng: random.Random) -> str:
    box = {
        "x": rng.randint(20, 500),
        "y": rng.randint(20, 300),
        "width": rng.randint(70, 130),
        "height": rng.randint(70, 130),
    }
    return json.dumps(box, ensure_ascii=False, separators=(",", ":"))


def build_attendance_events(rng: random.Random, students: Sequence[Student]) -> list[AttendanceEvent]:
    events: list[AttendanceEvent] = []
    student_by_id = {student.student_id: student for student in students}
    current_day = ATTENDANCE_START
    while current_day <= ATTENDANCE_END:
        low_day = is_low_day(current_day)
        if current_day in HOLIDAYS:
            target_count = rng.randint(3, 8)
        elif current_day.weekday() >= 5:
            target_count = rng.randint(5, 12)
        else:
            target_count = len(students)

        if low_day:
            selected_ids = list(HABITUAL_STUDENTS)
            candidates = [student.student_id for student in students if student.student_id not in selected_ids]
            selected_ids.extend(rng.sample(candidates, max(0, target_count - len(selected_ids))))
            selected = [student_by_id[student_id] for student_id in selected_ids[:target_count]]
        else:
            selected = list(students)

        for student in selected:
            attendance_time = random_business_time(rng, current_day)
            events.append(
                AttendanceEvent(
                    student_id=student.student_id,
                    class_name=class_at(student, attendance_time),
                    attendance_time=attendance_time,
                    low_day=low_day,
                )
            )
        current_day += timedelta(days=1)

    return events


def weighted_take(
    rng: random.Random,
    events: Sequence[AttendanceEvent],
    available: set[int],
    candidate_ids: set[str],
    count: int,
) -> list[int]:
    bucket = [index for index in available if events[index].student_id in candidate_ids]
    chosen: list[int] = []
    while bucket and len(chosen) < count:
        weights = [HABITUAL_WEIGHTS.get(events[index].student_id, 1) for index in bucket]
        selected_pos = rng.choices(range(len(bucket)), weights=weights, k=1)[0]
        chosen.append(bucket.pop(selected_pos))
    return chosen


def random_take(rng: random.Random, available: set[int], count: int, exclude_ids: set[str] | None, events: Sequence[AttendanceEvent]) -> list[int]:
    candidates = [
        index
        for index in available
        if exclude_ids is None or events[index].student_id not in exclude_ids
    ]
    if len(candidates) <= count:
        return candidates
    return rng.sample(candidates, count)


def assign_attendance_categories(rng: random.Random, events: Sequence[AttendanceEvent]) -> dict[int, str]:
    total = len(events)
    liveness_count = round(total * 0.05)
    match_count = round(total * 0.05)
    timeout_count = round(total * 0.02)
    categories: dict[int, str] = {}
    available = set(range(total))
    habitual_ids = set(HABITUAL_STUDENTS)

    liveness_habitual_count = min(len(available), int(liveness_count * 0.65))
    chosen = weighted_take(rng, events, available, habitual_ids, liveness_habitual_count)
    for index in chosen:
        categories[index] = "liveness_attack"
        available.remove(index)
    for index in random_take(rng, available, liveness_count - len(chosen), habitual_ids, events):
        categories[index] = "liveness_attack"
        available.remove(index)

    match_habitual_count = int(match_count * 0.35)
    chosen = weighted_take(rng, events, available, habitual_ids, match_habitual_count)
    for index in chosen:
        categories[index] = "face_not_matched"
        available.remove(index)
    for index in random_take(rng, available, match_count - len(chosen), None, events):
        categories[index] = "face_not_matched"
        available.remove(index)

    for index in random_take(rng, available, timeout_count, None, events):
        categories[index] = "recognition_timeout"
        available.remove(index)

    for index in available:
        categories[index] = "success"

    return categories


def build_attendance_and_emotion_rows(rng: random.Random, students: Sequence[Student]) -> tuple[list[str], list[str], dict[str, int]]:
    events = build_attendance_events(rng, students)
    categories = assign_attendance_categories(rng, events)
    attendance_rows: list[str] = []
    emotion_rows: list[str] = []
    stats = {"success": 0, "liveness_attack": 0, "face_not_matched": 0, "recognition_timeout": 0}

    record_id = 100000
    emotion_id = 200000
    spoof_cycle = ["photo_attack", "video_replay", "screen_replay"]

    for index, event in enumerate(events):
        record_id += 1
        category = categories[index]
        stats[category] += 1
        status = 1 if category == "success" else 0
        confidence: float | None
        liveness_passed: int
        liveness_score: float | None
        spoof_type: str | None = None
        failure_reason: str | None = None
        emotion: str | None = None
        confidence_emotion: float | None = None

        if category == "success":
            confidence = round(rng.uniform(86, 99), 2)
            liveness_passed = 1
            liveness_score = round(rng.uniform(88, 99), 2)
            emotion = choose_emotion(rng, event.low_day)
            confidence_emotion = emotion_confidence(rng, emotion)
        elif category == "liveness_attack":
            confidence = round(rng.uniform(15, 50), 2)
            liveness_passed = 0
            liveness_score = round(rng.uniform(5, 45), 2)
            spoof_type = spoof_cycle[index % len(spoof_cycle)]
            failure_reason = "liveness_failed"
        elif category == "face_not_matched":
            confidence = round(rng.uniform(18, 62), 2)
            liveness_passed = 1
            liveness_score = round(rng.uniform(86, 99), 2)
            failure_reason = "face_not_matched"
        else:
            confidence = None
            liveness_passed = 0
            liveness_score = None
            failure_reason = "recognition_timeout"

        timestamp_key = event.attendance_time.strftime("%Y%m%d%H%M%S")
        idempotency_key = f"checkin_{event.student_id}_{timestamp_key}_{DEVICE_ID}"

        attendance_rows.append(
            "  ("
            f"{record_id}, "
            f"{sql_string(event.student_id)}, "
            f"{sql_string(event.class_name)}, "
            f"{status}, "
            f"{sql_number(confidence)}, "
            f"{liveness_passed}, "
            f"{sql_number(liveness_score)}, "
            f"{sql_string(spoof_type)}, "
            f"{sql_string(failure_reason)}, "
            f"{sql_string(emotion)}, "
            f"{sql_number(confidence_emotion)}, "
            f"{sql_string(event.attendance_time)}, "
            f"{sql_string(f'attendance/{event.attendance_time:%Y%m%d}/{record_id}.jpg')}, "
            f"{sql_string('req_seed_att_' + str(record_id))}, "
            f"{sql_string(idempotency_key)}, "
            f"{sql_string(DEVICE_ID)}"
            ")"
        )

        if category == "success" and emotion is not None:
            emotion_id += 1
            emotion_rows.append(
                "  ("
                f"{emotion_id}, "
                f"{sql_string(event.student_id)}, "
                f"{sql_string(event.class_name)}, "
                "'attendance', "
                f"{record_id}, "
                "NULL, "
                f"{sql_string(emotion)}, "
                f"{sql_number(confidence_emotion)}, "
                f"{sql_string(event.attendance_time)}, "
                "NULL"
                ")"
            )

    stats["attendance_total"] = len(attendance_rows)
    stats["attendance_emotions"] = len(emotion_rows)
    return attendance_rows, emotion_rows, stats


def build_group_photo_rows(
    rng: random.Random,
    students: Sequence[Student],
    starting_emotion_id: int,
) -> tuple[list[str], list[str], list[str], int]:
    student_by_id = {student.student_id: student for student in students}
    transfer_students = [student_by_id[student_id] for student_id in TRANSFER_OLD_CLASS]
    photo_rows: list[str] = []
    detail_rows: list[str] = []
    emotion_rows: list[str] = []
    photo_id = 300000
    detail_id = 400000
    emotion_id = starting_emotion_id

    for activity_name, activity_time in ACTIVITIES:
        photo_id += 1
        sample_size = rng.randint(34, 48)
        selected = list(transfer_students)
        remaining = [student for student in students if student.student_id not in TRANSFER_OLD_CLASS]
        selected.extend(rng.sample(remaining, sample_size - len(selected)))
        unrecognized_count = rng.randint(1, 4)
        total_faces = len(selected) + unrecognized_count

        photo_rows.append(
            "  ("
            f"{photo_id}, "
            f"{sql_string(activity_name + '.jpg')}, "
            f"{sql_string(f'group_photos/{photo_id}.jpg')}, "
            f"{sql_string(activity_name)}, "
            f"{sql_string(activity_time)}, "
            f"{total_faces}, "
            f"{len(selected)}, "
            f"{unrecognized_count}, "
            "'u_teacher_001'"
            ")"
        )

        for student in selected:
            detail_id += 1
            emotion_id += 1
            class_name = class_at(student, activity_time)
            emotion = choose_emotion(rng, is_low_day(activity_time.date()))
            confidence = emotion_confidence(rng, emotion)
            box = face_box(rng)

            detail_rows.append(
                "  ("
                f"{detail_id}, "
                f"{photo_id}, "
                f"{sql_string(student.student_id)}, "
                f"{sql_string(class_name)}, "
                "1, "
                f"{round(rng.uniform(82, 99), 2)}, "
                f"CAST({sql_string(box)} AS JSON), "
                f"{sql_string(emotion)}, "
                f"{confidence}, "
                "NULL"
                ")"
            )

            emotion_rows.append(
                "  ("
                f"{emotion_id}, "
                f"{sql_string(student.student_id)}, "
                f"{sql_string(class_name)}, "
                "'group_photo', "
                "NULL, "
                f"{detail_id}, "
                f"{sql_string(emotion)}, "
                f"{confidence}, "
                f"{sql_string(activity_time)}, "
                f"CAST({sql_string(box)} AS JSON)"
                ")"
            )

        for _ in range(unrecognized_count):
            detail_id += 1
            box = face_box(rng)
            detail_rows.append(
                "  ("
                f"{detail_id}, "
                f"{photo_id}, "
                "NULL, "
                "NULL, "
                "0, "
                "NULL, "
                f"CAST({sql_string(box)} AS JSON), "
                "NULL, "
                "NULL, "
                "'face_not_matched'"
                ")"
            )

    return photo_rows, detail_rows, emotion_rows, emotion_id


def build_sql() -> str:
    rng = random.Random(RANDOM_SEED)
    students = student_roster()
    attendance_rows, attendance_emotion_rows, stats = build_attendance_and_emotion_rows(rng, students)
    photo_rows, detail_rows, group_emotion_rows, _last_emotion_id = build_group_photo_rows(
        rng,
        students,
        starting_emotion_id=200000 + stats["attendance_emotions"],
    )
    emotion_rows = attendance_emotion_rows + group_emotion_rows

    lines: list[str] = [
        "-- Phase-two demo records for attendance_db",
        f"-- Attendance total: {stats['attendance_total']}",
        f"-- Attendance success: {stats['success']}",
        f"-- Liveness attacks: {stats['liveness_attack']}",
        f"-- Face not matched: {stats['face_not_matched']}",
        f"-- Recognition timeouts: {stats['recognition_timeout']}",
        f"-- Attendance emotion records: {stats['attendance_emotions']}",
        f"-- Group photo records: {len(photo_rows)}",
        f"-- Group photo detail records: {len(detail_rows)}",
        "USE attendance_db;",
        "START TRANSACTION;",
        "",
    ]

    lines.extend(
        insert_batches(
            "attendance_record",
            [
                "record_id",
                "student_id",
                "class_name",
                "status",
                "confidence",
                "liveness_passed",
                "liveness_score",
                "spoof_type",
                "failure_reason",
                "emotion",
                "emotion_confidence",
                "attendance_time",
                "image_path",
                "request_id",
                "idempotency_key",
                "device_id",
            ],
            attendance_rows,
            [
                "student_id",
                "class_name",
                "status",
                "confidence",
                "liveness_passed",
                "liveness_score",
                "spoof_type",
                "failure_reason",
                "emotion",
                "emotion_confidence",
                "attendance_time",
                "image_path",
                "request_id",
                "idempotency_key",
                "device_id",
            ],
        )
    )

    lines.extend(
        insert_batches(
            "group_photo_record",
            [
                "photo_id",
                "photo_name",
                "photo_path",
                "activity_name",
                "activity_time",
                "total_faces",
                "recognized_count",
                "unrecognized_count",
                "created_by",
            ],
            photo_rows,
            [
                "photo_name",
                "photo_path",
                "activity_name",
                "activity_time",
                "total_faces",
                "recognized_count",
                "unrecognized_count",
                "created_by",
            ],
        )
    )

    lines.extend(
        insert_batches(
            "group_photo_recognition_detail",
            [
                "detail_id",
                "photo_id",
                "student_id",
                "class_name",
                "status",
                "confidence",
                "face_box",
                "emotion",
                "emotion_confidence",
                "failure_reason",
            ],
            detail_rows,
            [
                "photo_id",
                "student_id",
                "class_name",
                "status",
                "confidence",
                "face_box",
                "emotion",
                "emotion_confidence",
                "failure_reason",
            ],
        )
    )

    lines.extend(
        insert_batches(
            "emotion_record",
            [
                "emotion_id",
                "student_id",
                "class_name",
                "source_type",
                "attendance_record_id",
                "group_detail_id",
                "emotion",
                "confidence",
                "detected_at",
                "face_box",
            ],
            emotion_rows,
            [
                "student_id",
                "class_name",
                "source_type",
                "attendance_record_id",
                "group_detail_id",
                "emotion",
                "confidence",
                "detected_at",
                "face_box",
            ],
        )
    )

    lines.extend(["COMMIT;", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate phase-two demo record seed SQL.")
    parser.add_argument("--output", default="seed_demo_records.sql", help="Output SQL file path.")
    args = parser.parse_args()

    output = Path(args.output)
    output.write_text(build_sql(), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
