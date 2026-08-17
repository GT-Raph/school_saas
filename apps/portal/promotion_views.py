from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .pagination import paginate

from apps.accounts.decorators import (
    school_permission_required,
)
from apps.academics.models import Enrollment
from apps.promotions.models import (
    PromotionDecision,
    PromotionEvaluation,
    PromotionPolicy,
)
from apps.promotions.services import (
    approve_promotion_decision,
    evaluate_student_promotion,
    execute_promotion_decision,
)
from apps.subscriptions.decorators import (
    subscription_write_required,
)

from .promotion_forms import (
    PromotionDecisionForm,
    PromotionExecutionForm,
)


@school_permission_required(
    "promotions.view_promotionevaluation"
)
def promotion_dashboard(
    request,
):
    policies = (
        PromotionPolicy.objects
        .for_school(
            request.school
        )
        .filter(
            is_active=True
        )
        .select_related(
            "academic_year",
            "class_level",
        )
        .order_by(
            "-academic_year__starts_on",
            "class_level__order",
        )
    )

    page_obj, pagination_query = paginate(
        request,
        policies,
    )

    policies = page_obj.object_list

    return render(
        request,
        (
            "portal/promotions/"
            "dashboard.html"
        ),
        {
            "policies": policies,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
        },
    )


@subscription_write_required
@school_permission_required(
    "promotions.run_promotion_evaluation"
)
def promotion_run_policy(
    request,
    policy_id,
):
    if request.method != "POST":

        raise ValidationError(
            "POST request required."
        )

    policy = get_object_or_404(
        PromotionPolicy.objects
        .for_school(
            request.school
        ),
        id=policy_id,
        is_active=True,
    )

    enrollments = (
        Enrollment.objects
        .for_school(
            request.school
        )
        .filter(
            academic_year=(
                policy.academic_year
            ),
            class_section__level=(
                policy.class_level
            ),
            status=(
                Enrollment.Status.ACTIVE
            ),
        )
        .select_related(
            "student",
            "class_section",
        )
    )

    completed = 0

    with transaction.atomic():

        for enrollment in enrollments:

            evaluate_student_promotion(
                policy=policy,
                enrollment=enrollment,
            )

            completed += 1

    messages.success(
        request,
        (
            f"{completed} students "
            "evaluated."
        ),
    )

    return redirect(
        "portal:promotion-policy-results",
        policy_id=policy.id,
    )


@school_permission_required(
    "promotions.view_promotionevaluation"
)
def promotion_policy_results(
    request,
    policy_id,
):
    policy = get_object_or_404(
        PromotionPolicy.objects
        .for_school(
            request.school
        ),
        id=policy_id,
    )

    evaluations = (
        PromotionEvaluation.objects
        .for_school(
            request.school
        )
        .filter(
            policy=policy
        )
        .select_related(
            "enrollment__student",
            "enrollment__class_section",
        )
        .order_by(
            "enrollment__student__last_name",
            "enrollment__student__first_name",
        )
    )

    page_obj, pagination_query = paginate(
        request,
        evaluations,
    )

    evaluations = page_obj.object_list

    return render(
        request,
        (
            "portal/promotions/"
            "policy_results.html"
        ),
        {
            "policy": policy,
            "evaluations": evaluations,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
        },
    )


@subscription_write_required
@school_permission_required(
    "promotions.approve_promotion_decision"
)
def promotion_decide(
    request,
    evaluation_id,
):
    evaluation = get_object_or_404(
        PromotionEvaluation.objects
        .for_school(
            request.school
        ),
        id=evaluation_id,
    )

    if request.method == "POST":

        form = PromotionDecisionForm(
            request.POST,
            school=request.school,
        )

        if form.is_valid():

            try:

                approve_promotion_decision(
                    evaluation=evaluation,

                    final_decision=(
                        form.cleaned_data[
                            "final_decision"
                        ]
                    ),

                    approved_by=(
                        request.user
                    ),

                    target_class_section=(
                        form.cleaned_data[
                            "target_class_section"
                        ]
                    ),

                    reason=(
                        form.cleaned_data[
                            "reason"
                        ]
                    ),
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
                        "Promotion decision "
                        "approved."
                    ),
                )

                return redirect(
                    "portal:"
                    "promotion-policy-results",

                    policy_id=(
                        evaluation.policy_id
                    ),
                )

    else:

        form = PromotionDecisionForm(
            school=request.school,

            initial={
                "final_decision":
                    evaluation.recommendation,
            },
        )

    return render(
        request,
        (
            "portal/promotions/"
            "decision.html"
        ),
        {
            "evaluation":
                evaluation,

            "form":
                form,
        },
    )


@subscription_write_required
@school_permission_required(
    "promotions.execute_promotion_decision"
)
def promotion_execute(
    request,
    decision_id,
):
    decision = get_object_or_404(
        PromotionDecision.objects
        .for_school(
            request.school
        ),
        id=decision_id,
    )

    if request.method == "POST":

        form = PromotionExecutionForm(
            request.POST,
            school=request.school,
        )

        if form.is_valid():

            try:

                execute_promotion_decision(
                    decision=decision,

                    next_academic_year=(
                        form.cleaned_data[
                            "next_academic_year"
                        ]
                    ),

                    enrolled_on=(
                        form.cleaned_data[
                            "enrolled_on"
                        ]
                    ),

                    executed_by=(
                        request.user
                    ),
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
                        "Promotion decision "
                        "executed successfully."
                    ),
                )

                return redirect(
                    "portal:"
                    "promotion-policy-results",

                    policy_id=(
                        decision
                        .evaluation
                        .policy_id
                    ),
                )

    else:

        form = PromotionExecutionForm(
            school=request.school
        )

    return render(
        request,
        "portal/form.html",
        {
            "title":
                "Execute Promotion Decision",

            "form":
                form,

            "submit_label":
                "Execute Decision",
        },
    )