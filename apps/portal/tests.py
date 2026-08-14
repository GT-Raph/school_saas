from datetime import date

from django.contrib.auth import SESSION_KEY
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

from apps.guardians.models import (
    Guardian,
    StudentGuardian,
)

from apps.schools.models import (
    School,
    SchoolDomain,
    SchoolMembership,
    SchoolRole,
)

from apps.staff.models import Staff
from apps.students.models import Student


# =====================================================================
# PORTAL / TENANT SECURITY
# =====================================================================


@override_settings(
    DEBUG=True,
    PLATFORM_LOGIN_HOST="login.localhost",
    PLATFORM_BASE_DOMAIN="",
    DEV_SERVER_PORT="8000",
    ALLOWED_HOSTS=[
        "testserver",
        "localhost",
        ".localhost",
        "login.localhost",
        "school-a.localhost",
        "school-b.localhost",
        "school-a.testserver",
        "school-b.testserver",
    ],
)
class PortalTenantSecurityTests(TestCase):

    def setUp(self):

        self.password = "Password123!"

        # -------------------------------------------------------------
        # Schools
        # -------------------------------------------------------------

        self.school_a = School.objects.create(
            name="School A",
            slug="school-a",
        )

        self.school_b = School.objects.create(
            name="School B",
            slug="school-b",
        )

        # These explicit domains are retained so we can also test
        # traditional/custom-domain tenant resolution.
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

        # -------------------------------------------------------------
        # User A
        # -------------------------------------------------------------

        self.user_a = User.objects.create_user(
            username="user_a",
            password=self.password,
        )

        # -------------------------------------------------------------
        # School A role
        # -------------------------------------------------------------

        self.role_a = SchoolRole.objects.create(
            school=self.school_a,
            name="School Administrator",
            code="school-admin",
        )

        # -------------------------------------------------------------
        # User A membership in School A
        # -------------------------------------------------------------

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


    #------------------------------------------------------------------
    # CENTRAL LOGOUT
    #------------------------------------------------------------------

    def test_central_session_is_removed_after_handoff_created(
        self,
    ):
        """
        Once a school handoff has been generated, the central
        authentication session must be destroyed.

        Otherwise a user who logs out of their school would be
        automatically logged back in by the central session.
        """

        central_client = Client()

        response = central_client.post(
            reverse(
                "accounts:login"
            ),
            {
                "username":
                    self.user_a.username,

                "password":
                    self.password,
            },
            HTTP_HOST="login.localhost",
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            SESSION_KEY,
            central_client.session,
        )

        response = central_client.get(
            reverse(
                "accounts:post-login"
            ),
            HTTP_HOST="login.localhost",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "token",
            response.context,
        )

        # Central authentication must now be gone.
        self.assertNotIn(
            SESSION_KEY,
            central_client.session,
        )

    def test_school_logout_does_not_automatically_log_user_back_in(
        self,
    ):
        central_client = Client()

        # ---------------------------------------------------------
        # Central login
        # ---------------------------------------------------------

        central_client.post(
            reverse(
                "accounts:login"
            ),
            {
                "username":
                    self.user_a.username,

                "password":
                    self.password,
            },
            HTTP_HOST="login.localhost",
        )

        response = central_client.get(
            reverse(
                "accounts:post-login"
            ),
            HTTP_HOST="login.localhost",
        )

        token = response.context[
            "token"
        ]

        # ---------------------------------------------------------
        # Establish tenant session
        # ---------------------------------------------------------

        tenant_client = Client()

        response = tenant_client.post(
            reverse(
                "accounts:handoff"
            ),
            {
                "token": token,
            },
            HTTP_HOST="school-a.localhost",
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            SESSION_KEY,
            tenant_client.session,
        )

        # ---------------------------------------------------------
        # Logout from tenant
        # ---------------------------------------------------------

        response = tenant_client.get(
            reverse(
                "accounts:logout"
            ),
            HTTP_HOST="school-a.localhost",
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertNotIn(
            SESSION_KEY,
            tenant_client.session,
        )

        self.assertIn(
            "login.localhost",
            response.url,
        )

    # -----------------------------------------------------------------
    # CENTRAL LOGIN -> CORRECT SCHOOL
    # -----------------------------------------------------------------

    def test_user_can_login_to_own_school(self):
        """
        User authenticates centrally.

        The platform finds the user's active school membership,
        creates a one-use handoff token, and the destination
        school establishes its own authenticated session.
        """

        central_client = Client()

        # -------------------------------------------------------------
        # 1. Authenticate on central login
        # -------------------------------------------------------------

        response = central_client.post(
            reverse(
                "accounts:login"
            ),
            {
                "username":
                    self.user_a.username,

                "password":
                    self.password,
            },
            HTTP_HOST=(
                "login.localhost"
            ),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse(
                "accounts:post-login"
            ),
        )

        # Central host has authenticated the user.
        self.assertIn(
            SESSION_KEY,
            central_client.session,
        )

        # -------------------------------------------------------------
        # 2. Resolve membership and generate handoff
        # -------------------------------------------------------------

        response = central_client.get(
            reverse(
                "accounts:post-login"
            ),
            HTTP_HOST=(
                "login.localhost"
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "token",
            response.context,
        )

        self.assertIn(
            "school",
            response.context,
        )

        self.assertEqual(
            response.context[
                "school"
            ],
            self.school_a,
        )

        token = response.context[
            "token"
        ]

        self.assertTrue(
            token
        )

        # -------------------------------------------------------------
        # 3. Simulate browser arriving at School A
        # -------------------------------------------------------------

        tenant_client = Client()

        response = tenant_client.post(
            reverse(
                "accounts:handoff"
            ),
            {
                "token": token,
            },
            HTTP_HOST=(
                "school-a.localhost"
            ),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        # -------------------------------------------------------------
        # 4. Tenant now has its own authenticated session
        # -------------------------------------------------------------

        self.assertIn(
            SESSION_KEY,
            tenant_client.session,
        )

        self.assertEqual(
            str(
                tenant_client.session[
                    SESSION_KEY
                ]
            ),
            str(
                self.user_a.pk
            ),
        )

    # -----------------------------------------------------------------
    # TOKEN MUST NOT WORK FOR ANOTHER SCHOOL
    # -----------------------------------------------------------------

    def test_user_cannot_login_to_other_school(self):
        """
        A handoff token created for School A must not be usable
        on School B.
        """

        central_client = Client()

        # -------------------------------------------------------------
        # 1. Authenticate centrally
        # -------------------------------------------------------------

        response = central_client.post(
            reverse(
                "accounts:login"
            ),
            {
                "username":
                    self.user_a.username,

                "password":
                    self.password,
            },
            HTTP_HOST=(
                "login.localhost"
            ),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        # -------------------------------------------------------------
        # 2. Generate token for School A
        # -------------------------------------------------------------

        response = central_client.get(
            reverse(
                "accounts:post-login"
            ),
            HTTP_HOST=(
                "login.localhost"
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        token = response.context[
            "token"
        ]

        # -------------------------------------------------------------
        # 3. Attempt to use School A token on School B
        # -------------------------------------------------------------

        school_b_client = Client()

        response = school_b_client.post(
            reverse(
                "accounts:handoff"
            ),
            {
                "token": token,
            },
            HTTP_HOST=(
                "school-b.localhost"
            ),
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        # -------------------------------------------------------------
        # 4. School B must not receive an authenticated session
        # -------------------------------------------------------------

        self.assertNotIn(
            SESSION_KEY,
            school_b_client.session,
        )

    # -----------------------------------------------------------------
    # TENANT ISOLATION AFTER AUTHENTICATION
    # -----------------------------------------------------------------

    def test_school_a_user_cannot_access_school_b_portal(
        self,
    ):
        """
        Even if User A is authenticated, authentication alone must
        never grant access to School B.

        Tenant membership is still required.
        """

        logged_in = self.client.login(
            username=(
                self.user_a.username
            ),
            password=(
                self.password
            ),
        )

        self.assertTrue(
            logged_in
        )

        response = self.client.get(
            reverse(
                "portal:home"
            ),
            HTTP_HOST=(
                "school-b.testserver"
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    # -----------------------------------------------------------------
    # SCHOOL LOGIN PAGE REDIRECTS TO CENTRAL LOGIN
    # -----------------------------------------------------------------

    def test_school_login_redirects_to_central_login(
        self,
    ):
        """
        Users should not log in directly on individual school
        subdomains.

        School login routes redirect to the central authentication
        domain.
        """

        response = self.client.get(
            reverse(
                "accounts:login"
            ),
            HTTP_HOST=(
                "school-a.localhost"
            ),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertTrue(
            response.url.startswith(
                (
                    "http://"
                    "login.localhost:"
                    "8000/"
                )
            )
        )

        self.assertIn(
            "/accounts/login/",
            response.url,
        )

    # -----------------------------------------------------------------
    # HANDOFF TOKEN REPLAY PROTECTION
    # -----------------------------------------------------------------

    def test_login_handoff_cannot_be_reused(
        self,
    ):
        """
        A handoff token must be usable exactly once.
        """

        central_client = Client()

        # -------------------------------------------------------------
        # 1. Central authentication
        # -------------------------------------------------------------

        response = central_client.post(
            reverse(
                "accounts:login"
            ),
            {
                "username":
                    self.user_a.username,

                "password":
                    self.password,
            },
            HTTP_HOST=(
                "login.localhost"
            ),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        # -------------------------------------------------------------
        # 2. Generate handoff token
        # -------------------------------------------------------------

        response = central_client.get(
            reverse(
                "accounts:post-login"
            ),
            HTTP_HOST=(
                "login.localhost"
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        token = response.context[
            "token"
        ]

        # -------------------------------------------------------------
        # 3. First use succeeds
        # -------------------------------------------------------------

        first_client = Client()

        first_response = first_client.post(
            reverse(
                "accounts:handoff"
            ),
            {
                "token": token,
            },
            HTTP_HOST=(
                "school-a.localhost"
            ),
        )

        self.assertEqual(
            first_response.status_code,
            302,
        )

        self.assertIn(
            SESSION_KEY,
            first_client.session,
        )

        # -------------------------------------------------------------
        # 4. Second use must fail
        # -------------------------------------------------------------

        second_client = Client()

        second_response = (
            second_client.post(
                reverse(
                    "accounts:handoff"
                ),
                {
                    "token": token,
                },
                HTTP_HOST=(
                    "school-a.localhost"
                ),
            )
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

        self.assertNotIn(
            SESSION_KEY,
            second_client.session,
        )

    # -----------------------------------------------------------------
    # LOCALHOST SUBDOMAIN TENANT RESOLUTION
    # -----------------------------------------------------------------

    def test_school_slug_resolves_localhost_tenant(
        self,
    ):
        """
        school-a.localhost should resolve School A automatically
        from the school's slug.

        No SchoolDomain row for school-a.localhost is required.
        """

        logged_in = self.client.login(
            username=(
                self.user_a.username
            ),
            password=(
                self.password
            ),
        )

        self.assertTrue(
            logged_in
        )

        response = self.client.get(
            reverse(
                "portal:home"
            ),
            HTTP_HOST=(
                "school-a.localhost"
            ),
        )

        self.assertNotEqual(
            response.status_code,
            403,
        )


# =====================================================================
# TEACHER OBJECT ACCESS SECURITY
# =====================================================================


@override_settings(
    ALLOWED_HOSTS=[
        "testserver",
        "teacher-security.testserver",
    ]
)
class TeacherObjectAccessTests(
    TestCase
):

    def setUp(self):

        self.school = School.objects.create(
            name=(
                "Teacher Security School"
            ),
            slug=(
                "teacher-security"
            ),
        )

        SchoolDomain.objects.create(
            school=self.school,
            domain=(
                "teacher-security.testserver"
            ),
            is_verified=True,
            is_primary=True,
        )

        self.user_one = (
            User.objects.create_user(
                username=(
                    "teacher_one"
                ),
                password=(
                    "Password123!"
                ),
            )
        )

        self.user_two = (
            User.objects.create_user(
                username=(
                    "teacher_two"
                ),
                password=(
                    "Password123!"
                ),
            )
        )

        self.role = (
            SchoolRole.objects.create(
                school=self.school,
                name="Teacher",
                code="teacher",
            )
        )

        permission = (
            Permission.objects.get(
                content_type__app_label=(
                    "academics"
                ),
                codename=(
                    "view_teacherassignment"
                ),
            )
        )

        self.role.permissions.add(
            permission
        )

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

        self.teacher_one = (
            Staff.objects.create(
                school=self.school,
                user=self.user_one,
                employee_number="T001",
                first_name="Teacher",
                last_name="One",
                is_teacher=True,
                employment_status=(
                    Staff
                    .EmploymentStatus
                    .ACTIVE
                ),
            )
        )

        self.teacher_two = (
            Staff.objects.create(
                school=self.school,
                user=self.user_two,
                employee_number="T002",
                first_name="Teacher",
                last_name="Two",
                is_teacher=True,
                employment_status=(
                    Staff
                    .EmploymentStatus
                    .ACTIVE
                ),
            )
        )

        self.year = (
            AcademicYear.objects.create(
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
        )

        self.level = (
            ClassLevel.objects.create(
                school=self.school,
                name="Basic 4",
                code="basic-4",
                order=4,
            )
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

        self.subject = (
            Subject.objects.create(
                school=self.school,
                name="Mathematics",
                code="mathematics",
            )
        )

        self.offering_one = (
            SubjectOffering.objects.create(
                school=self.school,
                academic_year=self.year,
                class_section=(
                    self.section_a
                ),
                subject=self.subject,
            )
        )

        self.offering_two = (
            SubjectOffering.objects.create(
                school=self.school,
                academic_year=self.year,
                class_section=(
                    self.section_b
                ),
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

        logged_in = (
            self.client.login(
                username=(
                    "teacher_one"
                ),
                password=(
                    "Password123!"
                ),
            )
        )

        self.assertTrue(
            logged_in
        )

        response = self.client.get(
            reverse(
                (
                    "portal:"
                    "teacher-class-detail"
                ),
                kwargs={
                    "offering_id":
                        self.offering_two.id,
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


# =====================================================================
# PARENT / GUARDIAN OBJECT ACCESS SECURITY
# =====================================================================


@override_settings(
    ALLOWED_HOSTS=[
        "testserver",
        "parent-security.testserver",
    ]
)
class ParentObjectAccessTests(
    TestCase
):

    def setUp(self):

        self.school = (
            School.objects.create(
                name=(
                    "Parent Security School"
                ),
                slug=(
                    "parent-security"
                ),
            )
        )

        SchoolDomain.objects.create(
            school=self.school,
            domain=(
                "parent-security.testserver"
            ),
            is_verified=True,
            is_primary=True,
        )

        self.parent_user = (
            User.objects.create_user(
                username=(
                    "parent_one"
                ),
                password=(
                    "Password123!"
                ),
            )
        )

        self.parent_role = (
            SchoolRole.objects.create(
                school=self.school,
                name="Parent",
                code="parent",
            )
        )

        self.membership = (
            SchoolMembership.objects.create(
                user=self.parent_user,
                school=self.school,
                is_active=True,
            )
        )

        self.membership.roles.add(
            self.parent_role
        )

        self.guardian = (
            Guardian.objects.create(
                school=self.school,
                user=self.parent_user,
                first_name="Parent",
                last_name="One",
                phone_number=(
                    "0200000001"
                ),
            )
        )

        self.own_child = (
            Student.objects.create(
                school=self.school,
                admission_number=(
                    "P-001"
                ),
                first_name="Own",
                last_name="Child",
            )
        )

        self.other_child = (
            Student.objects.create(
                school=self.school,
                admission_number=(
                    "P-002"
                ),
                first_name="Other",
                last_name="Child",
            )
        )

        StudentGuardian.objects.create(
            school=self.school,
            guardian=self.guardian,
            student=self.own_child,
            relationship=(
                StudentGuardian
                .Relationship
                .MOTHER
            ),
            is_primary_contact=True,
        )

        self.client = Client()

    def test_parent_can_open_own_child(
        self,
    ):

        logged_in = (
            self.client.login(
                username=(
                    "parent_one"
                ),
                password=(
                    "Password123!"
                ),
            )
        )

        self.assertTrue(
            logged_in
        )

        response = self.client.get(
            reverse(
                (
                    "portal:"
                    "parent-child-detail"
                ),
                kwargs={
                    "student_id":
                        self.own_child.id,
                },
            ),
            HTTP_HOST=(
                "parent-security.testserver"
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_parent_cannot_open_other_child(
        self,
    ):

        logged_in = (
            self.client.login(
                username=(
                    "parent_one"
                ),
                password=(
                    "Password123!"
                ),
            )
        )

        self.assertTrue(
            logged_in
        )

        response = self.client.get(
            reverse(
                (
                    "portal:"
                    "parent-child-detail"
                ),
                kwargs={
                    "student_id":
                        self.other_child.id,
                },
            ),
            HTTP_HOST=(
                "parent-security.testserver"
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )


# =====================================================================
# SCHOOL USER MANAGEMENT SECURITY
# =====================================================================


class SchoolUserManagementSecurityTests(
    TestCase
):

    def test_membership_lookup_is_tenant_scoped(
        self,
    ):

        school_a = (
            School.objects.create(
                name="School A Users",
                slug="school-a-users",
            )
        )

        school_b = (
            School.objects.create(
                name="School B Users",
                slug="school-b-users",
            )
        )

        user_a = User.objects.create_user(
            username=(
                "shared-test-user"
            ),
            password=(
                "Password123!"
            ),
        )

        user_b = User.objects.create_user(
            username=(
                "shared-test-user-b"
            ),
            password=(
                "Password123!"
            ),
        )

        # Ensure user_a remains deliberately separate from
        # School B's membership.
        self.assertNotEqual(
            user_a.id,
            user_b.id,
        )

        membership_b = (
            SchoolMembership.objects.create(
                school=school_b,
                user=user_b,
            )
        )

        self.assertFalse(
            SchoolMembership.objects
            .filter(
                school=school_a,
                id=membership_b.id,
            )
            .exists()
        )