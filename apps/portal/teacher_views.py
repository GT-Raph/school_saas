from django.contrib import messages
from django.core.exceptions import (
    ValidationError,
)

from .pagination import paginate

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
    Enrollment,
    TeacherAssignment,
    Term,
)
from apps.assessments.models import (
    Assessment,
    OfferingAssessmentPlan,
    Score,
    SubjectResult,
)
from apps.assessments.services import (
    calculate_subject_result,
    save_student_score,
    submit_result,
)
from apps.attendance.models import (
    AttendanceRecord,
    AttendanceSession,
)
from apps.attendance.services import (
    create_attendance_session,
    save_attendance_records,
)
from apps.subscriptions.decorators import (
    subscription_write_required,
)

from .teacher_forms import (
    AttendanceFormSet,
    ScoreFormSet,
)
from .teacher_services import (
    get_offering_enrollments,
    get_teacher_offering_or_403,
    get_teacher_profile,
)


@school_permission_required(
    "academics.view_teacherassignment"
)
def teacher_classes(
    request,
):
    teacher = get_teacher_profile(
        user=request.user,
        school=request.school,
    )

    assignments = (
        TeacherAssignment.objects
        .for_school(
            request.school
        )
        .filter(
            teacher=teacher,
            is_active=True,
        )
        .select_related(
            "offering__subject",
            "offering__class_section__level",
            "offering__academic_year",
        )
        .order_by(
            "-offering__academic_year__starts_on",
            "offering__class_section__level__order",
            "offering__subject__name",
        )
    )

    page_obj, pagination_query = paginate(
        request,
        assignments,
    )

    assignments = page_obj.object_list

    return render(
        request,
        "portal/teacher/classes.html",
        {
            "teacher": teacher,
            "assignments": assignments,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
        },
    )


@school_permission_required(
    "academics.view_teacherassignment"
)
def teacher_class_detail(
    request,
    offering_id,
):
    teacher, offering = (
        get_teacher_offering_or_403(
            user=request.user,
            school=request.school,
            offering_id=offering_id,
        )
    )

    enrollments = (
        get_offering_enrollments(
            offering=offering
        )
    )

    student_count = enrollments.count()

    page_obj, pagination_query = paginate(
        request,
        enrollments,
    )

    enrollments = page_obj.object_list

    terms = (
        Term.objects
        .for_school(
            request.school
        )
        .filter(
            academic_year=(
                offering.academic_year
            )
        )
        .order_by(
            "sequence"
        )
    )

    plans = (
        OfferingAssessmentPlan.objects
        .for_school(
            request.school
        )
        .filter(
            offering=offering
        )
        .select_related(
            "term",
            "scheme",
            "grade_scale",
        )
        .order_by(
            "term__sequence"
        )
    )

    return render(
        request,
        (
            "portal/teacher/"
            "class_detail.html"
        ),
        {
            "teacher": teacher,
            "offering": offering,
            "enrollments": enrollments,
            "terms": terms,
            "plans": plans,
            "student_count": student_count,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
        },
    )


