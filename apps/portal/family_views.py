from django.core.exceptions import PermissionDenied
from django.shortcuts import (
    get_object_or_404,
    render,
)

from apps.accounts.decorators import (
    tenant_login_required,
)
from apps.academics.models import Enrollment
from apps.finance.services import (
    get_enrollment_balance,
    get_student_statement,
)
from apps.reports.models import (
    ReportCard,
    TermResult,
)
from apps.students.models import Student

from .family_services import (
    get_parent_student_or_403,
    get_student_or_403,
)


def build_student_portal_context(
    *,
    school,
    student,
):
    """
    Build the shared portal context used by
    both student and parent views.
    """

    enrollments = (
        student.enrollments
        .filter(
            school=school,
        )
        .select_related(
            "academic_year",
            "class_section__level",
        )
        .order_by(
            "-academic_year__starts_on",
        )
    )

    current_enrollment = (
        enrollments
        .filter(
            status=Enrollment.Status.ACTIVE,
        )
        .first()
    )

    term_results = (
        TermResult.objects
        .for_school(
            school
        )
        .filter(
            enrollment__student=student,
            status=(
                TermResult.Status.PUBLISHED
            ),
        )
        .select_related(
            "term",
            "term__academic_year",
            "enrollment",
            "enrollment__class_section",
            "enrollment__class_section__level",
        )
        .order_by(
            "-term__academic_year__starts_on",
            "term__sequence",
        )
    )

    report_cards = (
        ReportCard.objects
        .for_school(
            school
        )
        .filter(
            term_result__enrollment__student=(
                student
            ),
            status=(
                ReportCard.Status.PUBLISHED
            ),
        )
        .select_related(
            "term_result",
            "term_result__term",
            "term_result__term__academic_year",
            "term_result__enrollment",
        )
        .order_by(
            (
                "-term_result__term__"
                "academic_year__starts_on"
            ),
            "term_result__term__sequence",
        )
    )

    balance = None
    statement = []

    if current_enrollment:
        balance = get_enrollment_balance(
            current_enrollment
        )

        statement = get_student_statement(
            enrollment=current_enrollment,
        )

    return {
        "student": student,
        "enrollments": enrollments,
        "current_enrollment": (
            current_enrollment
        ),
        "term_results": term_results,
        "report_cards": report_cards,
        "balance": balance,
        "statement": statement,
    }


@tenant_login_required
def parent_child_detail(
    request,
    student_id,
):
    """
    Allow a parent/guardian to view only
    a student linked to their account.
    """

    _, student = (
        get_parent_student_or_403(
            user=request.user,
            school=request.school,
            student_id=student_id,
        )
    )

    context = build_student_portal_context(
        school=request.school,
        student=student,
    )

    context["portal_mode"] = "parent"

    return render(
        request,
        (
            "portal/family/"
            "student_overview.html"
        ),
        context,
    )


@tenant_login_required
def student_self_service(
    request,
):
    """
    Allow a student to access only their
    own student portal profile.
    """

    student = get_student_or_403(
        user=request.user,
        school=request.school,
    )

    context = build_student_portal_context(
        school=request.school,
        student=student,
    )

    context["portal_mode"] = "student"

    return render(
        request,
        (
            "portal/family/"
            "student_overview.html"
        ),
        context,
    )


@tenant_login_required
def family_report_card(
    request,
    report_card_id,
):
    """
    Allow access to a published report card
    only when the logged-in user is:

    1. The student who owns the report, or
    2. A parent/guardian linked to that student.
    """

    report = get_object_or_404(
        ReportCard.objects
        .for_school(
            request.school
        )
        .select_related(
            "term_result",
            "term_result__enrollment",
            (
                "term_result__enrollment__"
                "student"
            ),
            "term_result__term",
            "term_result__term__academic_year",
        ),
        id=report_card_id,
        status=(
            ReportCard.Status.PUBLISHED
        ),
    )

    report_student = (
        report.term_result
        .enrollment
        .student
    )

    # Check whether the logged-in user
    # has a student profile in this school.
    student_profile = (
        Student.objects
        .for_school(
            request.school
        )
        .filter(
            user=request.user,
        )
        .first()
    )

    if student_profile:
        # Student users may only view
        # their own report cards.
        if (
            report_student.id
            != student_profile.id
        ):
            raise PermissionDenied(
                "You cannot access this "
                "student's report card."
            )

    else:
        # Non-student users must have a valid
        # parent/guardian relationship with
        # the student who owns the report.
        get_parent_student_or_403(
            user=request.user,
            school=request.school,
            student_id=report_student.id,
        )

    return render(
        request,
        (
            "portal/family/"
            "report_card.html"
        ),
        {
            "report": report,
            "student": report_student,
        },
    )