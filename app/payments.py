import base64
import json
import urllib.error
import urllib.request

from django.conf import settings


class RazorpayError(Exception):
    pass


def razorpay_request(method, path, payload=None):
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET
    if not key_id or not key_secret:
        raise RazorpayError(
            "Online payments are not configured yet. Please contact the hotel."
        )

    credentials = base64.b64encode(
        f"{key_id}:{key_secret}".encode("utf-8")
    ).decode("ascii")
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"https://api.razorpay.com/v1/{path.lstrip('/')}",
        data=body,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RazorpayError(
            "Razorpay could not process the request. Please try again."
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RazorpayError(
            "Could not reach Razorpay. Please try again in a moment."
        ) from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RazorpayError(
            "Razorpay returned an invalid response. Please try again."
        ) from exc

    if not isinstance(result, dict):
        raise RazorpayError("Razorpay returned an invalid response.")
    return result


def create_razorpay_order(amount_paise, receipt, booking_id):
    return razorpay_request(
        "POST",
        "/orders",
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": {"booking_id": str(booking_id)},
        },
    )


def fetch_razorpay_payment(payment_id):
    return razorpay_request("GET", f"/payments/{payment_id}")


def refund_razorpay_payment(payment_id, amount_paise):
    return razorpay_request(
        "POST",
        f"/payments/{payment_id}/refund",
        {"amount": amount_paise},
    )
