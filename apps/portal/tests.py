from datetime import date

from django.contrib.auth.models import Permission
from django.test import (
    Client,
    TestCase,
    override_settings,
)
from django.urls import reverse

from apps.accounts.models import User
from apps.academics.models import (
    AcademicYear,
    ClassLevel,
    ClassSection,
    Subject,
    SubjectOffering,
    TeacherAssignment,
)
from apps.schools.models import (
    School,
    SchoolDomain,
    SchoolMembership,
    SchoolRole,
)
from apps.staff.models import Staff


@override_settings(
    ALLOWED_HOSTS=[
        "testserver",
        "school-a.testserver",
        "school-b.testserver",
    ]
)
class PortalTenantSecurityTests(TestCase):

    def setUp(self):
        self.school_a = School.objects.create(
            name="School A",
            slug="school-a",
        )

        self.school_b = School.objects.create(
            name="School B",
            slug="school-b",
        )

        SchoolDomain.objects.create(
            school=self.school_a,
            domain="school-a.testserver",
            is_verified=True,
            is_primary=True,
        )

        SchoolDomain.objects.create(
            school=self.school_b,
            domain="school-b.testserver",
            is_verified=True,
            is_primary=True,
        )

        self.user_a = User.objects.create_user(
            username="user_a",
            password="Password123!",
        )

        self.role_a = SchoolRole.objects.create(
            school=self.school_a,
            name="School Administrator",
            code="school-admin",
        )

        self.membership_a = (
            SchoolMembership.objects.create(
                user=self.user_a,
                school=self.school_a,
                is_active=True,
            )
        )

        self.membership_a.roles.add(
            self.role_a
        )

        self.client = Client()

    def test_user_can_login_to_own_school(
        self,
    ):
        response = self.client.post(
            reverse(
                "accounts:login"
            ),
            {
                "username": "user_a",
                "password": "Password123!",
            },
            HTTP_HOST="school-a.testserver",
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertTrue(
            response.wsgi_request
            .user
            .is_authenticated
        )

    def test_user_cannot_login_to_other_school(
        self,
    ):
        response = self.client.post(
            reverse(
                "accounts:login"
            ),
            {
                "username": "user_a",
                "password": "Password123!",
            },
            HTTP_HOST="school-b.testserver",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            (
                "Your account does not "
                "have access to this school."
            ),
        )

        self.assertFalse(
            response.wsgi_request
            .user
            .is_authenticated
        )

    def test_school_a_user_cannot_access_school_b_portal(
        self,
    ):
        logged_in = self.client.login(
            username="user_a",
            password="Password123!",
        )

        self.assertTrue(
            logged_in
        )

        response = self.client.get(
            reverse(
                "portal:home"
            ),
            HTTP_HOST="school-b.testserver",
        )

        self.assertEqual(
            response.status_code,
            403,
        )


@override_settings(
    ALLOWED_HOSTS=[
        "testserver",
        "teacher-security.testserver",
    ]
)
class TeacherObjectAccessTests(TestCase):

    def setUp(self):
        self.school = School.objects.create(
            name="Teacher Security School",
            slug="teacher-security",
        )

        SchoolDomain.objects.create(
            school=self.school,
            domain="teacher-security.testserver",
            is_verified=True,
            is_primary=True,
        )

        self.user_one = User.objects.create_user(
            username="teacher_one",
            password="Password123!",
        )

        self.user_two = User.objects.create_user(
            username="teacher_two",
            password="Password123!",
        )

        # Create teacher role.
        self.role = SchoolRole.objects.create(
            school=self.school,
            name="Teacher",
            code="teacher",
        )

        # Give the teacher role permission to view
        # teacher assignments.
        permission = Permission.objects.get(
            content_type__app_label=(
                "academics"
            ),
            codename=(
                "view_teacherassignment"
            ),
        )

        self.role.permissions.add(
            permission
        )

        # Create memberships for both teachers.
        for user in [
            self.user_one,
            self.user_two,
        ]:
            membership = (
                SchoolMembership.objects.create(
                    school=self.school,
                    user=user,
                    is_active=True,
                )
            )

            membership.roles.add(
                self.role
            )

        self.teacher_one = Staff.objects.create(
            school=self.school,
            user=self.user_one,
            employee_number="T001",
            first_name="Teacher",
            last_name="One",
            is_teacher=True,
            employment_status=(
                Staff.EmploymentStatus.ACTIVE
            ),
        )

        self.teacher_two = Staff.objects.create(
            school=self.school,
            user=self.user_two,
            employee_number="T002",
            first_name="Teacher",
            last_name="Two",
            is_teacher=True,
            employment_status=(
                Staff.EmploymentStatus.ACTIVE
            ),
        )

        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026/2027",
            starts_on=date(
                2026,
                9,
                1,
            ),
            ends_on=date(
                2027,
                7,
                31,
            ),
        )

        self.level = ClassLevel.objects.create(
            school=self.school,
            name="Basic 4",
            code="basic-4",
            order=4,
        )

        self.section_a = (
            ClassSection.objects.create(
                school=self.school,
                level=self.level,
                name="A",
                code="a",
            )
        )

        self.section_b = (
            ClassSection.objects.create(
                school=self.school,
                level=self.level,
                name="B",
                code="b",
            )
        )

        self.subject = Subject.objects.create(
            school=self.school,
            name="Mathematics",
            code="mathematics",
        )

        self.offering_one = (
            SubjectOffering.objects.create(
                school=self.school,
                academic_year=self.year,
                class_section=self.section_a,
                subject=self.subject,
            )
        )

        self.offering_two = (
            SubjectOffering.objects.create(
                school=self.school,
                academic_year=self.year,
                class_section=self.section_b,
                subject=self.subject,
            )
        )

        TeacherAssignment.objects.create(
            school=self.school,
            offering=self.offering_one,
            teacher=self.teacher_one,
            starts_on=date(
                2026,
                9,
                1,
            ),
            is_primary=True,
            is_active=True,
        )

        TeacherAssignment.objects.create(
            school=self.school,
            offering=self.offering_two,
            teacher=self.teacher_two,
            starts_on=date(
                2026,
                9,
                1,
            ),
            is_primary=True,
            is_active=True,
        )

        self.client = Client()

    def test_teacher_cannot_open_other_teachers_class(
        self,
    ):
        logged_in = self.client.login(
            username="teacher_one",
            password="Password123!",
        )

        self.assertTrue(
            logged_in
        )

        response = self.client.get(
            reverse(
                "portal:teacher-class-detail",
                kwargs={
                    "offering_id": (
                        self.offering_two.id
                    ),
                },
            ),
            HTTP_HOST=(
                "teacher-security.testserver"
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )