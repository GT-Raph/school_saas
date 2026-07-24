from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from apps.accounts.decorators import (
    school_permission_required,
)
from apps.academics.models import (
    ClassSection,
    Enrollment,
    Term,
)
from apps.assessments.models import (
    OfferingAssessmentPlan,
    SubjectResult,
)
from apps.assessments.services import (
    approve_result,
)
from apps.reports.models import (
    ReportCard,
    TermResult,
)
from apps.reports.services import (
    approve_term_result,
    calculate_term_result,
    generate_report_card,
    publish_report_card,
)
from apps.subscriptions.decorators import (
    subscription_write_required,
)


@school_permission_required(
    "assessments.view_subjectresult"
)
def academic_results_queue(
    request,
):
    results = (
        SubjectResult.objects
        .for_school(
            request.school
        )
        .filter(
            status=(
                SubjectResult
                .Status.SUBMITTED
            )
        )
        .select_related(
            "enrollment__student",
            "assessment_plan__term",
            "assessment_plan__offering__subject",
            "assessment_plan__offering__class_section",
        )
        .order_by(
            "assessment_plan__term__sequence",
            "assessment_plan__offering__class_section",
            "assessment_plan__offering__subject",
            "enrollment__student__last_name",
        )
    )

    return render(
        request,
        (
            "portal/academic/"
            "results_queue.html"
        ),
        {
            "results": results,
        },
    )


@subscription_write_required
@school_permission_required(
    "assessments.approve_subject_result"
)
def academic_approve_result(
    request,
    result_id,
):
    if request.method != "POST":

        raise ValidationError(
            "POST request required."
        )

    result = get_object_or_404(
        SubjectResult.objects
        .for_school(
            request.school
        ),
        id=result_id,
    )

    try:

        approve_result(
            result=result,
            user=request.user,
        )

    except ValidationError as exc:

        messages.error(
            request,
            " ".join(
                exc.messages
            ),
        )

    else:

        messages.success(
            request,
            "Result approved.",
        )

    return redirect(
        "portal:academic-results-queue"
    )


@school_permission_required(
    "reports.view_termresult"
)
def academic_term_results_home(
    request,
):
    terms = (
        Term.objects
        .for_school(
            request.school
        )
        .select_related(
            "academic_year"
        )
        .order_by(
            "-academic_year__starts_on",
            "sequence",
        )
    )

    sections = (
        ClassSection.objects
        .for_school(
            request.school
        )
        .filter(
            is_active=True
        )
        .select_related(
            "level"
        )
        .order_by(
            "level__order",
            "name",
        )
    )

    return render(
        request,
        (
            "portal/academic/"
            "term_results_home.html"
        ),
        {
            "terms": terms,
            "sections": sections,
        },
    )


@school_permission_required(
    "reports.view_termresult"
)
def academic_term_results(
    request,
    term_id,
    section_id,
):
    term = get_object_or_404(
        Term.objects.for_school(
            request.school
        ),
        id=term_id,
    )

    section = get_object_or_404(
        ClassSection.objects
        .for_school(
            request.school
        ),
        id=section_id,
    )

    enrollments = (
        Enrollment.objects
        .for_school(
            request.school
        )
        .filter(
            academic_year=(
                term.academic_year
            ),
            class_section=section,
        )
        .select_related(
            "student"
        )
        .order_by(
            "student__last_name",
            "student__first_name",
        )
    )

    rows = []

    for enrollment in enrollments:

        term_result = (
            TermResult.objects
            .for_school(
                request.school
            )
            .filter(
                enrollment=enrollment,
                term=term,
            )
            .first()
        )

        report_card = None

        if term_result:

            report_card = (
                ReportCard.objects
                .for_school(
                    request.school
                )
                .filter(
                    term_result=term_result
                )
                .first()
            )

        rows.append(
            {
                "enrollment":
                    enrollment,

                "term_result":
                    term_result,

                "report_card":
                    report_card,
            }
        )

    return render(
        request,
        (
            "portal/academic/"
            "term_results.html"
        ),
        {
            "term": term,
            "section": section,
            "rows": rows,
        },
    )


