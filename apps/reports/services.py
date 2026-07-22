import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.assessments.models import (
    OfferingAssessmentPlan,
    SubjectResult,
)
from apps.attendance.models import (
    AttendanceRecord,
    AttendanceSession,
)

from .models import (
    ReportCard,
    TermResult,
)


def calculate_attendance_percentage(
    *,
    enrollment,
    term,
):
    """
    V1 attendance logic:

    PRESENT = attended
    LATE = attended

    ABSENT = not attended
    SICK = not attended

    EXCUSED = excluded from denominator

    This can become configurable later.
    """

    records = (
        AttendanceRecord.objects
        .filter(
            enrollment=enrollment,
            session__term=term,
            session__status__in=[
                AttendanceSession.Status.SUBMITTED,
                AttendanceSession.Status.LOCKED,
            ],
        )
        .exclude(
            status=AttendanceRecord.Status.EXCUSED
        )
    )

    total = records.count()

    if total == 0:
        return None

    attended = records.filter(
        status__in=[
            AttendanceRecord.Status.PRESENT,
            AttendanceRecord.Status.LATE,
        ]
    ).count()

    percentage = (
        Decimal(attended)
        / Decimal(total)
        * Decimal("100")
    )

    return percentage.quantize(
        Decimal("0.01")
    )


@transaction.atomic
def calculate_term_result(
    *,
    enrollment,
    term,
):
    """
    Calculate the student's overall term result.

    All expected subject results must first be APPROVED
    or PUBLISHED.
    """

    if (
        enrollment.academic_year_id
        != term.academic_year_id
    ):
        raise ValidationError(
            "Enrollment and term belong "
            "to different academic years."
        )

    existing = (
        TermResult.objects
        .filter(
            enrollment=enrollment,
            term=term,
        )
        .first()
    )

    if (
        existing
        and existing.status
        == TermResult.Status.PUBLISHED
    ):
        raise ValidationError(
            "A published term result cannot "
            "be recalculated."
        )

    plans = (
        OfferingAssessmentPlan.objects
        .filter(
            school=enrollment.school,
            term=term,
            offering__academic_year=(
                enrollment.academic_year
            ),
            offering__class_section=(
                enrollment.class_section
            ),
        )
        .select_related(
            "offering__subject"
        )
    )

    if not plans.exists():
        raise ValidationError(
            "No subject assessment plans exist "
            "for this class and term."
        )

    subject_results = []

    for plan in plans:

        result = (
            SubjectResult.objects
            .filter(
                assessment_plan=plan,
                enrollment=enrollment,
                status__in=[
                    SubjectResult.Status.APPROVED,
                    SubjectResult.Status.PUBLISHED,
                ],
            )
            .first()
        )

        if not result:
            raise ValidationError(
                f"Missing approved result for "
                f"{plan.offering.subject.name}."
            )

        subject_results.append(
            result
        )

    total_score = sum(
        (
            result.total_score
            for result in subject_results
        ),
        Decimal("0"),
    )

    average = (
        total_score
        / Decimal(
            len(subject_results)
        )
    ).quantize(
        Decimal("0.01")
    )

    failed = sum(
        1
        for result in subject_results
        if not result.is_pass
    )

    attendance_percentage = (
        calculate_attendance_percentage(
            enrollment=enrollment,
            term=term,
        )
    )

    term_result, _ = (
        TermResult.objects.update_or_create(
            enrollment=enrollment,
            term=term,
            defaults={
                "school": (
                    enrollment.school
                ),
                "average_score": average,
                "total_subjects": (
                    len(subject_results)
                ),
                "failed_subjects": failed,
                "attendance_percentage": (
                    attendance_percentage
                ),
            },
        )
    )

    term_result.full_clean()
    term_result.save()

    return term_result


@transaction.atomic
def update_term_comments(
    *,
    term_result,
    class_teacher_comment=None,
    headteacher_comment=None,
):
    if (
        term_result.status
        == TermResult.Status.PUBLISHED
    ):
        raise ValidationError(
            "Published reports cannot be edited."
        )

    if class_teacher_comment is not None:
        term_result.class_teacher_comment = (
            class_teacher_comment
        )

    if headteacher_comment is not None:
        term_result.headteacher_comment = (
            headteacher_comment
        )

    term_result.full_clean()
    term_result.save()

    return term_result


@transaction.atomic
def approve_term_result(
    *,
    term_result,
    user,
):
    if (
        term_result.status
        != TermResult.Status.DRAFT
    ):
        raise ValidationError(
            "Only draft term results "
            "can be approved."
        )

    term_result.status = (
        TermResult.Status.APPROVED
    )

    term_result.approved_by = user
    term_result.approved_at = (
        timezone.now()
    )

    term_result.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "updated_at",
        ]
    )

    return term_result


