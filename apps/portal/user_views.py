from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .pagination import paginate

from apps.accounts.decorators import (
    school_permission_required,
)
from apps.schools.models import (
    SchoolMembership,
)
from apps.subscriptions.decorators import (
    subscription_write_required,
)

from .user_forms import (
    SchoolMembershipUpdateForm,
    SchoolUserCreateForm,
)
from .user_services import (
    create_school_user,
)


@school_permission_required(
    "schools.manage_school_users"
)
def school_user_list(request):
    memberships = (
        SchoolMembership.objects
        .filter(
            school=request.school
        )
        .select_related(
            "user"
        )
        .prefetch_related(
            "roles"
        )
        .order_by(
            "user__last_name",
            "user__first_name",
            "user__username",
        )
    )

    page_obj, pagination_query = paginate(
        request,
        memberships,
    )

    return render(
        request,
        "portal/users/list.html",
        {
            "memberships":
                page_obj.object_list,

            "page_obj":
                page_obj,

            "pagination_query":
                pagination_query,
        },
    )


@subscription_write_required
@school_permission_required(
    "schools.manage_school_users"
)
def school_user_create(
    request,
):
    if request.method == "POST":

        form = SchoolUserCreateForm(
            request.POST,
            school=request.school,
        )

        if form.is_valid():

            try:

                membership = (
                    create_school_user(
                        school=request.school,

                        data=(
                            form.cleaned_data
                        ),

                        created_by=(
                            request.user
                        ),
                    )
                )

            except ValidationError as exc:

                form.add_error(
                    None,
                    exc.messages,
                )

            else:

                messages.success(
                    request,
                    (
                        f"Account "
                        f"{membership.user.username} "
                        "created successfully."
                    ),
                )

                return redirect(
                    "portal:school-user-list"
                )

    else:

        form = SchoolUserCreateForm(
            school=request.school
        )

    return render(
        request,
        "portal/form.html",
        {
            "title":
                "Create User Account",

            "form":
                form,

            "submit_label":
                "Create Account",
        },
    )


@subscription_write_required
@school_permission_required(
    "schools.manage_school_users"
)
def school_user_edit(
    request,
    membership_id,
):
    membership = get_object_or_404(
        SchoolMembership.objects
        .filter(
            school=request.school
        )
        .prefetch_related(
            "roles"
        ),
        id=membership_id,
    )

    if (
        membership.user_id
        == request.user.id
        and request.method == "POST"
        and not request.POST.get(
            "is_active"
        )
    ):

        messages.error(
            request,
            (
                "You cannot deactivate your "
                "own school access."
            ),
        )

        return redirect(
            "portal:school-user-list"
        )

    if request.method == "POST":

        form = (
            SchoolMembershipUpdateForm(
                request.POST,
                school=request.school,
            )
        )

        if form.is_valid():

            membership.is_active = (
                form.cleaned_data[
                    "is_active"
                ]
            )

            membership.save(
                update_fields=[
                    "is_active",
                    "updated_at",
                ]
            )

            membership.roles.set(
                form.cleaned_data[
                    "roles"
                ]
            )

            messages.success(
                request,
                "User access updated.",
            )

            return redirect(
                "portal:school-user-list"
            )

    else:

        form = (
            SchoolMembershipUpdateForm(
                school=request.school,

                initial={
                    "roles":
                        membership.roles.all(),

                    "is_active":
                        membership.is_active,
                },
            )
        )

    return render(
        request,
        "portal/form.html",
        {
            "title": (
                f"Manage Access: "
                f"{membership.user}"
            ),

            "form":
                form,

            "submit_label":
                "Save Access",
        },
    )