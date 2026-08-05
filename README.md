# School Management SaaS

A multi-tenant school management platform built with Django, PostgreSQL, Supabase, and Render.

The system is designed for schools to manage students, guardians, staff, academics, attendance, assessments, results, promotions, fees, payments, subscriptions, and role-specific portals from one shared SaaS platform.

> **Project status:** Active development. The platform is suitable for development, staging, demonstrations, and controlled pilot testing. It is not yet approved for unrestricted production use with real schools.

---

## 1. Project goals

The platform is being built to provide schools with:

- A secure school-specific portal
- Student admissions and enrollment history
- Guardian and staff management
- Academic year, term, class, subject, and teacher assignment management
- Attendance recording
- Assessment and result processing
- Report cards
- Promotion, repetition, graduation, and review workflows
- Fee structures, invoices, payments, receipts, adjustments, and financial statements
- Parent, student, teacher, finance, academic administrator, and school administrator portals
- Subscription plans and student-capacity limits
- Tenant-level roles and permissions
- Audit trails for sensitive operations
- Controlled school branding and configuration

The codebase uses one shared application and one shared PostgreSQL schema. Every tenant-owned record is linked to a school.

---

## 2. Technology stack

| Area | Technology |
|---|---|
| Backend | Django 5.2.16 LTS |
| Language | Python 3.10.9 |
| Database | PostgreSQL through Supabase |
| Local fallback | SQLite, development only |
| Static files | WhiteNoise |
| Production server | Gunicorn |
| Deployment | Render |
| File storage | Supabase Storage, planned/in progress |
| Payments | Paystack, subscription-renewal integration planned/in progress |
| Frontend | Django templates, HTML, CSS, and JavaScript |
| UI direction | Responsive dashboard with tenant branding and role-aware navigation |

Do not upgrade Django or Python casually. Dependency changes must be tested and reviewed before merging.

---

## 3. Current application modules

The project is organized into Django apps under `apps/`.

```text
apps/
├── accounts/         Custom user model, login, password controls
├── academics/        Academic years, terms, classes, subjects, enrollments
├── assessments/      Schemes, categories, assessments, scores, subject results
├── attendance/       Attendance sessions and records
├── audit/            Audit events
├── core/             Shared models, middleware, health checks, utilities
├── finance/          Fees, invoices, payments, receipts, ledger, reversals
├── guardians/        Guardians and student-guardian relationships
├── portal/           Role-specific dashboards and operational pages
├── promotions/       Promotion policies, evaluations, decisions, execution
├── reports/          Term results and report cards
├── schools/          Tenants, domains, memberships, roles, branding
├── staff/            Staff and teacher profiles
├── students/         Students, admissions, and staged bulk imports
└── subscriptions/    Plans, school subscriptions, limits, write access
```

The repository and migrations are the source of truth. This README describes the intended architecture, but collaborators must confirm model names and service signatures in the current branch before changing code.

---

## 4. User roles

The platform currently supports these main school-level roles:

| Role | Main access |
|---|---|
| Platform Administrator | Cross-platform technical administration |
| School Administrator | Students, guardians, staff, users, settings, oversight |
| Academic Administrator | Results approval, report cards, promotions |
| Teacher | Assigned classes, attendance, assessments, marks, submitted results |
| Finance Officer | Invoices, payments, receipts, accounts, debtors |
| Parent / Guardian | Linked children only |
| Student | Own records only |

A user may belong to more than one school and may have different roles in each school.

Never treat `is_staff` as permission to access school data. Use the active school membership, assigned school roles, permissions, and object-level checks.

---

## 5. Multi-tenant architecture

This is a shared-schema multi-tenant application.

Each tenant-owned model must include a school reference, normally through the shared `SchoolOwnedModel` abstraction.

```text
User request
    ↓
TenantMiddleware resolves the school
    ↓
Active SchoolMembership is loaded
    ↓
School roles and permissions are checked
    ↓
Queries are filtered by school
    ↓
Object-level ownership is verified
```

### Mandatory tenant rules

