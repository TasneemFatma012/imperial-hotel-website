from datetime import timedelta
import hmac
from decimal import Decimal

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from .models import Contact1 
from .models import reservation3 
from .models import reservation2 

from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.templatetags.static import static
from .forms import (
    AccountLoginForm,
    AccountSignUpForm,
    BookingForm,
    ContactForm,
)
from .payments import (
    RazorpayError,
    create_razorpay_order,
    fetch_razorpay_payment,
    refund_razorpay_payment,
)

ROOM_TYPES = {
    "Standard": "Standard Room",
    "Deluxe": "Deluxe Room",
    "Imperial": "Imperial Room",
}

ROOM_RATES = {
    "Standard": 2500,
    "Deluxe": 2500,
    "Imperial": 2500,
}

PENDING_BOOKING_HOLD = timedelta(minutes=15)


def _has_conflicting_booking(room, arrival_date, checkout_date, exclude_id=None):
    active_pending_since = timezone.now() - PENDING_BOOKING_HOLD
    reservations = (
        reservation2.objects.filter(room=room, date__lt=checkout_date)
        .filter(
            Q(checkout_date__gt=arrival_date)
            | Q(checkout_date__isnull=True, date__gte=arrival_date)
        )
        .filter(
            Q(status=reservation2.Status.CONFIRMED)
            | Q(
                status=reservation2.Status.PENDING,
                created_at__gte=active_pending_since,
            )
        )
    )
    if exclude_id is not None:
        reservations = reservations.exclude(pk=exclude_id)
    return reservations.exists()


ROOM_DETAILS = {
    "Standard": {
        "key": "Standard",
        "name": "Standard Room",
        "eyebrow": "Comfort, thoughtfully considered",
        "capacity": "Sleeps 1",
        "description": (
            "A restful room with a comfortable single bed, an en-suite bathroom, "
            "free Wi-Fi, TV with Chromecast, radio, telephone, and tea and coffee "
            "making facilities."
        ),
        "images": (
            ("images/room-2.jpg", "Comfortable standard room"),
            ("images/room-5.jpg", "Standard room interior"),
            ("images/room-6.jpg", "Standard room furnishings"),
        ),
    },
    "Deluxe": {
        "key": "Deluxe",
        "name": "Deluxe Room",
        "eyebrow": "A little more room to unwind",
        "capacity": "Sleeps 1-2",
        "description": (
            "Settle into a refined room with a comfortable single bed, an en-suite "
            "bathroom, free Wi-Fi, TV with Chromecast, radio, telephone, and tea "
            "and coffee making facilities."
        ),
        "images": (
            ("images/24.jpg", "Deluxe room"),
            ("images/bath.png", "Deluxe room bathroom"),
            ("images/bath1.jpg", "Deluxe bathroom details"),
        ),
    },
    "Imperial": {
        "key": "Imperial",
        "name": "Imperial Room",
        "eyebrow": "The signature Imperial experience",
        "capacity": "Sleeps 1-2",
        "description": (
            "Enjoy a serene signature room with a double bed, an en-suite bathroom, "
            "free Wi-Fi, TV with Chromecast, radio, telephone, and tea and coffee "
            "making facilities."
        ),
        "images": (
            ("images/30.jpg", "Imperial room"),
            ("images/email1.jpg", "Imperial room interior"),
            ("images/fac-room.jpg", "Imperial room details"),
        ),
    },
}

for room_details in ROOM_DETAILS.values():
    room_details["images"] = tuple(
        {"url": static(path), "alt": alt}
        for path, alt in room_details["images"]
    )


def _render_room_detail(request, room_key):
    return render(
        request,
        "room_detail.html",
        {"room": ROOM_DETAILS[room_key]},
    )

def index(request):
    return render(request,"index.html")
def about(request):
    return render(request,"about.html")
def contact(request):
    return render(
        request,
        "contact.html",
        {"c": Contact1.objects.all(), "form": ContactForm()},
    )


def insert1Data(request):
    if request.method != "POST":
        return redirect("contact")

    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Thanks for contacting us. We will get back to you.")
        return redirect("contact")

    return render(
        request,
        "contact.html",
        {"c": Contact1.objects.all(), "form": form},
    )


def room(request):
    return render(request, "room.html")
def handlelogin(request):
    if request.user.is_authenticated:
        return redirect("index")

    form_data = request.POST if request.method == "POST" else None
    form = AccountLoginForm(request=request, data=form_data)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Welcome back.")
        return redirect("index")

    return render(request, "login.html", {"form": form})