@transaction.atomic
def generate_report_card(
    *,
    term_result,
    user,
):
    if term_result.status not in {
        TermResult.Status.APPROVED,
        TermResult.Status.PUBLISHED,
    }:
        raise ValidationError(
            "The term result must be approved "
            "before generating a report card."
        )

    existing = (
        ReportCard.objects
        .filter(
            term_result=term_result
        )
        .first()
    )

    if (
        existing
        and existing.status
        == ReportCard.Status.PUBLISHED
    ):
        raise ValidationError(
            "A published report card "
            "cannot be regenerated."
        )

    enrollment = (
        term_result.enrollment
    )

    student = enrollment.student

    plans = (
        OfferingAssessmentPlan.objects
        .filter(
            term=term_result.term,
            offering__class_section=(
                enrollment.class_section
            ),
            offering__academic_year=(
                enrollment.academic_year
            ),
        )
    )

    results = (
        SubjectResult.objects
        .filter(
            enrollment=enrollment,
            assessment_plan__in=plans,
            status__in=[
                SubjectResult.Status.APPROVED,
                SubjectResult.Status.PUBLISHED,
            ],
        )
        .select_related(
            "assessment_plan__offering__subject"
        )
        .order_by(
            "assessment_plan__offering__subject__name"
        )
    )

    subject_snapshot = []

    for result in results:

        subject_snapshot.append(
            {
                "subject": (
                    result.assessment_plan
                    .offering.subject.name
                ),
                "subject_code": (
                    result.assessment_plan
                    .offering.subject.code
                ),
                "score": str(
                    result.total_score
                ),
                "grade": result.grade,
                "is_pass": (
                    result.is_pass
                ),
                "remark": (
                    result.remark
                ),
            }
        )

    snapshot = {
        "student": {
            "id": str(
                student.id
            ),
            "admission_number": (
                student.admission_number
            ),
            "name": (
                student.full_name
            ),
        },

        "academic_year": (
            enrollment
            .academic_year
            .name
        ),

        "term": (
            term_result.term.name
        ),

        "class": str(
            enrollment.class_section
        ),

        "subjects": subject_snapshot,

        "summary": {
            "average_score": str(
                term_result.average_score
            ),
            "total_subjects": (
                term_result.total_subjects
            ),
            "failed_subjects": (
                term_result.failed_subjects
            ),
            "attendance_percentage": (
                str(
                    term_result
                    .attendance_percentage
                )
                if term_result
                .attendance_percentage
                is not None
                else None
            ),
        },

        "comments": {
            "class_teacher": (
                term_result
                .class_teacher_comment
            ),
            "headteacher": (
                term_result
                .headteacher_comment
            ),
        },
    }

    if existing:

        existing.snapshot = snapshot
        existing.generated_by = user

        existing.full_clean()
        existing.save()

        return existing

    clean_year = (
        enrollment.academic_year.name
        .replace("/", "")
        .replace(" ", "")
    )

    report_number = (
        f"RC-{clean_year}-"
        f"{uuid.uuid4().hex[:8].upper()}"
    )

    report = ReportCard(
        school=term_result.school,
        term_result=term_result,
        report_number=report_number,
        snapshot=snapshot,
        generated_by=user,
    )

    report.full_clean()
    report.save()

    return report


@transaction.atomic
def publish_report_card(
    *,
    report_card,
    user,
):
    if (
        report_card.status
        == ReportCard.Status.PUBLISHED
    ):
        raise ValidationError(
            "Report card is already published."
        )

    term_result = (
        report_card.term_result
    )

    if (
        term_result.status
        != TermResult.Status.APPROVED
    ):
        raise ValidationError(
            "Term result must be approved "
            "before publication."
        )

    now = timezone.now()

    enrollment = (
        term_result.enrollment
    )

    subject_results = (
        SubjectResult.objects
        .filter(
            enrollment=enrollment,
            assessment_plan__term=(
                term_result.term
            ),
            status=(
                SubjectResult.Status.APPROVED
            ),
        )
    )

    subject_results.update(
        status=(
            SubjectResult.Status.PUBLISHED
        ),
        published_by=user,
        published_at=now,
    )

    report_card.status = (
        ReportCard.Status.PUBLISHED
    )

    report_card.published_by = user
    report_card.published_at = now

    report_card.save(
        update_fields=[
            "status",
            "published_by",
            "published_at",
            "updated_at",
        ]
    )

    term_result.status = (
        TermResult.Status.PUBLISHED
    )

    term_result.published_by = user
    term_result.published_at = now

    term_result.save(
        update_fields=[
            "status",
            "published_by",
            "published_at",
            "updated_at",
        ]
    )

    return report_card