1. Never use an unrestricted queryset for tenant-owned data in a portal view.
2. Use `.for_school(request.school)` or an equally explicit school filter.
3. A UUID in a URL is not authorization.
4. Teachers may access only actively assigned offerings.
5. Parents may access only linked children.
6. Students may access only their own profile and records.
7. Finance, report, and promotion operations must confirm that all related records belong to the same school.
8. Cross-school relationships must be rejected in model validation and service logic.
9. Run the tenant-integrity command before staging or production deployment.

```powershell
py manage.py check_tenant_integrity
```

---

## 6. Service-layer rule

Critical writes must go through service functions rather than direct model creation in views, templates, or Django Admin.

Examples include:

- Student admission
- Enrollment creation
- Guardian linking
- Attendance submission and locking
- Score entry
- Result calculation, submission, and approval
- Promotion decisions and execution
- Invoice generation and issuing
- Payment recording
- Receipt generation
- Financial adjustments and reversals
- Subscription-limit enforcement

Avoid this for sensitive workflows:

```python
Payment.objects.create(...)
```

Use the relevant service instead:

```python
record_payment(...)
```

The service layer is responsible for validation, transactions, related records, audit events, subscription checks, and tenant consistency.

---

## 7. Finance integrity rules

Finance is ledger-driven. A financial record must not be created in isolation.

```text
Invoice
    ↓
Ledger debit

Payment
    ↓
Payment allocation
    ↓
Ledger credit
    ↓
Invoice balance update
    ↓
Receipt
```

Transactional finance models are primarily read/review records in Django Admin. Creation should happen through controlled service-layer workflows.

Do not permanently delete financial transactions. Use reversal or void workflows with reasons, actors, timestamps, and audit records.

---

## 8. Academic and result integrity rules

- Students are created once.
- Annual class placement is represented through `Enrollment`.
- Historical enrollments must not be overwritten.
- Submitted, approved, or published results must not be silently recalculated.
- Published report cards must be based on stored snapshots, not live mutable score rows.
- Teachers submit results; authorized academic administrators approve or publish them.
- Promotion recommendations must remain explainable and require human approval.
- Promotion execution creates the next academic-year enrollment and preserves the previous history.

---

## 9. V1 scope

### Included

- Tenant and school management
- Authentication and school memberships
- Tenant roles and permissions
- Students, guardians, and staff
- Admissions and bulk student import
- Academic structure
- Teacher assignments
- Attendance
- Assessments and marks
- Results and report cards
- Promotion, repetition, review, and graduation workflows
- Fee structures and invoicing
- Payments, receipts, statements, debtors, and reversals
- Subscription plans and student limits
- School administration studio
- Role-specific portals
- Tenant branding
- Audit foundation

### Not part of V1

- Payroll
- Library management
- Transport management
- Hostel management
- Inventory management
- Biometrics
- Native mobile apps
- Unrestricted custom Python, SQL, or JavaScript supplied by schools

Do not add out-of-scope modules without product approval.

---

## 10. Local development setup

### Prerequisites

- Python 3.10.9
- Git
- PostgreSQL or a Supabase project
- Windows PowerShell commands are shown below

### Clone the repository

```powershell
git clone <repository-url>
cd school_saas
```

