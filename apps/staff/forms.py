from django import forms

from .models import Staff


class StaffForm(
    forms.ModelForm
):

    class Meta:
        model = Staff

        fields = [
            "employee_number",
            "first_name",
            "middle_name",
            "last_name",
            "job_title",
            "department",
            "is_teacher",
            "phone_number",
            "email",
            "employment_date",
            "employment_status",
            "notes",
        ]

        widgets = {
            "employment_date":
                forms.DateInput(
                    attrs={
                        "type": "date",
                    }
                ),
        }