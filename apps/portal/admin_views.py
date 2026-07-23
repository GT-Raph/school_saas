from django.contrib import messages
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from apps.accounts.decorators import (
    school_permission_required,
    tenant_login_required,
)
from apps.guardians.forms import (
    GuardianForm,
    StudentGuardianLinkForm,
)
from apps.guardians.models import (
    Guardian,
)
from apps.guardians.services import (
    link_guardian_to_student,
)
from apps.schools.forms import (
    SchoolBrandingForm,
    SchoolProfileForm,
)
from apps.schools.models import (
    SchoolBranding,
)
from apps.staff.forms import (
    StaffForm,
)
from apps.staff.models import (
    Staff,
)
from apps.students.forms import (
    StudentAdmissionForm,
    StudentForm,
    StudentImportUploadForm,
)
from apps.students.imports import (
    confirm_student_import,
    stage_student_import,
)
from apps.students.models import (
    Student,
    StudentImportBatch,
)
from apps.students.services import (
    admit_student,
)
from apps.subscriptions.decorators import (
    subscription_write_required,
)
from apps.subscriptions.services import (
    get_subscription_usage,
)


@tenant_login_required
@school_permission_required(
    "students.view_student"
)
def student_list(
    request,
):
    students = (
        Student.objects
        .for_school(
            request.school
        )
        .select_related(
            "user"
        )
        .order_by(
            "last_name",
            "first_name",
        )
    )

    query = (
        request.GET.get(
            "q",
            ""
        ).strip()
    )

    if query:

        from django.db.models import Q

        students = students.filter(
            Q(
                admission_number__icontains=(
                    query
                )
            )
            |
            Q(
                first_name__icontains=(
                    query
                )
            )
            |
            Q(
                last_name__icontains=(
                    query
                )
            )
        )

    return render(
        request,
        "portal/students/list.html",
        {
            "students": students[:500],
            "query": query,
        },
    )


@subscription_write_required
@school_permission_required(
    "students.add_student"
)
def student_admit(
    request,
):
    if request.method == "POST":

        form = StudentAdmissionForm(
            request.POST,
            school=request.school,
        )

        if form.is_valid():

            try:

                student = admit_student(
                    school=request.school,

                    data=(
                        form.cleaned_data
                    ),

                    created_by=(
                        request.user
                    ),
                )

            except ValidationError as exc:

                form.add_error(
                    None,
                    exc.messages
                )

            else:

                messages.success(
                    request,
                    (
                        f"{student.full_name} "
                        "was admitted successfully."
                    ),
                )

                return redirect(
                    "portal:student-detail",
                    student_id=(
                        student.id
                    ),
                )

    else:

        form = StudentAdmissionForm(
            school=request.school
        )

    return render(
        request,
        "portal/form.html",
        {
            "title": "Admit Student",
            "form": form,
            "submit_label":
                "Admit Student",
        },
    )


@tenant_login_required
@school_permission_required(
    "students.view_student"
)
def student_detail(
    request,
    student_id,
):
    student = get_object_or_404(
        Student.objects
        .for_school(
            request.school
        ),
        id=student_id,
    )

    enrollments = (
        student.enrollments
        .filter(
            school=request.school
        )
        .select_related(
            "academic_year",
            "class_section__level",
        )
        .order_by(
            "-academic_year__starts_on"
        )
    )

    guardian_links = (
        student.guardian_links
        .filter(
            school=request.school
        )
        .select_related(
            "guardian"
        )
    )

    usage = get_subscription_usage(
        school=request.school
    )

    return render(
        request,
        (
            "portal/students/"
            "detail.html"
        ),
        {
            "student": student,
            "enrollments": enrollments,
            "guardian_links":
                guardian_links,
            "usage": usage,
        },
    )


@subscription_write_required
@school_permission_required(
    "students.change_student"
)
def student_edit(
    request,
    student_id,
):
    student = get_object_or_404(
        Student.objects
        .for_school(
            request.school
        ),
        id=student_id,
    )

    if request.method == "POST":

        form = StudentForm(
            request.POST,
            instance=student,
        )

        if form.is_valid():

            student = form.save(
                commit=False
            )

            student.school = (
                request.school
            )

            student.full_clean()
            student.save()

            messages.success(
                request,
                "Student updated successfully.",
            )

            return redirect(
                "portal:student-detail",
                student_id=student.id,
            )

    else:

        form = StudentForm(
            instance=student
        )

    return render(
        request,
        "portal/form.html",
        {
            "title":
                "Edit Student",

            "form":
                form,

            "submit_label":
                "Save Changes",
        },
    )


