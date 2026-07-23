from django import forms

from apps.students.models import (
    Student,
)

from .models import (
    Guardian,
    StudentGuardian,
)


class GuardianForm(
    forms.ModelForm
):

    class Meta:
        model = Guardian

        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "alternative_phone",
            "email",
            "occupation",
            "address",
            "is_active",
        ]


class StudentGuardianLinkForm(
    forms.Form
):

    student = (
        forms.ModelChoiceField(
            queryset=(
                Student.objects.none()
            )
        )
    )

    guardian = (
        forms.ModelChoiceField(
            queryset=(
                Guardian.objects.none()
            )
        )
    )

    relationship = (
        forms.ChoiceField(
            choices=(
                StudentGuardian
                .Relationship.choices
            )
        )
    )

    is_primary_contact = (
        forms.BooleanField(
            required=False,
        )
    )

    financially_responsible = (
        forms.BooleanField(
            required=False,
        )
    )

    receives_reports = (
        forms.BooleanField(
            required=False,
            initial=True,
        )
    )

    emergency_contact = (
        forms.BooleanField(
            required=False,
        )
    )

    can_collect_student = (
        forms.BooleanField(
            required=False,
        )
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
                "student"
            ].queryset = (
                Student.objects
                .for_school(school)
                .order_by(
                    "last_name",
                    "first_name",
                )
            )

            self.fields[
                "guardian"
            ].queryset = (
                Guardian.objects
                .for_school(school)
                .filter(
                    is_active=True
                )
                .order_by(
                    "last_name",
                    "first_name",
                )
            )