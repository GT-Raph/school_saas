from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    AttendanceRecord,
    AttendanceSession,
)


@transaction.atomic
def create_attendance_session(
    *,
    school,
    academic_year,
    term,
    class_section,
    attendance_date,
    taken_by=None,
):
    session = AttendanceSession(
        school=school,
        academic_year=academic_year,
        term=term,
        class_section=class_section,
        attendance_date=attendance_date,
        taken_by=taken_by,
    )

    session.full_clean()
    session.save()

    return session


@transaction.atomic
def save_attendance_records(
    *,
    session,
    attendance_data,
):
    """
    attendance_data example:

    [
        {
            "enrollment": enrollment,
            "status": "present",
            "remarks": "",
        },
        ...
    ]
    """

    if session.status == AttendanceSession.Status.LOCKED:
        raise ValidationError(
            "This attendance session is locked."
        )

    saved_records = []

    for item in attendance_data:
        enrollment = item["enrollment"]
        status = item["status"]
        remarks = item.get("remarks", "")

        record, _ = AttendanceRecord.objects.get_or_create(
            session=session,
            enrollment=enrollment,
            defaults={
                "school": session.school,
                "status": status,
                "remarks": remarks,
            },
        )

        record.school = session.school
        record.status = status
        record.remarks = remarks

        record.full_clean()
        record.save()

        saved_records.append(record)

    return saved_records