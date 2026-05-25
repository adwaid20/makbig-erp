# Create your views here.
# here is the penalties app
# now here i want the penalties or fine of each app(attendance, review or late) to be called separately and then add them to total and pay fine option at each leave if the student wants he can pay only review fine now or only attendace fine now as payment is done the money or fine will be reduced and also keep a colomn at the bottom so that the student can raise a ticket and make any clarrfication related to the fine 


from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required, user_passes_test

from adminpanel.models import StudentProfile, Course
from .models import Penalty
from .forms import PenaltyUpdateForm


import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from .payment_services import PaymentService


from django.core.cache import cache
from adminpanel.services import DASHBOARD_CACHE_KEY
from core.cache_utils import SafeCache



logger = logging.getLogger(__name__)


def is_staff_user(user):
    return user.is_staff


# ----------------------------------------
# 1️⃣ Dashboard - Course filter + students
# ----------------------------------------

@login_required
@user_passes_test(is_staff_user)
def penalty_dashboard(request):

    courses = Course.objects.all()
    selected_course = request.GET.get('course')

    students = StudentProfile.objects.all()

    if selected_course:
        students = students.filter(course_id=selected_course)

    students = students.annotate(
        total_unpaid=Sum(
            'penalties__amount',
            filter=Q(penalties__is_paid=False)
        )
    )

    context = {
        'courses': courses,
        'students': students,
        'selected_course': selected_course
    }

    return render(request, 'penalties/fines.html', context)


# ----------------------------------------
# 2️⃣ Student Detail Page
# ----------------------------------------

@login_required
@user_passes_test(is_staff_user)
def student_penalty_detail(request, student_id):

    student = get_object_or_404(StudentProfile, id=student_id)

    unpaid_penalties = student.penalties.filter(is_paid=False).order_by('-created_at')
    paid_penalties = student.penalties.filter(is_paid=True).order_by('-created_at')

    total_unpaid = unpaid_penalties.aggregate(
        total=Sum('amount')
    )['total'] or 0

    context = {
        'student': student,
        'unpaid_penalties': unpaid_penalties,
        'paid_penalties': paid_penalties,
        'total_unpaid': total_unpaid
    }

    return render(request, 'penalties/student_detail.html', context)


# ----------------------------------------
# 3️⃣ Edit Penalty Amount
# ----------------------------------------

@login_required
@user_passes_test(is_staff_user)
def edit_penalty(request, penalty_id):

    penalty = get_object_or_404(Penalty, id=penalty_id)

    if request.method == 'POST':
        form = PenaltyUpdateForm(request.POST, instance=penalty)
        if form.is_valid():
            form.save()

            SafeCache.delete(DASHBOARD_CACHE_KEY)

            return redirect('student_detail', student_id=penalty.student.id)
    else:
        form = PenaltyUpdateForm(instance=penalty)

    return render(request, 'penalties/edit_penalty.html', {
        'form': form,
        'penalty': penalty
    })


# ----------------------------------------
# 4️⃣ Mark Penalty as Paid
# ----------------------------------------

@login_required
@user_passes_test(is_staff_user)
def mark_penalty_paid(request, penalty_id):
    penalty = get_object_or_404(Penalty, id=penalty_id)
    penalty.is_paid = True
    penalty.paid_via = 'manual'    # ← mark as manually paid
    penalty.save()
    cache.delete(DASHBOARD_CACHE_KEY)
    return redirect('student_detail', student_id=penalty.student.id)


@login_required
@user_passes_test(is_staff_user)
def mark_penalty_unpaid(request, penalty_id):
    penalty = get_object_or_404(Penalty, id=penalty_id)

    # Block reversal of online payments — cannot undo
    if penalty.paid_via == 'online':
        messages.error(request, "Online payments cannot be reversed.")
        return redirect('student_detail', student_id=penalty.student.id)

    # Only manual payments can be reversed
    if penalty.paid_via != 'manual':
        messages.error(request, "This penalty has not been manually marked as paid.")
        return redirect('student_detail', student_id=penalty.student.id)

    penalty.is_paid = False
    penalty.paid_via = None        # ← clear the payment method
    penalty.save()
    cache.delete(DASHBOARD_CACHE_KEY)
    messages.success(request, "Penalty marked as unpaid.")
    return redirect('student_detail', student_id=penalty.student.id)




# penalties/views.py — ADD AT THE BOTTOM


# ----------------------------------------
# 6️⃣  Initiate Payment — student hits "Pay Now"
# ----------------------------------------