def handlesignup(request):
    if request.user.is_authenticated:
        return redirect("index")

    form_data = request.POST if request.method == "POST" else None
    form = AccountSignUpForm(form_data)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready. Welcome to Imperial Hotel.")
        return redirect("index")

    return render(request, "signup.html", {"form": form})


def handlelogout(request):
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("index")


def _submit_booking(request, forced_room=None):
    if request.method != "POST":
        return redirect("book")

    data = request.POST.copy()
    if forced_room is not None:
        data["room"] = forced_room

    room_choices = (
        ((forced_room, ROOM_TYPES[forced_room]),)
        if forced_room is not None
        else tuple(ROOM_TYPES.items())
    )
    form = BookingForm(data, room_choices=room_choices)
    room = forced_room or data.get("room", "")
    booking_url = reverse("book")
    if room in ROOM_TYPES:
        booking_url = f"{booking_url}?room={room}"

    if not form.is_valid():
        error_summary = " ".join(
            f"{field}: {', '.join(errors)}"
            for field, errors in form.errors.items()
        )
        messages.error(request, f"Please check the booking details. {error_summary}")
        return redirect(booking_url)

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        messages.error(
            request,
            "Online payments are not configured yet. Please contact the hotel.",
        )
        return redirect(booking_url)

    arrival_date = form.cleaned_data["date"]
    checkout_date = form.cleaned_data["checkout_date"]
    if _has_conflicting_booking(room, arrival_date, checkout_date):
        messages.error(
            request,
            "That room is not available for the selected dates. "
            "Please choose different dates.",
        )
        return redirect(booking_url)

    nights = (checkout_date - arrival_date).days
    amount_paise = ROOM_RATES[room] * nights * 100
    booking = reservation2.objects.create(
        **form.cleaned_data,
        amount_paise=amount_paise,
        status=reservation2.Status.PENDING,
    )
    try:
        order = create_razorpay_order(
            amount_paise,
            receipt=f"hotel-{booking.pk}",
            booking_id=booking.pk,
        )
        order_id = order.get("id")
        if not order_id:
            raise RazorpayError("Razorpay did not return a payment order.")
        if (
            order.get("amount") != amount_paise
            or order.get("currency") != "INR"
        ):
            raise RazorpayError("Razorpay returned an order with an unexpected amount.")
    except RazorpayError as error:
        booking.status = reservation2.Status.FAILED
        booking.save(update_fields=("status",))
        messages.error(request, str(error))
        return redirect(booking_url)

    booking.payment_order_id = order_id
    booking.save(update_fields=("payment_order_id",))
    return redirect("payment", booking_token=booking.checkout_token)


def insertData(request):
    return _submit_booking(request)


def book(request):
    selected_room = request.GET.get("room", "")
    if selected_room not in ROOM_TYPES:
        selected_room = ""

    return render(
        request,
        "book.html",
        {
            "room_types": ROOM_TYPES.items(),
            "selected_room": selected_room,
            "min_arrival_date": timezone.localdate().isoformat(),
        },
    )


def payment(request, booking_token):
    booking = get_object_or_404(reservation2, checkout_token=booking_token)
    if booking.status not in (
        reservation2.Status.PENDING,
        reservation2.Status.CONFIRMED,
    ):
        messages.error(request, "This reservation is no longer active. Please book again.")
        return redirect(f"{reverse('book')}?room={booking.room}")
    if booking.status == reservation2.Status.PENDING:
        if booking.created_at < timezone.now() - PENDING_BOOKING_HOLD:
            booking.status = reservation2.Status.FAILED
            booking.save(update_fields=("status",))
            messages.error(
                request,
                "This payment session expired. Please make a new reservation.",
            )
            return redirect(f"{reverse('book')}?room={booking.room}")
        if not booking.payment_order_id:
            messages.error(request, "The payment order is not available.")
            return redirect(f"{reverse('book')}?room={booking.room}")

    return render(
        request,
        "payment.html",
        {
            "booking": booking,
            "amount_display": f"{Decimal(booking.amount_paise) / 100:.2f}",
            "nights": (booking.checkout_date - booking.date).days,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "is_confirmed": booking.status == reservation2.Status.CONFIRMED,
        },
    )