@subscription_write_required
@school_permission_required(
    "attendance.add_attendancesession"
)
def teacher_take_attendance(
    request,
    offering_id,
    term_id,
):
    teacher, offering = (
        get_teacher_offering_or_403(
            user=request.user,
            school=request.school,
            offering_id=offering_id,
        )
    )

    term = get_object_or_404(
        Term.objects.for_school(
            request.school
        ),
        id=term_id,
        academic_year=(
            offering.academic_year
        ),
    )

    date_value = (
        request.GET.get("date")
        or request.POST.get(
            "attendance_date"
        )
    )

    from datetime import date

    if date_value:
        try:
            attendance_date = (
                date.fromisoformat(
                    date_value
                )
            )
        except ValueError:
            attendance_date = (
                date.today()
            )
    else:
        attendance_date = (
            date.today()
        )

    enrollments = list(
        get_offering_enrollments(
            offering=offering
        )
    )

    existing_session = (
        AttendanceSession.objects
        .for_school(
            request.school
        )
        .filter(
            class_section=(
                offering.class_section
            ),
            attendance_date=(
                attendance_date
            ),
        )
        .first()
    )

    existing_records = {}

    if existing_session:
        existing_records = {
            record.enrollment_id:
                record
            for record
            in existing_session.records.all()
        }

    initial = []

    for enrollment in enrollments:
        existing = existing_records.get(
            enrollment.id
        )

        initial.append(
            {
                "enrollment_id":
                    enrollment.id,

                "student_name":
                    enrollment
                    .student.full_name,

                "admission_number":
                    enrollment
                    .student
                    .admission_number,

                "status": (
                    existing.status
                    if existing
                    else AttendanceRecord
                    .Status.PRESENT
                ),

                "remarks": (
                    existing.remarks
                    if existing
                    else ""
                ),
            }
        )

    if request.method == "POST":
        formset = AttendanceFormSet(
            request.POST,
            initial=initial,
        )

        if formset.is_valid():

            if existing_session:

                if (
                    existing_session.status
                    == AttendanceSession
                    .Status.LOCKED
                ):
                    raise ValidationError(
                        (
                            "This attendance "
                            "session is locked."
                        )
                    )

                session = (
                    existing_session
                )

            else:

                session = (
                    create_attendance_session(
                        school=(
                            request.school
                        ),

                        academic_year=(
                            offering
                            .academic_year
                        ),

                        term=term,

                        class_section=(
                            offering
                            .class_section
                        ),

                        attendance_date=(
                            attendance_date
                        ),

                        taken_by=teacher,
                    )
                )

            enrollment_map = {
                enrollment.id:
                    enrollment
                for enrollment
                in enrollments
            }

            attendance_data = []

            for form in formset:

                cleaned = (
                    form.cleaned_data
                )

                enrollment_id = (
                    cleaned[
                        "enrollment_id"
                    ]
                )

                enrollment = (
                    enrollment_map.get(
                        enrollment_id
                    )
                )

                if not enrollment:
                    raise ValidationError(
                        (
                            "Invalid student "
                            "submitted."
                        )
                    )

                attendance_data.append(
                    {
                        "enrollment":
                            enrollment,

                        "status":
                            cleaned[
                                "status"
                            ],

                        "remarks":
                            cleaned.get(
                                "remarks",
                                "",
                            ),
                    }
                )

            save_attendance_records(
                session=session,
                attendance_data=(
                    attendance_data
                ),
            )

            messages.success(
                request,
                (
                    "Attendance saved "
                    "successfully."
                ),
            )

            return redirect(
                "portal:"
                "teacher-class-detail",
                offering_id=(
                    offering.id
                ),
            )

    else:
        formset = AttendanceFormSet(
            initial=initial
        )

    return render(
        request,
        (
            "portal/teacher/"
            "attendance.html"
        ),
        {
            "offering": offering,
            "term": term,
            "attendance_date":
                attendance_date,
            "formset": formset,
            "session":
                existing_session,
        },
    )


@school_permission_required(
    "assessments.view_assessment"
)
def teacher_assessments(
    request,
    offering_id,
    term_id,
):
    _, offering = (
        get_teacher_offering_or_403(
            user=request.user,
            school=request.school,
            offering_id=offering_id,
        )
    )

    plan = get_object_or_404(
        OfferingAssessmentPlan.objects
        .for_school(
            request.school
        ),
        offering=offering,
        term_id=term_id,
    )

    assessments = (
        plan.assessments
        .select_related(
            "category"
        )
        .order_by(
            "category__sequence",
            "assessment_date",
            "name",
        )
    )

    return render(
        request,
        (
            "portal/teacher/"
            "assessments.html"
        ),
        {
            "offering": offering,
            "plan": plan,
            "assessments":
                assessments,
        },
    )


