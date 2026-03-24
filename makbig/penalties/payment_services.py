import razorpay
from django.conf import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class PaymentService:

    @staticmethod
    def create_order(amount):
        """
        Creates Razorpay order
        amount → in rupees
        """

        data = {
            "amount": int(amount * 100),  # Razorpay uses paise
            "currency": "INR",
            "payment_capture": 1
        }

        order = client.order.create(data=data)
        return order

    @staticmethod
    def verify_payment(data):
        """
        Verifies payment signature (SECURITY)
        """

        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })

        return True