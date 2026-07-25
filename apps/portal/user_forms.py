from django import forms
from django.contrib.auth.password_validation import (
    validate_password,
)

from apps.guardians.models import Guardian
from apps.schools.models import SchoolRole
from apps.staff.models import Staff
from apps.students.models import Student


class SchoolUserCreateForm(
    forms.Form
):

    username = forms.CharField(
        max_length=150,
    )

    first_name = forms.CharField(
        max_length=150,
    )

    last_name = forms.CharField(
        max_length=150,
    )

    email = forms.EmailField(
        required=False,
    )

    temporary_password = forms.CharField(
        widget=forms.PasswordInput(),
        min_length=10,
    )

    role = forms.ModelChoiceField(
        queryset=SchoolRole.objects.none()
    )

    staff_profile = forms.ModelChoiceField(
        queryset=Staff.objects.none(),
        required=False,
    )

    guardian_profile = forms.ModelChoiceField(
        queryset=Guardian.objects.none(),
        required=False,
    )

    student_profile = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        required=False,
    )

    def __init__(
        self,
        *args,
        school=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.school = school

        if school:

            self.fields[
                "role"
            ].queryset = (
                SchoolRole.objects
                .filter(
                    school=school
                )
                .order_by(
                    "name"
                )
            )

            self.fields[
                "staff_profile"
            ].queryset = (
                Staff.objects
                .for_school(school)
                .filter(
                    user__isnull=True
                )
                .order_by(
                    "last_name",
                    "first_name",
                )
            )

            self.fields[
                "guardian_profile"
            ].queryset = (
                Guardian.objects
                .for_school(school)
                .filter(
                    user__isnull=True,
                    is_active=True,
                )
                .order_by(
                    "last_name",
                    "first_name",
                )
            )

            self.fields[
                "student_profile"
            ].queryset = (
                Student.objects
                .for_school(school)
                .filter(
                    user__isnull=True
                )
                .order_by(
                    "last_name",
                    "first_name",
                )
            )

    def clean_temporary_password(
        self,
    ):
        password = self.cleaned_data[
            "temporary_password"
        ]

        validate_password(
            password
        )

        return password

    def clean(
        self,
    ):
        cleaned = super().clean()

        role = cleaned.get(
            "role"
        )

        staff = cleaned.get(
            "staff_profile"
        )

        guardian = cleaned.get(
            "guardian_profile"
        )

        student = cleaned.get(
            "student_profile"
        )

        selected_profiles = [
            profile
            for profile in [
                staff,
                guardian,
                student,
            ]
            if profile is not None
        ]

        if len(
            selected_profiles
        ) > 1:

            raise forms.ValidationError(
                (
                    "Select only one linked "
                    "person profile."
                )
            )

        if role:

            if (
                role.code == "teacher"
                and not staff
            ):

                self.add_error(
                    "staff_profile",
                    (
                        "A Teacher account must "
                        "be linked to a staff profile."
                    ),
                )

            if (
                role.code == "teacher"
                and staff
                and not staff.is_teacher
            ):

                self.add_error(
                    "staff_profile",
                    (
                        "The selected staff member "
                        "is not marked as a teacher."
                    ),
                )

            if (
                role.code == "parent"
                and not guardian
            ):

                self.add_error(
                    "guardian_profile",
                    (
                        "A Parent account must be "
                        "linked to a guardian."
                    ),
                )

            if (
                role.code == "student"
                and not student
            ):

                self.add_error(
                    "student_profile",
                    (
                        "A Student account must be "
                        "linked to a student record."
                    ),
                )

        return cleaned


class SchoolMembershipUpdateForm(
    forms.Form
):

    roles = forms.ModelMultipleChoiceField(
        queryset=SchoolRole.objects.none(),
        required=False,
    )

    is_active = forms.BooleanField(
        required=False,
    )

    def __init__(
        self,
        *args,
        school=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        if school:

            self.fields[
                "roles"
            ].queryset = (
                SchoolRole.objects
                .filter(
                    school=school
                )
                .order_by(
                    "name"
                )
            )