### Create and activate the virtual environment

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
py -m pip install --upgrade pip
pip install -r requirements.txt
```

### Create the environment file

Copy `.env.example` to `.env`.

```powershell
Copy-Item .env.example .env
```

Example local values:

```env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=replace-with-a-long-random-development-key
ALLOWED_HOSTS=127.0.0.1,localhost,.localhost,testserver
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
DEV_TENANT_SLUG=demo-international-school
DEFAULT_TENANT_SLUG=demo-international-school
DATABASE_URL=your-supabase-session-pooler-url
LOG_LEVEL=INFO
```

Never commit `.env`, database passwords, Paystack keys, Supabase service keys, or user credentials.

### Apply migrations

```powershell
py manage.py migrate
```

### Create a platform administrator

```powershell
py manage.py createsuperuser
```

### Configure default roles for a school

```powershell
py manage.py setup_school_roles --school demo-international-school
```

### Run the development server

```powershell
py manage.py runserver
```

Useful local URLs:

```text
http://127.0.0.1:8000/login/
http://127.0.0.1:8000/portal/
http://127.0.0.1:8000/admin/
http://127.0.0.1:8000/health/live/
http://127.0.0.1:8000/health/ready/
```

---

## 11. Required checks before committing

Run all applicable checks before opening a pull request.

```powershell
py manage.py check
py manage.py makemigrations --check --dry-run
py manage.py test
py manage.py check_tenant_integrity
py manage.py collectstatic --no-input
```

For production readiness:

```powershell
py manage.py check --deploy
```

Do not merge code when tests or tenant-integrity checks fail.

---

## 12. Database migrations

Create migrations only when models change.

```powershell
py manage.py makemigrations
py manage.py migrate
```

Migration rules:

- Review every generated migration.
- Do not edit an already deployed migration unless the team explicitly agrees.
- Add a new migration to correct deployed database history.
- Data migrations must be reversible where practical.
- Large data migrations must be tested against a staging copy.
- Never delete production data to make a migration pass.

---

## 13. Frontend structure

The portal uses reusable Django templates and static assets.

```text
templates/
├── accounts/
└── portal/
    ├── academic/
    ├── admin_studio/
    ├── family/
    ├── finance/
    ├── guardians/
    ├── promotions/
    ├── staff/
    ├── students/
    ├── teacher/
    ├── users/
    ├── base.html
    └── form.html

static/
└── portal/
    ├── css/portal.css
    └── js/portal.js
```

### UI principles

- Keep the interface clean, responsive, and consistent.
- Use the shared layout and existing components before introducing new patterns.
- Navigation must be permission-aware.
- Do not expose a link merely because the backend will return `403`; hide unavailable modules as well.
- Avoid inline CSS for new pages unless it is genuinely page-specific.
- School branding must use controlled values, not arbitrary code.
- Student and financial records should not show destructive delete actions.

---

## 14. Coding standards

### Python

- Follow PEP 8.
- Prefer clear service functions over large views.
- Use type hints for reusable utilities and service boundaries where practical.
- Use `transaction.atomic()` for multi-record writes.
- Call `full_clean()` in controlled service workflows before saving models where cross-field validation matters.
- Use Django enums instead of repeated string literals.
- Avoid hidden side effects in model `save()` methods.
- Keep tenant filters explicit.

### Django views

- Use the correct permission decorator.
- Derive the school from `request.school`, never from user-submitted form data.
- Use `get_object_or_404()` with a tenant-filtered queryset.
- Validate object-level access after general permission checks.
- Never trust hidden form IDs without comparing them to the authorized queryset.

### Templates

- Keep business logic out of templates.
- Use named URLs.
- Use CSRF tokens on all POST forms.
- Use POST for state-changing actions.
- Do not expose unpublished or unapproved records to parents or students.

### Tests

Every sensitive feature should include tests for:

- Expected successful behavior
- Permission denial
- Cross-tenant denial
- Object-level denial
- Invalid state transitions
- Transaction rollback
- Subscription read-only behavior
- Historical-record immutability

---

## 15. Git workflow

Recommended branch naming:

```text
feature/student-import
feature/paystack-renewals
fix/tenant-result-access
fix/payment-reversal-ledger
ui/finance-dashboard
hardening/production-settings
```

Recommended workflow:

```powershell
git checkout main
git pull
git checkout -b feature/short-description
```

After making changes:

```powershell
py manage.py check
py manage.py test
git status
git add .
git commit -m "Add concise description of the change"
git push -u origin feature/short-description
```

Pull requests should explain:

1. What changed
2. Why it changed
3. Affected apps and models
4. Migrations added
5. Security or tenant-isolation impact
6. Tests added or updated
7. Manual verification performed
8. Screenshots for UI changes

Do not commit directly to the protected production branch.

---

## 16. Environment and deployment

### Recommended environment separation

```text
Local development
    ↓
