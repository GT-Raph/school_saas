from django.test import (
    Client,
    TestCase,
    override_settings,
)
from django.urls import reverse

from apps.accounts.models import User

from apps.schools.models import (
    School,
    SchoolDomain,
    SchoolMembership,
    SchoolRole,
)


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
            response.wsgi_request.user.is_authenticated
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
            response.wsgi_request.user.is_authenticated
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