@login_required
@require_GET
def initiate_payment(request, penalty_id):
    """
    Student-facing view. Creates a Razorpay order and renders checkout.

    Security:
    - student__user=request.user  → student can only pay their own penalties
    - is_paid=False               → cannot re-pay an already paid penalty
    """
    # Guard: only students access this
    if not request.user.is_student:
        messages.error(request, "Access denied.")
        return redirect('home')

    penalty = get_object_or_404(
        Penalty,
        id=penalty_id,
        student__user=request.user,   # owns this penalty
        is_paid=False,                # not already paid
    )

    try:
        order = PaymentService.create_order(penalty)
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('student_review')
    except Exception as e:
        logger.error("initiate_payment unexpected error for penalty_id=%s: %s", penalty_id, e, exc_info=True)
        messages.error(request, "Could not initiate payment. Please try again later.")
        return redirect('student_review')

    return render(request, 'penalties/pay.html', {
        'penalty':      penalty,
        'order':        order,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
    })


# ----------------------------------------
# 7️⃣  Payment Callback — Razorpay POSTs here after payment
# ----------------------------------------

@csrf_exempt       # Razorpay's POST has no Django CSRF token — must exempt
@require_POST
def payment_callback(request):
    """
    Called by Razorpay after payment attempt (success OR failure).

    Security flow:
    ① Extract the three Razorpay POST fields
    ② Verify HMAC-SHA256 signature — reject immediately if invalid
    ③ Fetch order from Razorpay API to get penalty_id from receipt
       (never trust penalty_id from POST data — client can tamper it)
    ④ transaction.atomic() + select_for_update():
       - atomic: all-or-nothing, no partial state on DB failure
       - select_for_update: row-level lock prevents race condition
         if Razorpay fires duplicate webhooks simultaneously
    ⑤ is_paid=False filter: idempotency guard —
       duplicate callbacks never double-mark
    """

    # ── ① Extract fields ─────────────────────────────────────────
    razorpay_order_id   = request.POST.get('razorpay_order_id',   '').strip()
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '').strip()
    razorpay_signature  = request.POST.get('razorpay_signature',  '').strip()

    # If any field missing → payment failed or request tampered
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        logger.warning(
            f"[Payment] Incomplete callback fields | "
            f"order={razorpay_order_id} payment={razorpay_payment_id}"
        )
        messages.error(request, "Payment failed. Please try again.")
        return redirect('student_dashboard')

    # ── ② Verify signature ────────────────────────────────────────
    is_valid = PaymentService.verify_signature(
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
    )

    if not is_valid:
        messages.error(request, "Payment verification failed. Please contact support.")
        return redirect('student_dashboard')

    # ── ③ Fetch order from Razorpay to get penalty_id ─────────────
    # receipt format is "penalty_{id}" — set in create_order
    try:
        order      = PaymentService.fetch_order(razorpay_order_id)
        receipt    = order.get('receipt', '')
        penalty_id = int(receipt.replace('penalty_', ''))
    except Exception as e:
        logger.error(f"[Payment] Could not extract penalty_id from order | error={e}")
        messages.error(request, "Payment received but could not process. Contact support.")
        return redirect('student_dashboard')

    # ── ④ Mark penalty as paid — atomic + row lock ────────────────
    try:
        with transaction.atomic():
            penalty = Penalty.objects.select_for_update().get(
                id=penalty_id,
                is_paid=False,   # idempotency — skip if already paid
            )
            penalty.is_paid             = True
            penalty.paid_via            = 'online'          # permanent — cannot be reversed
            penalty.razorpay_order_id   = razorpay_order_id
            penalty.razorpay_payment_id = razorpay_payment_id
            penalty.razorpay_signature  = razorpay_signature

            # Only write the fields we changed — not the whole row
            penalty.save(update_fields=[
                'is_paid',
                'paid_via',
                'razorpay_order_id',
                'razorpay_payment_id',
                'razorpay_signature',
            ])

        cache.delete(DASHBOARD_CACHE_KEY)

        logger.info(
            f"[Payment] Success | penalty_id={penalty_id} "
            f"payment_id={razorpay_payment_id} order_id={razorpay_order_id}"
        )
        messages.success(request, "Payment successful! Your fine has been cleared.")

    except Penalty.DoesNotExist:
        # Already paid — duplicate webhook, idempotent — just show success
        logger.info(
            f"[Payment] Duplicate callback for already-paid penalty_id={penalty_id}"
        )
        messages.info(request, "This penalty is already marked as paid.")

    except Exception as e:
        logger.error(
            f"[Payment] Error marking paid | penalty_id={penalty_id} | error={e}"
        )
        messages.error(
            request,
            "Payment was received but we could not update your record. "
            "Please contact support with your payment ID: "
            f"{razorpay_payment_id}"
        )

    return redirect('student_review')