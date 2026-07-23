from django import forms

from apps.academics.models import (
    AcademicYear,
    ClassSection,
)

from .models import Student


class StudentAdmissionForm(
    forms.Form
):
    admission_number = forms.CharField(
        max_length=50,
    )

    first_name = forms.CharField(
        max_length=100,
    )

    middle_name = forms.CharField(
        max_length=100,
        required=False,
    )

    last_name = forms.CharField(
        max_length=100,
    )

    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    gender = forms.ChoiceField(
        choices=Student.Gender.choices,
    )

    admission_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    phone_number = forms.CharField(
        max_length=30,
        required=False,
    )

    email = forms.EmailField(
        required=False,
    )

    academic_year = (
        forms.ModelChoiceField(
            queryset=(
                AcademicYear.objects.none()
            )
        )
    )

    class_section = (
        forms.ModelChoiceField(
            queryset=(
                ClassSection.objects.none()
            )
        )
    )

    enrolled_on = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    guardian_first_name = (
        forms.CharField(
            max_length=100,
            required=False,
        )
    )

    guardian_last_name = (
        forms.CharField(
            max_length=100,
            required=False,
        )
    )

    guardian_phone = forms.CharField(
        max_length=30,
        required=False,
    )

    guardian_email = forms.EmailField(
        required=False,
    )

    guardian_relationship = (
        forms.ChoiceField(
            required=False,
            choices=[
                ("", "---------"),
                ("mother", "Mother"),
                ("father", "Father"),
                ("guardian", "Guardian"),
                ("aunt", "Aunt"),
                ("uncle", "Uncle"),
                ("grandmother", "Grandmother"),
                ("grandfather", "Grandfather"),
                ("other", "Other"),
            ],
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

        self.school = school

        if school:

            self.fields[
                "academic_year"
            ].queryset = (
                AcademicYear.objects
                .for_school(school)
                .filter(
                    status__in=[
                        AcademicYear
                        .Status.PLANNED,

                        AcademicYear
                        .Status.ACTIVE,
                    ]
                )
                .order_by(
                    "-starts_on"
                )
            )

            self.fields[
                "class_section"
            ].queryset = (
                ClassSection.objects
                .for_school(school)
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

    def clean(
        self,
    ):
        cleaned = super().clean()

        academic_year = cleaned.get(
            "academic_year"
        )

        class_section = cleaned.get(
            "class_section"
        )

        admission_number = cleaned.get(
            "admission_number"
        )

        if (
            self.school
            and admission_number
            and Student.objects
            .for_school(self.school)
            .filter(
                admission_number=(
                    admission_number
                )
            )
            .exists()
        ):
            self.add_error(
                "admission_number",
                (
                    "A student with this "
                    "admission number already "
                    "exists."
                ),
            )

        enrolled_on = cleaned.get(
            "enrolled_on"
        )

        if (
            academic_year
            and enrolled_on
            and not (
                academic_year.starts_on
                <= enrolled_on
                <= academic_year.ends_on
            )
        ):
            self.add_error(
                "enrolled_on",
                (
                    "Enrollment date must fall "
                    "within the academic year."
                ),
            )

        guardian_values = [
            cleaned.get(
                "guardian_first_name"
            ),
            cleaned.get(
                "guardian_last_name"
            ),
            cleaned.get(
                "guardian_phone"
            ),
        ]

        if any(
            guardian_values
        ) and not all(
            guardian_values
        ):
            raise forms.ValidationError(
                (
                    "To add a guardian during "
                    "admission, first name, "
                    "last name and phone number "
                    "are required."
                )
            )

        return cleaned


class StudentForm(
    forms.ModelForm
):
    class Meta:
        model = Student

        fields = [
            "admission_number",
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",
            "admission_date",
            "phone_number",
            "email",
            "status",
            "notes",
        ]

        widgets = {
            "date_of_birth":
                forms.DateInput(
                    attrs={
                        "type": "date",
                    }
                ),

            "admission_date":
                forms.DateInput(
                    attrs={
                        "type": "date",
                    }
                ),
        }


class StudentImportUploadForm(
    forms.Form
):
    file = forms.FileField(
        help_text=(
            "Upload CSV or XLSX. "
            "Maximum size 5 MB."
        )
    )

    def clean_file(
        self,
    ):
        uploaded = (
            self.cleaned_data[
                "file"
            ]
        )

        max_size = (
            5
            * 1024
            * 1024
        )

        if uploaded.size > max_size:

            raise forms.ValidationError(
                "File must not exceed 5 MB."
            )

        filename = (
            uploaded.name.lower()
        )

        if not (
            filename.endswith(
                ".csv"
            )
            or filename.endswith(
                ".xlsx"
            )
        ):
            raise forms.ValidationError(
                (
                    "Only CSV and XLSX "
                    "files are supported."
                )
            )

        return uploaded