Staging Render service + staging Supabase project
    ↓
Production Render paid service + production Supabase project
```

Do not use the same database for development, staging, and production.

### Render

The Django backend is designed for Render, not Vercel serverless functions.

Typical commands:

```text
Build: ./build.sh
Start: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
Health check: /health/ready/
```

Render Free is for development, demonstrations, and controlled testing. A live school should use a paid service because free instances sleep and do not provide production-grade availability.

### Supabase

- PostgreSQL is the primary database.
- Render application traffic should normally use the Supavisor session-mode pooler.
- Direct database URLs should be used only where required for administration and backups.
- Supabase Storage will hold uploaded assets when implemented.
- Database backups do not automatically back up Storage objects.

---

## 17. Backup and restore

Database backup scripts are expected under:

```text
scripts/backup_supabase.ps1
scripts/restore_supabase.ps1
```

A backup is not considered reliable until it has been restored successfully into a disposable test database and the application has been verified against that restored data.

Never test restoration directly against the production database.

---

## 18. Security expectations

Do not:

- Commit secrets
- Log passwords, tokens, card details, or complete sensitive documents
- Build SQL strings using user input
- Disable CSRF protection for convenience
- Bypass tenant filters
- Use GET requests for state-changing actions
- Allow schools to upload and execute code
- Store uploaded files permanently on Render's ephemeral filesystem
- Expose unpublished results or reports
- Permanently delete financial audit history

Report suspected tenant leakage, payment inconsistencies, unauthorized access, or data loss immediately. Security fixes take priority over feature work.

---

## 19. Current priorities

The current phase is V1 hardening and pilot readiness.

Priority work includes:

1. Complete the responsive UI conversion across all portal pages
2. Expand tenant-isolation and object-access tests
3. Finish Paystack subscription renewal integration
4. Add Supabase Storage for logos, student photos, and documents
5. Generate branded PDF report cards and receipts
6. Add secure password-reset email workflows
7. Expand audit coverage for sensitive operations
8. Add database indexes and remove N+1 queries
9. Verify backup and restore procedures
10. Complete staging deployment and end-to-end testing
11. Create pilot-school onboarding and support procedures

Avoid adding major unrelated modules until these items are stable.

---

## 20. Definition of done

A task is complete only when:

- The behavior matches the approved requirement
- Tenant ownership is enforced
- Permissions and object-level access are enforced
- Subscription write restrictions are respected
- Financial or academic state transitions are valid
- Critical writes use transactions
- Audit events are created where required
- Tests pass
- No unreviewed migration is present
- UI changes are responsive
- Documentation is updated
- The pull request has been reviewed

---

## 21. Collaborator onboarding checklist

Before starting work:

- Read this README fully
- Review `config/settings.py`
- Review `apps/core/models.py`
- Review `apps/schools/models.py`
- Review tenant middleware and permission helpers
- Review service modules for the app being changed
- Run the test suite
- Log into the relevant role portal locally
- Confirm the issue or feature in the current branch
- Create a dedicated Git branch

Before requesting review:

- Run checks and tests
- Test with at least two different schools where tenant data is involved
- Test an unauthorized role
- Test direct URL manipulation
- Include screenshots for frontend changes
- Document environment-variable or migration changes

---

## 22. Project ownership and product decisions

This project is proprietary. Source code, designs, business logic, documentation, and product concepts must not be copied, redistributed, or reused outside the authorized collaboration arrangement.

Major changes to architecture, pricing, plan limits, financial logic, result workflows, promotion rules, or V1 scope require approval from the project owner before implementation.

---

## 23. Questions and issue reporting

Use repository issues or the agreed team communication channel. Include:

- A clear title
- Environment: local, staging, or production
- User role
- School/tenant used for testing
- Exact steps to reproduce
- Expected behavior
- Actual behavior
- Error traceback or request ID
- Screenshots where relevant
- Whether financial, academic, or personal data may be affected

Never paste secrets or real student data into public issues.