@tenant_login_required
@school_permission_required(
    "guardians.view_guardian"
)
def guardian_list(
    request,
):
    guardians = (
        Guardian.objects
        .for_school(
            request.school
        )
        .order_by(
            "last_name",
            "first_name",
        )
    )

    return render(
        request,
        (
            "portal/guardians/"
            "list.html"
        ),
        {
            "guardians": guardians[:500],
        },
    )


@subscription_write_required
@school_permission_required(
    "guardians.add_guardian"
)
def guardian_create(
    request,
):
    if request.method == "POST":

        form = GuardianForm(
            request.POST
        )

        if form.is_valid():

            guardian = form.save(
                commit=False
            )

            guardian.school = (
                request.school
            )

            guardian.full_clean()
            guardian.save()

            messages.success(
                request,
                "Guardian created successfully.",
            )

            return redirect(
                "portal:guardian-list"
            )

    else:

        form = GuardianForm()

    return render(
        request,
        "portal/form.html",
        {
            "title":
                "Add Guardian",

            "form":
                form,

            "submit_label":
                "Save Guardian",
        },
    )


@subscription_write_required
@school_permission_required(
    "guardians.add_studentguardian"
)
def guardian_link(
    request,
):
    if request.method == "POST":

        form = (
            StudentGuardianLinkForm(
                request.POST,
                school=request.school,
            )
        )

        if form.is_valid():

            try:

                link_guardian_to_student(
                    school=request.school,

                    student=(
                        form.cleaned_data[
                            "student"
                        ]
                    ),

                    guardian=(
                        form.cleaned_data[
                            "guardian"
                        ]
                    ),

                    relationship=(
                        form.cleaned_data[
                            "relationship"
                        ]
                    ),

                    is_primary_contact=(
                        form.cleaned_data[
                            "is_primary_contact"
                        ]
                    ),

                    financially_responsible=(
                        form.cleaned_data[
                            "financially_responsible"
                        ]
                    ),

                    receives_reports=(
                        form.cleaned_data[
                            "receives_reports"
                        ]
                    ),

                    emergency_contact=(
                        form.cleaned_data[
                            "emergency_contact"
                        ]
                    ),

                    can_collect_student=(
                        form.cleaned_data[
                            "can_collect_student"
                        ]
                    ),
                )

            except ValidationError as exc:

                form.add_error(
                    None,
                    exc.messages
                )

            else:

                messages.success(
                    request,
                    (
                        "Guardian linked "
                        "successfully."
                    ),
                )

                return redirect(
                    "portal:guardian-list"
                )

    else:

        form = (
            StudentGuardianLinkForm(
                school=request.school
            )
        )

    return render(
        request,
        "portal/form.html",
        {
            "title":
                "Link Guardian to Student",

            "form":
                form,

            "submit_label":
                "Create Link",
        },
    )


@tenant_login_required
@school_permission_required(
    "staff.view_staff"
)
def staff_list(
    request,
):
    staff_members = (
        Staff.objects
        .for_school(
            request.school
        )
        .order_by(
            "last_name",
            "first_name",
        )
    )

    return render(
        request,
        "portal/staff/list.html",
        {
            "staff_members":
                staff_members[:500],
        },
    )


@subscription_write_required
@school_permission_required(
    "staff.add_staff"
)
def staff_create(
    request,
):
    if request.method == "POST":

        form = StaffForm(
            request.POST
        )

        if form.is_valid():

            staff = form.save(
                commit=False
            )

            staff.school = (
                request.school
            )

            staff.full_clean()
            staff.save()

            messages.success(
                request,
                "Staff member created successfully.",
            )

            return redirect(
                "portal:staff-list"
            )

    else:

        form = StaffForm()

    return render(
        request,
        "portal/form.html",
        {
            "title":
                "Add Staff Member",

            "form":
                form,

            "submit_label":
                "Save Staff",
        },
    )