@subscription_write_required
@school_permission_required(
    "reports.change_termresult"
)
def academic_calculate_term_results(
    request,
    term_id,
    section_id,
):
    if request.method != "POST":

        raise ValidationError(
            "POST request required."
        )

    term = get_object_or_404(
        Term.objects.for_school(
            request.school
        ),
        id=term_id,
    )

    section = get_object_or_404(
        ClassSection.objects
        .for_school(
            request.school
        ),
        id=section_id,
    )

    enrollments = (
        Enrollment.objects
        .for_school(
            request.school
        )
        .filter(
            academic_year=(
                term.academic_year
            ),
            class_section=section,
        )
        .select_related(
            "student"
        )
    )

    errors = []
    completed = 0

    with transaction.atomic():

        for enrollment in enrollments:

            try:

                calculate_term_result(
                    enrollment=enrollment,
                    term=term,
                )

                completed += 1

            except ValidationError as exc:

                errors.append(
                    (
                        f"{enrollment.student.full_name}: "
                        + " ".join(
                            exc.messages
                        )
                    )
                )

        if errors:

            transaction.set_rollback(
                True
            )

    if errors:

        for error in errors[:20]:

            messages.error(
                request,
                error,
            )

    else:

        messages.success(
            request,
            (
                f"{completed} term results "
                "calculated."
            ),
        )

    return redirect(
        "portal:academic-term-results",

        term_id=term.id,

        section_id=section.id,
    )


@subscription_write_required
@school_permission_required(
    "reports.change_termresult"
)
def academic_approve_term_result(
    request,
    term_result_id,
):
    if request.method != "POST":

        raise ValidationError(
            "POST request required."
        )

    result = get_object_or_404(
        TermResult.objects
        .for_school(
            request.school
        ),
        id=term_result_id,
    )

    try:

        approve_term_result(
            term_result=result,
            user=request.user,
        )

    except ValidationError as exc:

        messages.error(
            request,
            " ".join(
                exc.messages
            ),
        )

    else:

        messages.success(
            request,
            "Term result approved.",
        )

    return redirect(
        "portal:academic-term-results",

        term_id=result.term_id,

        section_id=(
            result.enrollment
            .class_section_id
        ),
    )


@subscription_write_required
@school_permission_required(
    "reports.change_reportcard"
)
def academic_generate_report_card(
    request,
    term_result_id,
):
    if request.method != "POST":

        raise ValidationError(
            "POST request required."
        )

    result = get_object_or_404(
        TermResult.objects
        .for_school(
            request.school
        ),
        id=term_result_id,
    )

    try:

        generate_report_card(
            term_result=result,
            user=request.user,
        )

    except ValidationError as exc:

        messages.error(
            request,
            " ".join(
                exc.messages
            ),
        )

    else:

        messages.success(
            request,
            "Report card generated.",
        )

    return redirect(
        "portal:academic-term-results",

        term_id=result.term_id,

        section_id=(
            result.enrollment
            .class_section_id
        ),
    )


@subscription_write_required
@school_permission_required(
    "assessments.publish_subject_result"
)
def academic_publish_report_card(
    request,
    report_card_id,
):
    if request.method != "POST":

        raise ValidationError(
            "POST request required."
        )

    report = get_object_or_404(
        ReportCard.objects
        .for_school(
            request.school
        ),
        id=report_card_id,
    )

    result = report.term_result

    try:

        publish_report_card(
            report_card=report,
            user=request.user,
        )

    except ValidationError as exc:

        messages.error(
            request,
            " ".join(
                exc.messages
            ),
        )

    else:

        messages.success(
            request,
            "Report card published.",
        )

    return redirect(
        "portal:academic-term-results",

        term_id=result.term_id,

        section_id=(
            result.enrollment
            .class_section_id
        ),
    )