@subscription_write_required
@school_permission_required(
    "assessments.change_score"
)
def teacher_enter_scores(
    request,
    assessment_id,
):
    assessment = get_object_or_404(
        Assessment.objects
        .for_school(
            request.school
        )
        .select_related(
            "assessment_plan"
            "__offering",
            "assessment_plan"
            "__offering__subject",
            "assessment_plan"
            "__offering__class_section",
            "category",
        ),
        id=assessment_id,
    )

    offering = (
        assessment
        .assessment_plan
        .offering
    )

    get_teacher_offering_or_403(
        user=request.user,
        school=request.school,
        offering_id=(
            offering.id
        ),
    )

    if (
        assessment.status
        == Assessment.Status.LOCKED
    ):
        raise ValidationError(
            (
                "This assessment "
                "is locked."
            )
        )

    enrollments = list(
        get_offering_enrollments(
            offering=offering
        )
    )

    existing_scores = {
        score.enrollment_id:
            score
        for score
        in Score.objects
        .for_school(
            request.school
        )
        .filter(
            assessment=assessment
        )
    }

    initial = []

    for enrollment in enrollments:

        score = existing_scores.get(
            enrollment.id
        )

        initial.append(
            {
                "enrollment_id":
                    enrollment.id,

                "student_name":
                    enrollment
                    .student.full_name,

                "admission_number":
                    enrollment
                    .student
                    .admission_number,

                "raw_score": (
                    score.raw_score
                    if score
                    else None
                ),

                "is_absent": (
                    score.is_absent
                    if score
                    else False
                ),

                "comment": (
                    score.comment
                    if score
                    else ""
                ),
            }
        )

    formset_kwargs = {
        "initial": initial,
        "form_kwargs": {
            "max_score":
                assessment.max_score,
        },
    }

    if request.method == "POST":
        formset_kwargs[
            "data"
        ] = request.POST

    formset = ScoreFormSet(
        **formset_kwargs
    )

    if (
        request.method == "POST"
        and formset.is_valid()
    ):

        enrollment_map = {
            enrollment.id:
                enrollment
            for enrollment
            in enrollments
        }

        with transaction.atomic():

            for form in formset:

                cleaned = (
                    form.cleaned_data
                )

                enrollment = (
                    enrollment_map.get(
                        cleaned[
                            "enrollment_id"
                        ]
                    )
                )

                if not enrollment:
                    raise ValidationError(
                        (
                            "Invalid student "
                            "submitted."
                        )
                    )

                save_student_score(
                    school=request.school,

                    assessment=(
                        assessment
                    ),

                    enrollment=(
                        enrollment
                    ),

                    raw_score=(
                        cleaned.get(
                            "raw_score"
                        )
                    ),

                    is_absent=(
                        cleaned.get(
                            "is_absent",
                            False,
                        )
                    ),

                    comment=(
                        cleaned.get(
                            "comment",
                            "",
                        )
                    ),

                    entered_by=(
                        request.user
                    ),
                )

        messages.success(
            request,
            "Scores saved successfully.",
        )

        return redirect(
            "portal:"
            "teacher-assessments",

            offering_id=(
                offering.id
            ),

            term_id=(
                assessment
                .assessment_plan
                .term_id
            ),
        )

    return render(
        request,
        (
            "portal/teacher/"
            "score_entry.html"
        ),
        {
            "assessment":
                assessment,
            "offering":
                offering,
            "formset":
                formset,
        },
    )


@subscription_write_required
@school_permission_required(
    "assessments.submit_subject_result"
)
def teacher_calculate_submit_results(
    request,
    plan_id,
):
    if request.method != "POST":
        raise ValidationError(
            "POST request required."
        )

    plan = get_object_or_404(
        OfferingAssessmentPlan.objects
        .for_school(
            request.school
        )
        .select_related(
            "offering",
            "offering__subject",
            "offering__class_section",
            "term",
        ),
        id=plan_id,
    )

    offering = plan.offering

    get_teacher_offering_or_403(
        user=request.user,
        school=request.school,
        offering_id=offering.id,
    )

    enrollments = (
        get_offering_enrollments(
            offering=offering
        )
    )

    errors = []

    completed = 0

    with transaction.atomic():

        for enrollment in enrollments:

            try:
                result = (
                    calculate_subject_result(
                        assessment_plan=plan,
                        enrollment=(
                            enrollment
                        ),
                    )
                )

                if (
                    result.status
                    == SubjectResult
                    .Status.DRAFT
                ):
                    submit_result(
                        result=result,
                        user=request.user,
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
                f"{completed} results "
                "calculated and submitted."
            ),
        )

    return redirect(
        "portal:"
        "teacher-assessments",

        offering_id=(
            offering.id
        ),

        term_id=(
            plan.term_id
        ),
    )