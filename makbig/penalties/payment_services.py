# penalties/payment_service.py

import hmac
import hashlib
import logging
from decimal import Decimal, InvalidOperation

import razorpay
from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# ── Constants matching your model validators ──────────────────────
MIN_AMOUNT = Decimal("1.00")       # Razorpay minimum
MAX_AMOUNT = Decimal("10000.00")   # your Penalty model hard limit


# ── Single lazy client instance ───────────────────────────────────
_client = None

def get_razorpay_client():
    """
    Lazy singleton — one client instance for the entire process lifetime.
    Never creates a new HTTP client on every request.
    """
    global _client
    if _client is None:
        _client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    return _client


# ── Amount helper ─────────────────────────────────────────────────
def _to_paise(amount) -> int:
    """
    Converts rupees → paise (integer) safely.
    Uses str() to avoid float precision issues e.g. 0.1 + 0.2 != 0.3.
    Raises ValidationError if amount is invalid or out of bounds.
    """
    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"Invalid amount: {amount!r}")

    if amount < MIN_AMOUNT:
        raise ValidationError(f"Amount ₹{amount} is below minimum ₹{MIN_AMOUNT}.")

    if amount > MAX_AMOUNT:
        raise ValidationError(f"Amount ₹{amount} exceeds maximum ₹{MAX_AMOUNT}.")

    return int(amount * 100)


class PaymentService:

    @staticmethod
    def create_order(penalty):
        """
        Creates a Razorpay order for a given Penalty instance.

        Uses penalty.id as the receipt for unique idempotency tracking.
        Embeds penalty_id and student_id in notes for traceability.

        Returns:
            dict — Razorpay order object with 'id', 'amount', etc.

        Raises:
            ValidationError — amount out of bounds
            Exception       — Razorpay API failure (logged before re-raise)
        """
        paise = _to_paise(penalty.amount)

        payload = {
            "amount":          paise,
            "currency":        "INR",
            "payment_capture": 1,                    # auto-capture immediately
            "receipt":         f"penalty_{penalty.id}",  # unique per penalty
            "notes": {
                "penalty_id": str(penalty.id),
                "student_id": str(penalty.student.id),
                "student":    penalty.student.user.email,
            }
        }

        try:
            order = get_razorpay_client().order.create(data=payload)
            logger.info(
                f"[Payment] Order created | order_id={order['id']} "
                f"penalty_id={penalty.id} amount=₹{penalty.amount}"
            )
            return order
        except Exception as e:
            logger.error(
                f"[Payment] Order creation failed | "
                f"penalty_id={penalty.id} amount=₹{penalty.amount} | error={e}"
            )
            raise

    @staticmethod
    def verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        Verifies Razorpay payment signature using raw HMAC-SHA256.

        Why manual instead of SDK's verify_payment_signature:
        — Full control, no dependency on SDK internal changes
        — Uses hmac.compare_digest for constant-time comparison
          which prevents timing side-channel attacks

        Returns:
            True  — signature valid, payment is genuine
            False — mismatch, treat as tampered or fraudulent
        """
        try:
            message  = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
            secret   = settings.RAZORPAY_KEY_SECRET.encode('utf-8')
            expected = hmac.new(secret, message, hashlib.sha256).hexdigest()

            is_valid = hmac.compare_digest(expected, razorpay_signature)

            if not is_valid:
                logger.warning(
                    f"[Payment] Signature mismatch | "
                    f"order_id={razorpay_order_id} payment_id={razorpay_payment_id}"
                )
            return is_valid

        except Exception as e:
            logger.error(f"[Payment] Signature verification error: {e}")
            return False

    @staticmethod
    def fetch_order(razorpay_order_id):
        """
        Fetches order details from Razorpay API.
        Used in callback to extract receipt (penalty_id)
        without trusting POST data from the client.
        """
        try:
            return get_razorpay_client().order.fetch(razorpay_order_id)
        except Exception as e:
            logger.error(f"[Payment] Order fetch failed | order_id={razorpay_order_id} | error={e}")
            raise