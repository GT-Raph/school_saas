from decimal import Decimal

from django.core.exceptions import (
    PermissionDenied,
)
from django.db.models import (
    Count,
    Sum
)
from django.shortcuts import (
    redirect,
    render,
)

from apps.accounts.decorators import (
    tenant_login_required,
)
from apps.academics.models import (
    Enrollment,
    TeacherAssignment,
)
from apps.finance.models import (
    LedgerEntry,
    Payment,
    StudentInvoice,
)
from apps.guardians.models import (
    Guardian,
)

from apps.staff.models import Staff
from apps.students.models import Student

from apps.schools.permissions import (
    has_role,
)
from apps.students.models import Student

from .services import (
    determine_dashboard,
)


@tenant_login_required
def portal_home(
    request,
):
    dashboard = determine_dashboard(
        user=request.user,
        school=request.school,
    )

    routes = {
        "school_admin":
            "portal:school-admin",

        "academic":
            "portal:academic",

        "finance":
            "portal:finance",

        "teacher":
            "portal:teacher",

        "parent":
            "portal:parent",

        "student":
            "portal:student",
    }

    route = routes.get(
        dashboard
    )

    if route:
        return redirect(
            route
        )

    return render(
        request,
        "portal/basic_dashboard.html",
    )


@tenant_login_required
def school_admin_dashboard(
    request,
):
    if (
        not request.user.is_superuser
        and not request.user.is_platform_admin
        and not has_role(
            user=request.user,
            school=request.school,
            role_code="school-admin",
        )
    ):
        raise PermissionDenied

    school = request.school

    active_students = (
        Student.objects
        .for_school(school)
        .filter(
            status=Student.Status.ACTIVE
        )
    )

    student_count = (
        active_students.count()
    )

    teacher_count = (
        Staff.objects
        .for_school(school)
        .filter(
            is_teacher=True,
            employment_status=(
                Staff
                .EmploymentStatus.ACTIVE
            ),
        )
        .count()
    )

    guardian_count = (
        Guardian.objects
        .for_school(school)
        .filter(
            is_active=True
        )
        .count()
    )

    ledger_totals = (
        LedgerEntry.objects
        .for_school(school)
        .aggregate(
            debit=Sum("debit"),
            credit=Sum("credit"),
        )
    )

    total_debit = (
        ledger_totals["debit"]
        or Decimal("0")
    )

    total_credit = (
        ledger_totals["credit"]
        or Decimal("0")
    )

    outstanding = (
        total_debit
        - total_credit
    )

    class_rows = list(
        Enrollment.objects
        .for_school(school)
        .filter(
            status=Enrollment.Status.ACTIVE
        )
        .values(
            "class_section__level__name",
            "class_section__name",
        )
        .annotate(
            total=Count(
                "student_id",
                distinct=True,
            )
        )
        .order_by(
            "class_section__level__order",
            "class_section__name",
        )
    )

    largest_class = max(
        (
            row["total"]
            for row
            in class_rows
        ),
        default=1,
    )

    class_chart = [
        {
            "label": (
                f"{row['class_section__level__name']} "
                f"{row['class_section__name']}"
            ),

            "total": row["total"],

            "percent": round(
                (
                    row["total"]
                    / largest_class
                )
                * 100,
                2,
            ),
        }
        for row
        in class_rows
    ]

    gender_rows = (
        active_students
        .values(
            "gender"
        )
        .annotate(
            total=Count("id")
        )
    )

    gender_counts = {
        row["gender"]:
            row["total"]
        for row
        in gender_rows
    }

    male_count = gender_counts.get(
        Student.Gender.MALE,
        0,
    )

    female_count = gender_counts.get(
        Student.Gender.FEMALE,
        0,
    )

    other_count = max(
        student_count
        - male_count
        - female_count,
        0,
    )

    gender_total = max(
        student_count,
        1,
    )

    gender_summary = {
        "male": male_count,

        "female": female_count,

        "other": other_count,

        "male_percent": round(
            male_count
            / gender_total
            * 100,
            2,
        ),

        "female_percent": round(
            female_count
            / gender_total
            * 100,
            2,
        ),

        "other_percent": round(
            other_count
            / gender_total
            * 100,
            2,
        ),
    }

    recent_students = (
        Student.objects
        .for_school(school)
        .order_by(
            "-created_at"
        )[:5]
    )

    recent_payments = (
        Payment.objects
        .for_school(school)
        .filter(
            status=(
                Payment.Status.CONFIRMED
            )
        )
        .select_related(
            "enrollment__student"
        )
        .order_by(
            "-paid_at"
        )[:5]
    )

    context = {
        "student_count":
            student_count,

        "teacher_count":
            teacher_count,

        "guardian_count":
            guardian_count,

        "outstanding":
            outstanding,

        "total_debit":
            total_debit,

        "total_credit":
            total_credit,

        "class_chart":
            class_chart,

        "gender_summary":
            gender_summary,

        "recent_students":
            recent_students,

        "recent_payments":
            recent_payments,
    }

    return render(
        request,
        (
            "portal/"
            "school_admin_dashboard.html"
        ),
        context,
    )