@subscription_write_required
@school_permission_required(
    "staff.change_staff"
)
def staff_edit(
    request,
    staff_id,
):
    staff = get_object_or_404(
        Staff.objects
        .for_school(
            request.school
        ),
        id=staff_id,
    )

    if request.method == "POST":

        form = StaffForm(
            request.POST,
            instance=staff,
        )

        if form.is_valid():

            staff = form.save(
                commit=False
            )

            staff.school = (
                request.school
            )

            staff.full_clean()
            staff.save()

            messages.success(
                request,
                "Staff record updated.",
            )

            return redirect(
                "portal:staff-list"
            )

    else:

        form = StaffForm(
            instance=staff
        )

    return render(
        request,
        "portal/form.html",
        {
            "title":
                "Edit Staff Member",

            "form":
                form,

            "submit_label":
                "Save Changes",
        },
    )


@subscription_write_required
@school_permission_required(
    "students.add_student"
)
def student_import_upload(
    request,
):
    if request.method == "POST":

        form = (
            StudentImportUploadForm(
                request.POST,
                request.FILES,
            )
        )

        if form.is_valid():

            try:

                batch = (
                    stage_student_import(
                        school=(
                            request.school
                        ),

                        uploaded_file=(
                            form.cleaned_data[
                                "file"
                            ]
                        ),

                        uploaded_by=(
                            request.user
                        ),
                    )
                )

            except ValidationError as exc:

                form.add_error(
                    None,
                    exc.messages
                )

            else:

                return redirect(
                    "portal:"
                    "student-import-detail",

                    batch_id=batch.id,
                )

    else:

        form = (
            StudentImportUploadForm()
        )

    return render(
        request,
        "portal/form.html",
        {
            "title":
                "Bulk Import Students",

            "form":
                form,

            "submit_label":
                "Upload and Validate",

            "multipart":
                True,
        },
    )


@tenant_login_required
@school_permission_required(
    "students.view_student"
)
def student_import_detail(
    request,
    batch_id,
):
    batch = get_object_or_404(
        StudentImportBatch.objects
        .for_school(
            request.school
        ),
        id=batch_id,
    )

    rows = (
        batch.rows
        .all()[:500]
    )

    usage = get_subscription_usage(
        school=request.school
    )

    return render(
        request,
        (
            "portal/students/"
            "import_detail.html"
        ),
        {
            "batch": batch,
            "rows": rows,
            "usage": usage,
        },
    )


@subscription_write_required
@school_permission_required(
    "students.add_student"
)
def student_import_confirm(
    request,
    batch_id,
):
    if request.method != "POST":

        raise PermissionDenied

    batch = get_object_or_404(
        StudentImportBatch.objects
        .for_school(
            request.school
        ),
        id=batch_id,
    )

    try:

        imported = (
            confirm_student_import(
                batch=batch,

                confirmed_by=(
                    request.user
                ),
            )
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
            (
                f"{len(imported)} students "
                "were imported successfully."
            ),
        )

    return redirect(
        "portal:"
        "student-import-detail",

        batch_id=batch.id,
    )


@tenant_login_required
@school_permission_required(
    "schools.manage_school_settings"
)
def admin_studio(
    request,
):
    usage = get_subscription_usage(
        school=request.school
    )

    return render(
        request,
        (
            "portal/admin_studio/"
            "index.html"
        ),
        {
            "usage": usage,
        },
    )


@subscription_write_required
@school_permission_required(
    "schools.manage_school_settings"
)
def school_profile_settings(
    request,
):
    school = request.school

    if request.method == "POST":

        form = SchoolProfileForm(
            request.POST,
            instance=school,
        )

        if form.is_valid():

            school = form.save()

            messages.success(
                request,
                "School profile updated.",
            )

            return redirect(
                "portal:admin-studio"
            )

    else:

        form = SchoolProfileForm(
            instance=school
        )

    return render(
        request,
        "portal/form.html",
        {
            "title":
                "School Profile",

            "form":
                form,

            "submit_label":
                "Save Settings",
        },
    )


@subscription_write_required
@school_permission_required(
    "schools.manage_school_settings"
)
def school_branding_settings(
    request,
):
    branding, _ = (
        SchoolBranding.objects
        .get_or_create(
            school=request.school
        )
    )

    if request.method == "POST":

        form = SchoolBrandingForm(
            request.POST,
            instance=branding,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Branding updated.",
            )

            return redirect(
                "portal:admin-studio"
            )

    else:

        form = SchoolBrandingForm(
            instance=branding
        )

    return render(
        request,
        "portal/form.html",
        {
            "title":
                "School Branding",

            "form":
                form,

            "submit_label":
                "Save Branding",
        },
    )