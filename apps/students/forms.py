from django import forms

from apps.academics.models import (
    AcademicYear,
    ClassSection,
)

from .models import Student


class StudentAdmissionForm(
    forms.Form
):
    """
    Form used for admitting a new student.

    Admission numbers are NOT entered manually.
    They are generated automatically by the
    student admission service.
    """

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
                (
                    "",
                    "---------",
                ),
                (
                    "mother",
                    "Mother",
                ),
                (
                    "father",
                    "Father",
                ),
                (
                    "guardian",
                    "Guardian",
                ),
                (
                    "aunt",
                    "Aunt",
                ),
                (
                    "uncle",
                    "Uncle",
                ),
                (
                    "grandmother",
                    "Grandmother",
                ),
                (
                    "grandfather",
                    "Grandfather",
                ),
                (
                    "other",
                    "Other",
                ),
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
                .for_school(
                    school
                )
                .filter(
                    status__in=[
                        (
                            AcademicYear
                            .Status
                            .PLANNED
                        ),
                        (
                            AcademicYear
                            .Status
                            .ACTIVE
                        ),
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
                .for_school(
                    school
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

    def clean(
        self,
    ):
        cleaned = (
            super().clean()
        )

        academic_year = (
            cleaned.get(
                "academic_year"
            )
        )

        class_section = (
            cleaned.get(
                "class_section"
            )
        )

        admission_date = (
            cleaned.get(
                "admission_date"
            )
        )

        enrolled_on = (
            cleaned.get(
                "enrolled_on"
            )
        )

        # -----------------------------------------------------
        # Academic year validation
        # -----------------------------------------------------

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
                    "Enrollment date must "
                    "fall within the "
                    "academic year."
                ),
            )

        # -----------------------------------------------------
        # Make sure class belongs to this school
        # -----------------------------------------------------

        if (
            self.school
            and class_section
            and class_section.school_id
            != self.school.id
        ):
            self.add_error(
                "class_section",
                (
                    "Selected class does "
                    "not belong to this "
                    "school."
                ),
            )

        # -----------------------------------------------------
        # Admission date validation
        # -----------------------------------------------------

        if (
            admission_date
            and enrolled_on
            and admission_date
            > enrolled_on
        ):
            self.add_error(
                "admission_date",
                (
                    "Admission date cannot "
                    "be after the enrollment "
                    "date."
                ),
            )

        # -----------------------------------------------------
        # Guardian validation
        # -----------------------------------------------------

        guardian_first_name = (
            cleaned.get(
                "guardian_first_name"
            )
        )

        guardian_last_name = (
            cleaned.get(
                "guardian_last_name"
            )
        )

        guardian_phone = (
            cleaned.get(
                "guardian_phone"
            )
        )

        guardian_relationship = (
            cleaned.get(
                "guardian_relationship"
            )
        )

        guardian_values = [
            guardian_first_name,
            guardian_last_name,
            guardian_phone,
            guardian_relationship,
        ]

        if any(
            guardian_values
        ):

            required_guardian_values = [
                guardian_first_name,
                guardian_last_name,
                guardian_phone,
            ]

            if not all(
                required_guardian_values
            ):
                raise forms.ValidationError(
                    (
                        "To add a guardian "
                        "during admission, "
                        "guardian first name, "
                        "last name and phone "
                        "number are required."
                    )
                )

        return cleaned


class StudentForm(
    forms.ModelForm
):
    """
    Used when editing an existing student.

    Admission number is displayed but cannot
    be manually changed.
    """

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

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        if (
            "admission_number"
            in self.fields
        ):
            self.fields[
                "admission_number"
            ].disabled = True

            self.fields[
                "admission_number"
            ].help_text = (
                "Generated automatically "
                "by the system."
            )


class StudentImportUploadForm(
    forms.Form
):
    file = forms.FileField(
        help_text=(
            "Upload the completed CSV "
            "or XLSX student template. "
            "Admission numbers are generated "
            "automatically. Maximum size 5 MB."
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

        if (
            uploaded.size
            > max_size
        ):
            raise forms.ValidationError(
                (
                    "File must not exceed "
                    "5 MB."
                )
            )

        filename = (
            uploaded.name
            .lower()
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