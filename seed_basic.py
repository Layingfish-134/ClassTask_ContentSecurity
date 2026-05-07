"""Generate phase-two basic seed SQL for the attendance system.

The output SQL should be imported after database_schema.sql:

    python seed_basic.py --output seed_basic.sql
    mysql -u root -p attendance_db < seed_basic.sql
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence


RANDOM_SEED = 20260506
PASSWORD_HASH = "demo_hash_123456"
FEATURE_UPDATED_AT = "2026-05-06 08:00:00"
ENROLLMENT_START = "2025-09-01 08:00:00"
TRANSFER_TIME = "2026-04-20 00:00:00"

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

SURNAMES = [
    "赵",
    "钱",
    "孙",
    "李",
    "周",
    "吴",
    "郑",
    "王",
    "冯",
    "陈",
    "褚",
    "卫",
    "蒋",
    "沈",
    "韩",
    "杨",
    "朱",
    "秦",
    "尤",
    "许",
    "何",
    "吕",
    "施",
    "张",
    "孔",
    "曹",
    "严",
    "华",
    "金",
    "魏",
]

GIVEN_NAMES = [
    "子涵",
    "宇轩",
    "梓萱",
    "浩然",
    "欣怡",
    "思源",
    "雨桐",
    "俊杰",
    "嘉怡",
    "明哲",
    "若曦",
    "博文",
    "一诺",
    "可欣",
    "泽宇",
    "诗涵",
    "晨曦",
    "佳宁",
    "睿泽",
    "雅琪",
    "景行",
    "安然",
    "沐阳",
    "书瑶",
    "承泽",
    "星辰",
    "知远",
    "亦航",
    "昕然",
    "靖雯",
    "子墨",
    "思齐",
    "嘉懿",
    "清扬",
    "映雪",
    "致远",
    "语彤",
    "逸飞",
    "初阳",
    "佳航",
]


@dataclass(frozen=True)
class Student:
    student_id: str
    name: str
    class_name: str


def sql_string(value: str | date | datetime | None) -> str:
    if value is None:
        return "NULL"
    text = value.isoformat() if isinstance(value, (date, datetime)) else value
    return "'" + text.replace("\\", "\\\\").replace("'", "''") + "'"


def fake_face_feature(rng: random.Random) -> str:
    vector = [round(rng.uniform(-1.0, 1.0), 6) for _ in range(128)]
    return json.dumps(vector, ensure_ascii=False, separators=(",", ":"))


def feature_hash(face_feature: str) -> str:
    return hashlib.sha256(face_feature.encode("utf-8")).hexdigest()


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


def build_students(rng: random.Random) -> list[Student]:
    names: set[str] = set()
    students: list[Student] = []
    student_index = 1

    for class_name, count in CLASSES:
        for _ in range(count):
            while True:
                candidate = rng.choice(SURNAMES) + rng.choice(GIVEN_NAMES)
                if candidate not in names:
                    names.add(candidate)
                    break
            students.append(
                Student(
                    student_id=f"2024{student_index:04d}",
                    name=candidate,
                    class_name=class_name,
                )
            )
            student_index += 1

    return students


def build_calendar_rows() -> list[str]:
    rows: list[str] = []
    current_date = date(2024, 1, 1)
    end_date = date(2026, 12, 31)
    while current_date <= end_date:
        rows.append(
            "  ("
            f"{sql_string(current_date)}, "
            f"{current_date.year}, "
            f"{current_date.month}, "
            f"{current_date.day}"
            ")"
        )
        current_date += timedelta(days=1)
    return rows


def build_user_rows(students: Sequence[Student]) -> list[str]:
    rows = [
        "  ('u_admin_001', 'admin', 'demo_hash_123456', 'admin', NULL, 1, 1)",
        "  ('u_teacher_001', 'teacher01', 'demo_hash_123456', 'teacher', NULL, 1, 1)",
        "  ('u_teacher_002', 'teacher02', 'demo_hash_123456', 'teacher', NULL, 1, 1)",
        "  ('u_teacher_003', 'teacher03', 'demo_hash_123456', 'teacher', NULL, 1, 1)",
    ]
    for student in students:
        rows.append(
            "  ("
            f"{sql_string('u_student_' + student.student_id)}, "
            f"{sql_string(student.student_id)}, "
            f"{sql_string(PASSWORD_HASH)}, "
            "'student', "
            f"{sql_string(student.student_id)}, "
            "1, "
            "1"
            ")"
        )
    return rows


def build_student_rows(students: Sequence[Student], rng: random.Random) -> list[str]:
    rows: list[str] = []
    for student in students:
        face_feature = fake_face_feature(rng)
        rows.append(
            "  ("
            f"{sql_string(student.student_id)}, "
            f"{sql_string(student.name)}, "
            f"{sql_string(student.class_name)}, "
            f"CAST({sql_string(face_feature)} AS JSON), "
            f"{sql_string(feature_hash(face_feature))}, "
            "1, "
            f"{sql_string(FEATURE_UPDATED_AT)}, "
            "1"
            ")"
        )
    return rows


def build_enrollment_rows(students: Sequence[Student]) -> list[str]:
    rows: list[str] = []
    for student in students:
        old_class = TRANSFER_OLD_CLASS.get(student.student_id)
        if old_class:
            rows.append(
                "  ("
                f"{sql_string(student.student_id)}, "
                f"{sql_string(old_class)}, "
                f"{sql_string(ENROLLMENT_START)}, "
                f"{sql_string(TRANSFER_TIME)}"
                ")"
            )
            rows.append(
                "  ("
                f"{sql_string(student.student_id)}, "
                f"{sql_string(student.class_name)}, "
                f"{sql_string(TRANSFER_TIME)}, "
                "NULL"
                ")"
            )
        else:
            rows.append(
                "  ("
                f"{sql_string(student.student_id)}, "
                f"{sql_string(student.class_name)}, "
                f"{sql_string(ENROLLMENT_START)}, "
                "NULL"
                ")"
            )
    return rows


def build_sql() -> str:
    rng = random.Random(RANDOM_SEED)
    students = build_students(rng)

    lines: list[str] = [
        "-- Phase-two basic seed data for attendance_db",
        "-- Includes calendar_date, users, students, face features, and class enrollment history.",
        "USE attendance_db;",
        "START TRANSACTION;",
        "",
    ]

    lines.extend(
        insert_batches(
            "calendar_date",
            ["stat_date", "year_num", "month_num", "day_num"],
            build_calendar_rows(),
            [
                "year_num",
                "month_num",
                "day_num",
            ],
        )
    )

    lines.extend(
        insert_batches(
            "student_info",
            [
                "student_id",
                "name",
                "class_name",
                "face_feature",
                "face_feature_hash",
                "feature_version",
                "feature_updated_at",
                "status",
            ],
            build_student_rows(students, rng),
            [
                "name",
                "class_name",
                "face_feature",
                "face_feature_hash",
                "feature_version",
                "feature_updated_at",
                "status",
            ],
        )
    )

    lines.extend(
        insert_batches(
            "class_enrollment_history",
            ["student_id", "class_name", "enrolled_at", "left_at"],
            build_enrollment_rows(students),
            ["left_at"],
        )
    )

    lines.extend(
        insert_batches(
            "user_info",
            [
                "user_id",
                "username",
                "password_hash",
                "role",
                "student_id",
                "status",
                "token_version",
            ],
            build_user_rows(students),
            [
                "username",
                "password_hash",
                "role",
                "student_id",
                "status",
                "token_version",
            ],
        )
    )

    lines.extend(["COMMIT;", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate phase-two basic seed SQL.")
    parser.add_argument("--output", default="seed_basic.sql", help="Output SQL file path.")
    args = parser.parse_args()

    output = Path(args.output)
    output.write_text(build_sql(), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