@tenant_login_required
def teacher_dashboard(
    request,
):
    school = request.school

    staff = (
        request.user
        .staff_profiles
        .filter(
            school=school,
            employment_status="active",
            is_teacher=True,
        )
        .first()
    )

    if not staff:
        raise PermissionDenied(
            "No active teacher profile "
            "is linked to this account."
        )

    assignments = (
        TeacherAssignment.objects
        .for_school(school)
        .filter(
            teacher=staff,
            is_active=True,
        )
        .select_related(
            "offering__subject",
            "offering__class_section__level",
            "offering__academic_year",
        )
    )

    return render(
        request,
        "portal/teacher_dashboard.html",
        {
            "staff": staff,
            "assignments": assignments,
        },
    )


@tenant_login_required
def parent_dashboard(
    request,
):
    school = request.school

    guardian = (
        Guardian.objects
        .for_school(school)
        .filter(
            user=request.user,
            is_active=True,
        )
        .first()
    )

    if not guardian:
        raise PermissionDenied(
            "No guardian profile is "
            "linked to this account."
        )

    student_links = (
        guardian.student_links
        .filter(
            school=school,
        )
        .select_related(
            "student"
        )
    )

    children = [
        link.student
        for link in student_links
    ]

    return render(
        request,
        "portal/parent_dashboard.html",
        {
            "guardian": guardian,
            "children": children,
        },
    )


@tenant_login_required
def student_dashboard(
    request,
):
    school = request.school

    student = (
        Student.objects
        .for_school(school)
        .filter(
            user=request.user,
        )
        .first()
    )

    if not student:
        raise PermissionDenied(
            "No student profile is "
            "linked to this account."
        )

    enrollments = (
        student.enrollments
        .filter(
            school=school
        )
        .select_related(
            "academic_year",
            "class_section__level",
        )
        .order_by(
            "-academic_year__starts_on"
        )
    )

    return render(
        request,
        "portal/student_dashboard.html",
        {
            "student": student,
            "enrollments": enrollments,
        },
    )


@tenant_login_required
def academic_dashboard(
    request,
):
    if not (
        request.user.is_superuser
        or request.user.is_platform_admin
        or has_role(
            user=request.user,
            school=request.school,
            role_code="academic-admin",
        )
    ):
        raise PermissionDenied

    school = request.school

    context = {
        "active_students": (
            Student.objects
            .for_school(school)
            .filter(
                status=Student.Status.ACTIVE
            )
            .count()
        ),

        "active_enrollments": (
            Enrollment.objects
            .for_school(school)
            .filter(
                status=Enrollment.Status.ACTIVE
            )
            .count()
        ),
    }

    return render(
        request,
        "portal/academic_dashboard.html",
        context,
    )


@tenant_login_required
def finance_dashboard(
    request,
):
    if not (
        request.user.is_superuser
        or request.user.is_platform_admin
        or has_role(
            user=request.user,
            school=request.school,
            role_code="finance",
        )
    ):
        raise PermissionDenied

    school = request.school

    ledger_totals = (
        LedgerEntry.objects
        .for_school(school)
        .aggregate(
            debit=Sum("debit"),
            credit=Sum("credit"),
        )
    )

    total_debit = (
        ledger_totals["debit"]
        or Decimal("0")
    )

    total_credit = (
        ledger_totals["credit"]
        or Decimal("0")
    )

    outstanding = (
        total_debit
        - total_credit
    )

    recent_payments = (
        Payment.objects
        .for_school(school)
        .filter(
            status=(
                Payment.Status.CONFIRMED
            )
        )
        .select_related(
            "enrollment__student"
        )
        .order_by(
            "-paid_at"
        )[:10]
    )

    context = {
        "total_billed": (
            total_debit
        ),

        "total_credits": (
            total_credit
        ),

        "outstanding": (
            outstanding
        ),

        "recent_payments": (
            recent_payments
        ),
    }

    return render(
        request,
        "portal/finance_dashboard.html",
        context,
    )