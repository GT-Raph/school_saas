from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import (
    ValidationError,
)
from django.db import transaction
from django.utils import timezone

from apps.academics.models import (
    Enrollment,
)
from apps.academics.services import (
    enroll_student,
)
from apps.assessments.models import (
    SubjectResult,
)
from apps.attendance.models import (
    AttendanceRecord,
    AttendanceSession,
)
from apps.audit.models import (
    AuditEvent,
)
from apps.reports.models import (
    TermResult,
)
from apps.students.models import (
    Student,
)

from .models import (
    PromotionDecision,
    PromotionEvaluation,
)


def calculate_annual_attendance(
    *,
    enrollment,
):
    records = (
        AttendanceRecord.objects
        .filter(
            enrollment=enrollment,
            session__academic_year=(
                enrollment.academic_year
            ),
            session__status__in=[
                AttendanceSession.Status.SUBMITTED,
                AttendanceSession.Status.LOCKED,
            ],
        )
        .exclude(
            status=(
                AttendanceRecord
                .Status.EXCUSED
            )
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

    return (
        Decimal(attended)
        / Decimal(total)
        * Decimal("100")
    ).quantize(
        Decimal("0.01")
    )


@transaction.atomic
def evaluate_student_promotion(
    *,
    policy,
    enrollment,
):
    """
    Evaluate one student against a versioned
    promotion policy.

    The engine recommends.
    Humans still approve.
    """

    if (
        enrollment.school_id
        != policy.school_id
    ):
        raise ValidationError(
            "Enrollment and policy belong "
            "to different schools."
        )

    if (
        enrollment.academic_year_id
        != policy.academic_year_id
    ):
        raise ValidationError(
            "Enrollment does not belong "
            "to the policy academic year."
        )

    if (
        enrollment.class_section
        .level_id
        != policy.class_level_id
    ):
        raise ValidationError(
            "Student is not enrolled in "
            "the class level covered "
            "by this policy."
        )

    reasons = []

    missing_data = []

    terms = (
        policy.academic_year
        .terms.all()
        .order_by("sequence")
    )

    published_term_results = (
        TermResult.objects
        .filter(
            enrollment=enrollment,
            term__academic_year=(
                policy.academic_year
            ),
            status=(
                TermResult.Status.PUBLISHED
            ),
        )
    )

    if policy.require_all_terms:

        expected_term_count = (
            terms.count()
        )

        actual_term_count = (
            published_term_results.count()
        )

        if (
            actual_term_count
            < expected_term_count
        ):
            missing_data.append(
                (
                    "Not all term results "
                    "have been published. "
                    f"Expected "
                    f"{expected_term_count}, "
                    f"found "
                    f"{actual_term_count}."
                )
            )

    term_scores = list(
        published_term_results
        .values_list(
            "average_score",
            flat=True,
        )
    )

    annual_average = None

    if term_scores:

        annual_average = (
            sum(
                term_scores,
                Decimal("0"),
            )
            / Decimal(
                len(term_scores)
            )
        ).quantize(
            Decimal("0.01")
        )

    else:

        missing_data.append(
            "No published term results exist."
        )

    attendance_percentage = (
        calculate_annual_attendance(
            enrollment=enrollment
        )
    )

    subject_results = (
        SubjectResult.objects
        .filter(
            enrollment=enrollment,
            assessment_plan__term__academic_year=(
                policy.academic_year
            ),
            status=(
                SubjectResult.Status.PUBLISHED
            ),
        )
        .select_related(
            "assessment_plan__offering__subject"
        )
    )

    subject_scores = defaultdict(
        list
    )

    subject_names = {}

    for result in subject_results:

        subject = (
            result.assessment_plan
            .offering.subject
        )

        subject_scores[
            subject.id
        ].append(
            result.total_score
        )

        subject_names[
            subject.id
        ] = subject.name

    subject_averages = {}

    for (
        subject_id,
        scores,
    ) in subject_scores.items():

        average = (
            sum(
                scores,
                Decimal("0"),
            )
            / Decimal(
                len(scores)
            )
        ).quantize(
            Decimal("0.01")
        )

        subject_averages[
            subject_id
        ] = average

    failed_subjects = sum(
        1
        for average
        in subject_averages.values()
        if average
        < policy.subject_pass_mark
    )

    if annual_average is not None:

        if (
            annual_average
            < policy.minimum_overall_average
        ):
            reasons.append(
                (
                    f"Overall average is "
                    f"{annual_average}%; "
                    f"required minimum is "
                    f"{policy.minimum_overall_average}%."
                )
            )

    if (
        failed_subjects
        > policy.maximum_failed_subjects
    ):
        reasons.append(
            (
                f"Failed subjects: "
                f"{failed_subjects}; "
                f"maximum allowed: "
                f"{policy.maximum_failed_subjects}."
            )
        )

    if (
        policy.minimum_attendance_percentage
        is not None
    ):

        if attendance_percentage is None:

            missing_data.append(
                "No valid attendance data "
                "is available."
            )

        elif (
            attendance_percentage
            < policy
            .minimum_attendance_percentage
        ):
            reasons.append(
                (
                    f"Attendance is "
                    f"{attendance_percentage}%; "
                    f"required minimum is "
                    f"{policy.minimum_attendance_percentage}%."
                )
            )

    for rule in (
        policy.subject_rules
        .select_related(
            "subject"
        )
        .all()
    ):

        subject_average = (
            subject_averages.get(
                rule.subject_id
            )
        )

        if subject_average is None:

            missing_data.append(
                (
                    f"No published annual "
                    f"result is available for "
                    f"{rule.subject.name}."
                )
            )

            continue

        if (
            subject_average
            < rule.minimum_average
        ):
            reasons.append(
                (
                    f"{rule.subject.name}: "
                    f"{subject_average}%; "
                    f"required minimum is "
                    f"{rule.minimum_average}%."
                )
            )

    if missing_data:

        recommendation = (
            PromotionEvaluation
            .Recommendation.REVIEW
        )

        reasons.extend(
            missing_data
        )

    elif not reasons:

        if (
            policy.class_level
            .is_graduating_level
        ):
            recommendation = (
                PromotionEvaluation
                .Recommendation.GRADUATE
            )

        else:

            recommendation = (
                PromotionEvaluation
                .Recommendation.PROMOTE
            )

    else:

        if (
            policy.demotion_threshold
            is not None
            and annual_average
            is not None
            and annual_average
            < policy.demotion_threshold
        ):
            recommendation = (
                PromotionEvaluation
                .Recommendation.DEMOTE
            )

        elif (
            policy.failure_action
            == policy
            .FailureAction.REVIEW
        ):
            recommendation = (
                PromotionEvaluation
                .Recommendation.REVIEW
            )

        else:

            recommendation = (
                PromotionEvaluation
                .Recommendation.REPEAT
            )

    metrics = {
        "annual_average": (
            str(annual_average)
            if annual_average
            is not None
            else None
        ),

        "attendance_percentage": (
            str(
                attendance_percentage
            )
            if attendance_percentage
            is not None
            else None
        ),

        "failed_subjects": (
            failed_subjects
        ),

        "terms_published": (
            published_term_results
            .count()
        ),

        "subject_averages": {
            str(subject_id): {
                "subject": (
                    subject_names[
                        subject_id
                    ]
                ),
                "average": str(
                    average
                ),
            }
            for (
                subject_id,
                average,
            )
            in subject_averages.items()
        },
    }

    evaluation, _ = (
        PromotionEvaluation
        .objects.update_or_create(
            policy=policy,
            enrollment=enrollment,
            defaults={
                "school": (
                    enrollment.school
                ),
                "annual_average": (
                    annual_average
                ),
                "attendance_percentage": (
                    attendance_percentage
                ),
                "failed_subjects": (
                    failed_subjects
                ),
                "recommendation": (
                    recommendation
                ),
                "reasons": reasons,
                "metrics": metrics,
            },
        )
    )

    evaluation.full_clean()
    evaluation.save()

    return evaluation


@transaction.atomic
def approve_promotion_decision(
    *,
    evaluation,
    final_decision,
    approved_by,
    target_class_section=None,
    reason="",
):
    """
    Human approval step.

    System recommendation may be overridden,
    but the override is permanently recorded.
    """

    enrollment = (
        evaluation.enrollment
    )

    current_level = (
        enrollment.class_section.level
    )

    if final_decision in {
        PromotionDecision
        .Decision.PROMOTE,

        PromotionDecision
        .Decision.REPEAT,

        PromotionDecision
        .Decision.DEMOTE,
    }:

        if target_class_section is None:
            raise ValidationError(
                "A target class section "
                "is required."
            )

        if (
            target_class_section.school_id
            != evaluation.school_id
        ):
            raise ValidationError(
                "Target class belongs "
                "to another school."
            )

    if (
        final_decision
        == PromotionDecision
        .Decision.PROMOTE
    ):

        if (
            current_level.next_level_id
            is None
        ):
            raise ValidationError(
                "Current level has no "
                "configured next level."
            )

        if (
            target_class_section.level_id
            != current_level.next_level_id
        ):
            raise ValidationError(
                "Promotion target must be "
                "the configured next level."
            )

    elif (
        final_decision
        == PromotionDecision
        .Decision.REPEAT
    ):

        if (
            target_class_section.level_id
            != current_level.id
        ):
            raise ValidationError(
                "A repeating student must "
                "remain at the same level."
            )

    elif (
        final_decision
        == PromotionDecision
        .Decision.DEMOTE
    ):

        if (
            target_class_section.level.order
            >= current_level.order
        ):
            raise ValidationError(
                "A demotion target must be "
                "below the current level."
            )

    elif (
        final_decision
        == PromotionDecision
        .Decision.GRADUATE
    ):

        if not (
            current_level
            .is_graduating_level
        ):
            raise ValidationError(
                "Only students in a "
                "graduating level can "
                "be marked as graduated."
            )

    decision, _ = (
        PromotionDecision
        .objects.update_or_create(
            evaluation=evaluation,
            defaults={
                "school": (
                    evaluation.school
                ),
                "final_decision": (
                    final_decision
                ),
                "target_class_section": (
                    target_class_section
                ),
                "reason": reason,
                "approved_by": (
                    approved_by
                ),
                "approved_at": (
                    timezone.now()
                ),
            },
        )
    )

    decision.full_clean()
    decision.save()

    AuditEvent.objects.create(
        school=evaluation.school,
        actor=approved_by,
        action=(
            "promotion_decision_approved"
        ),
        object_type=(
            "PromotionDecision"
        ),
        object_id=str(
            decision.id
        ),
        changes={
            "system_recommendation": (
                evaluation.recommendation
            ),
            "final_decision": (
                final_decision
            ),
            "reason": reason,
        },
    )

    return decision


@transaction.atomic
def execute_promotion_decision(
    *,
    decision,
    next_academic_year=None,
    enrolled_on=None,
    executed_by=None,
):
    """
    Execute an approved promotion decision.

    All changes happen inside one transaction.
    """

    if decision.executed_at:
        raise ValidationError(
            "This decision has already "
            "been executed."
        )

    enrollment = (
        decision.evaluation.enrollment
    )

    student = enrollment.student

    final_decision = (
        decision.final_decision
    )

    if (
        final_decision
        == PromotionDecision
        .Decision.REVIEW
    ):
        raise ValidationError(
            "A manual review decision "
            "cannot be executed."
        )

    if (
        final_decision
        == PromotionDecision
        .Decision.GRADUATE
    ):

        enrollment.status = (
            Enrollment.Status.COMPLETED
        )

        enrollment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        student.status = (
            Student.Status.GRADUATED
        )

        student.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        decision.executed_at = (
            timezone.now()
        )

        decision.save(
            update_fields=[
                "executed_at",
                "updated_at",
            ]
        )

        AuditEvent.objects.create(
            school=decision.school,
            actor=executed_by,
            action=(
                "student_graduated"
            ),
            object_type="Student",
            object_id=str(
                student.id
            ),
            changes={
                "academic_year": (
                    enrollment
                    .academic_year.name
                ),
                "decision": (
                    final_decision
                ),
            },
        )

        return decision

    if next_academic_year is None:
        raise ValidationError(
            "Next academic year is required."
        )

    if (
        next_academic_year.school_id
        != decision.school_id
    ):
        raise ValidationError(
            "Next academic year belongs "
            "to another school."
        )

    if (
        next_academic_year.starts_on
        <= enrollment
        .academic_year.starts_on
    ):
        raise ValidationError(
            "The destination academic year "
            "must be after the current year."
        )

    target = (
        decision.target_class_section
    )

    if target is None:
        raise ValidationError(
            "Target class section "
            "is required."
        )

    enrollment.status = (
        Enrollment.Status.COMPLETED
    )

    enrollment.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    new_enrollment = enroll_student(
        school=decision.school,
        student=student,
        academic_year=(
            next_academic_year
        ),
        class_section=target,
        enrolled_on=enrolled_on,
        notes=(
            f"Created from promotion "
            f"decision {decision.id}"
        ),
    )

    student.status = (
        Student.Status.ACTIVE
    )

    student.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    decision.resulting_enrollment = (
        new_enrollment
    )

    decision.executed_at = (
        timezone.now()
    )

    decision.save(
        update_fields=[
            "resulting_enrollment",
            "executed_at",
            "updated_at",
        ]
    )

    AuditEvent.objects.create(
        school=decision.school,
        actor=executed_by,
        action=(
            "promotion_decision_executed"
        ),
        object_type=(
            "PromotionDecision"
        ),
        object_id=str(
            decision.id
        ),
        changes={
            "student": (
                student.full_name
            ),
            "from": str(
                enrollment.class_section
            ),
            "to": str(
                new_enrollment
                .class_section
            ),
            "decision": (
                final_decision
            ),
            "academic_year": (
                next_academic_year.name
            ),
        },
    )

    return new_enrollment