def verify_payment(request, booking_token):
    if request.method != "POST":
        return redirect("payment", booking_token=booking_token)

    booking = get_object_or_404(reservation2, checkout_token=booking_token)
    if booking.status == reservation2.Status.CONFIRMED:
        return redirect("payment", booking_token=booking.checkout_token)
    if booking.status not in (
        reservation2.Status.PENDING,
        reservation2.Status.FAILED,
    ) or not booking.payment_order_id:
        messages.error(request, "This booking is not awaiting payment.")
        return redirect(f"{reverse('book')}?room={booking.room}")

    order_id = request.POST.get("razorpay_order_id", "")
    payment_id = request.POST.get("razorpay_payment_id", "")
    signature = request.POST.get("razorpay_signature", "")
    if (
        order_id != booking.payment_order_id
        or not payment_id
        or not signature
        or not settings.RAZORPAY_KEY_SECRET
    ):
        messages.error(request, "Payment verification failed. Please try again.")
        return redirect("payment", booking_token=booking.checkout_token)

    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        f"{order_id}|{payment_id}".encode("utf-8"),
        digestmod="sha256",
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        messages.error(request, "Payment verification failed. Please try again.")
        return redirect("payment", booking_token=booking.checkout_token)

    try:
        payment_details = fetch_razorpay_payment(payment_id)
    except RazorpayError as error:
        messages.error(request, str(error))
        return redirect("payment", booking_token=booking.checkout_token)

    if (
        payment_details.get("status") != "captured"
        or payment_details.get("order_id") != order_id
        or payment_details.get("amount") != booking.amount_paise
        or payment_details.get("currency") != "INR"
    ):
        messages.error(
            request,
            "Payment has not been captured for the correct booking amount.",
        )
        return redirect("payment", booking_token=booking.checkout_token)

    if _has_conflicting_booking(
        booking.room,
        booking.date,
        booking.checkout_date,
        exclude_id=booking.pk,
    ):
        booking.payment_id = payment_id
        booking.status = reservation2.Status.REFUND_PENDING
        booking.save(update_fields=("payment_id", "status"))
        try:
            refund = refund_razorpay_payment(payment_id, booking.amount_paise)
        except RazorpayError:
            messages.error(
                request,
                "Payment was captured, but the room is no longer available. "
                "The refund needs manual follow-up; please contact the hotel.",
            )
            return redirect(f"{reverse('book')}?room={booking.room}")

        if refund.get("id"):
            refund_processed = refund.get("status") == "processed"
            booking.status = (
                reservation2.Status.REFUNDED
                if refund_processed
                else reservation2.Status.REFUND_PENDING
            )
            booking.save(update_fields=("status",))
            if refund_processed:
                messages.error(
                    request,
                    "The room became unavailable during payment. "
                    "The refund has been processed.",
                )
            elif refund.get("status") == "failed":
                messages.error(
                    request,
                    "The room became unavailable during payment, and the refund "
                    "could not be processed automatically. Please contact the hotel.",
                )
            else:
                messages.error(
                    request,
                    "The room became unavailable during payment. "
                    "A refund has been requested; please contact the hotel if it "
                    "does not appear on your original payment method.",
                )
            return redirect(f"{reverse('book')}?room={booking.room}")

        messages.error(
            request,
            "Payment was captured, but the refund could not be confirmed. "
            "Please contact the hotel.",
        )
        return redirect(f"{reverse('book')}?room={booking.room}")

    booking.payment_id = payment_id
    booking.status = reservation2.Status.CONFIRMED
    booking.save(update_fields=("payment_id", "status"))
    messages.success(request, "Payment successful. Your room is confirmed.")
    return redirect("payment", booking_token=booking.checkout_token)

def service(request):
    return render(request,"service.html")
def standard(request):
    return _render_room_detail(request, "Standard")
def standardbook(request):
    return redirect(f"{reverse('book')}?room=Standard")

def deluxe(request):
    return _render_room_detail(request, "Deluxe")
def imperial(request):
    return _render_room_detail(request, "Imperial")
def faq(request):
    return render(request,"faq.html")
def insert3Data(request):
    return _submit_booking(request, forced_room="Standard")
def deluxebook(request):
    return redirect(f"{reverse('book')}?room=Deluxe")
def insert4Data(request):
    return _submit_booking(request, forced_room="Deluxe")


def imperialbook(request):
    return redirect(f"{reverse('book')}?room=Imperial")
def insert5Data(request):
    return _submit_booking(request, forced_room="Imperial")
# def payment(request):
#     return render(request,"payment.html")
# Create your views here.
