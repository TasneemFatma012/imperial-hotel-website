import hashlib
import hmac
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Contact1, reservation2


@override_settings(RAZORPAY_KEY_ID="rzp_test_key", RAZORPAY_KEY_SECRET="test_secret")
class SharedBookingPageTests(TestCase):
    def test_room_booking_routes_open_the_shared_form_with_room_selected(self):
        for route_name, room in (
            ("standardbook", "Standard"),
            ("deluxebook", "Deluxe"),
            ("imperialbook", "Imperial"),
        ):
            with self.subTest(room=room):
                response = self.client.get(reverse(route_name), follow=True)
                self.assertEqual(response.request["PATH_INFO"], reverse("book"))
                self.assertEqual(response.context["selected_room"], room)

    @patch(
        "app.views.create_razorpay_order",
        return_value={"id": "order_test_123", "amount": 500000, "currency": "INR"},
    )
    def test_booking_submission_saves_dates_amount_and_payment_order(self, create_order):
        arrival = timezone.localdate() + timedelta(days=20)
        checkout = arrival + timedelta(days=2)
        response = self.client.post(
            reverse("insertdata"),
            {
                "fname": "Asha",
                "lname": "Sharma",
                "phone": "+91 01234 56789",
                "email": "asha@example.com",
                "room": "Deluxe",
                "date": arrival.isoformat(),
                "checkout_date": checkout.isoformat(),
            },
        )

        booking = reservation2.objects.get()
        self.assertRedirects(
            response,
            reverse("payment", args=(booking.checkout_token,)),
        )
        create_order.assert_called_once_with(
            500000,
            receipt=f"hotel-{booking.pk}",
            booking_id=booking.pk,
        )
        self.assertEqual(booking.room, "Deluxe")
        self.assertEqual(booking.phone, "+91 01234 56789")
        self.assertEqual(booking.date, arrival)
        self.assertEqual(booking.checkout_date, checkout)
        self.assertEqual(booking.amount_paise, 500000)
        self.assertEqual(booking.payment_order_id, "order_test_123")
        self.assertEqual(booking.status, reservation2.Status.PENDING)

    def test_invalid_room_is_not_saved(self):
        response = self.client.post(
            reverse("insertdata"),
            {
                "fname": "Asha",
                "lname": "Sharma",
                "phone": "0123456789",
                "email": "asha@example.com",
                "room": "Penthouse",
                "date": (timezone.localdate() + timedelta(days=20)).isoformat(),
                "checkout_date": (timezone.localdate() + timedelta(days=21)).isoformat(),
            },
        )

        self.assertRedirects(response, reverse("book"))
        self.assertEqual(reservation2.objects.count(), 0)

    def test_invalid_booking_details_are_not_saved(self):
        response = self.client.post(
            reverse("insertdata"),
            {
                "fname": "Asha",
                "lname": "Sharma",
                "phone": "0123456789",
                "email": "not-an-email",
                "room": "Deluxe",
                "date": (timezone.localdate() + timedelta(days=20)).isoformat(),
                "checkout_date": "not-a-date",
            },
            follow=True,
        )

        self.assertRedirects(response, f"{reverse('book')}?room=Deluxe")
        self.assertEqual(reservation2.objects.count(), 0)
        self.assertContains(response, "Please check the booking details.")

    @patch(
        "app.views.create_razorpay_order",
        return_value={"id": "order_legacy", "amount": 250000, "currency": "INR"},
    )
    def test_legacy_booking_endpoints_validate_and_force_their_room(self, create_order):
        arrival = timezone.localdate() + timedelta(days=20)
        response = self.client.post(
            reverse("insert3data"),
            {
                "fname": "Asha",
                "lname": "Sharma",
                "phone": "0123456789",
                "email": "asha@example.com",
                "room": "Imperial",
                "date": arrival.isoformat(),
                "checkout_date": (arrival + timedelta(days=1)).isoformat(),
            },
        )

        self.assertRedirects(
            response,
            reverse("payment", args=(reservation2.objects.get().checkout_token,)),
        )
        create_order.assert_called_once()
        self.assertEqual(reservation2.objects.get().room, "Standard")

    def test_legacy_booking_get_routes_return_to_shared_form(self):
        for route_name, room in (
            ("standardbook", "Standard"),
            ("deluxebook", "Deluxe"),
            ("imperialbook", "Imperial"),
        ):
            with self.subTest(room=room):
                response = self.client.get(reverse(route_name))
                self.assertRedirects(response, f"{reverse('book')}?room={room}")

    @patch(
        "app.views.create_razorpay_order",
        return_value={"id": "order_adjacent", "amount": 250000, "currency": "INR"},
    )
    def test_checkout_date_can_match_next_guests_arrival(self, create_order):
        arrival = timezone.localdate() + timedelta(days=25)
        reservation2.objects.create(
            fname="Previous",
            lname="Guest",
            phone="0123456789",
            email="previous@example.com",
            room="Standard",
            date=arrival - timedelta(days=2),
            checkout_date=arrival,
            amount_paise=500000,
            status=reservation2.Status.CONFIRMED,
        )

        response = self.client.post(
            reverse("insertdata"),
            {
                "fname": "Asha",
                "lname": "Sharma",
                "phone": "0123456789",
                "email": "asha@example.com",
                "room": "Standard",
                "date": arrival.isoformat(),
                "checkout_date": (arrival + timedelta(days=1)).isoformat(),
            },
        )

        booking = reservation2.objects.exclude(email="previous@example.com").get()
        self.assertRedirects(
            response,
            reverse("payment", args=(booking.checkout_token,)),
        )
        create_order.assert_called_once()

    def test_overlapping_confirmed_reservation_is_not_available(self):
        arrival = timezone.localdate() + timedelta(days=25)
        reservation2.objects.create(
            fname="Previous",
            lname="Guest",
            phone="0123456789",
            email="previous@example.com",
            room="Deluxe",
            date=arrival,
            checkout_date=arrival + timedelta(days=3),
            amount_paise=750000,
            status=reservation2.Status.CONFIRMED,
        )

        response = self.client.post(
            reverse("insertdata"),
            {
                "fname": "Asha",
                "lname": "Sharma",
                "phone": "0123456789",
                "email": "asha@example.com",
                "room": "Deluxe",
                "date": (arrival + timedelta(days=2)).isoformat(),
                "checkout_date": (arrival + timedelta(days=4)).isoformat(),
            },
            follow=True,
        )

        self.assertEqual(reservation2.objects.count(), 1)
        self.assertContains(response, "That room is not available")

    @patch("app.views.create_razorpay_order", return_value={})
    def test_payment_order_failure_releases_the_booking_hold(self, create_order):
        arrival = timezone.localdate() + timedelta(days=25)
        response = self.client.post(
            reverse("insertdata"),
            {
                "fname": "Asha",
                "lname": "Sharma",
                "phone": "0123456789",
                "email": "asha@example.com",
                "room": "Imperial",
                "date": arrival.isoformat(),
                "checkout_date": (arrival + timedelta(days=1)).isoformat(),
            },
            follow=True,
        )

        self.assertEqual(reservation2.objects.get().status, reservation2.Status.FAILED)
        self.assertContains(response, "Razorpay did not return a payment order.")
        create_order.assert_called_once()

    @override_settings(RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET="")
    @patch("app.views.create_razorpay_order")
    def test_missing_gateway_keys_do_not_create_a_booking(self, create_order):
        arrival = timezone.localdate() + timedelta(days=25)
        response = self.client.post(
            reverse("insertdata"),
            {
                "fname": "Asha",
                "lname": "Sharma",
                "phone": "0123456789",
                "email": "asha@example.com",
                "room": "Standard",
                "date": arrival.isoformat(),
                "checkout_date": (arrival + timedelta(days=1)).isoformat(),
            },
            follow=True,
        )

        self.assertEqual(reservation2.objects.count(), 0)
        self.assertContains(response, "Online payments are not configured yet.")
        create_order.assert_not_called()

    @patch(
        "app.views.create_razorpay_order",
        return_value={"id": "order_wrong_amount", "amount": 1, "currency": "INR"},
    )
    def test_unexpected_razorpay_order_amount_is_rejected(self, create_order):
        arrival = timezone.localdate() + timedelta(days=25)
        response = self.client.post(
            reverse("insertdata"),
            {
                "fname": "Asha",
                "lname": "Sharma",
                "phone": "0123456789",
                "email": "asha@example.com",
                "room": "Standard",
                "date": arrival.isoformat(),
                "checkout_date": (arrival + timedelta(days=1)).isoformat(),
            },
            follow=True,
        )

        booking = reservation2.objects.get()
        self.assertEqual(booking.status, reservation2.Status.FAILED)
        self.assertEqual(booking.payment_order_id, "")
        self.assertContains(response, "unexpected amount")
        create_order.assert_called_once()

    def test_checkout_date_must_be_after_arrival(self):
        arrival = timezone.localdate() + timedelta(days=25)
        response = self.client.post(
            reverse("insertdata"),
            {
                "fname": "Asha",
                "lname": "Sharma",
                "phone": "0123456789",
                "email": "asha@example.com",
                "room": "Imperial",
                "date": arrival.isoformat(),
                "checkout_date": arrival.isoformat(),
            },
            follow=True,
        )

        self.assertEqual(reservation2.objects.count(), 0)
        self.assertContains(response, "Checkout date must be after the arrival date.")

    def test_explore_details_opens_the_matching_room_page(self):
        for route_name, room_name, room_key in (
            ("standard", "Standard Room", "Standard"),
            ("deluxe", "Deluxe Room", "Deluxe"),
            ("imperial", "Imperial Room", "Imperial"),
        ):
            with self.subTest(room=room_key):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, room_name)
                self.assertContains(
                    response,
                    f"{reverse('book')}?room={room_key}",
                )

    def test_faq_lists_guest_questions_and_links_to_booking_and_contact(self):
        response = self.client.get(reverse("faq"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How do I book a room?")
        self.assertContains(response, "What amenities are available in the rooms?")
        self.assertContains(response, 'class="faq-widget"')
        self.assertContains(response, reverse("book"))
        self.assertContains(response, reverse("contact"))

    def test_faq_help_icon_is_available_on_all_main_pages(self):
        for route_name in (
            "index",
            "about",
            "contact",
            "room",
            "handlelogin",
            "handlesignup",
            "book",
            "service",
            "standard",
            "deluxe",
            "imperial",
            "faq",
        ):
            with self.subTest(page=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="faq-widget"')


class AccountPageTests(TestCase):
    def test_login_and_signup_pages_render_their_forms(self):
        for route_name, heading in (
            ("handlelogin", "Sign in"),
            ("handlesignup", "Create account"),
        ):
            with self.subTest(page=heading):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, heading)
                self.assertContains(response, "account.css")

    def test_signup_creates_and_authenticates_user(self):
        response = self.client.post(
            reverse("handlesignup"),
            {
                "username": "asha_guest",
                "email": "asha@example.com",
                "password1": "SuiteStay!2026",
                "password2": "SuiteStay!2026",
            },
        )

        self.assertRedirects(response, reverse("index"))
        self.assertTrue(self.client.session.get("_auth_user_id"))
        self.assertTrue(User.objects.filter(username="asha_guest").exists())

    def test_invalid_signup_shows_errors_without_creating_user(self):
        response = self.client.post(
            reverse("handlesignup"),
            {
                "username": "asha_guest",
                "email": "asha@example.com",
                "password1": "SuiteStay!2026",
                "password2": "DifferentStay!2026",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn’t match.")
        self.assertEqual(User.objects.count(), 0)

    def test_login_authenticates_user_and_invalid_credentials_are_visible(self):
        User.objects.create_user(username="asha_guest", password="SuiteStay!2026")

        invalid_response = self.client.post(
            reverse("handlelogin"),
            {"username": "asha_guest", "password": "incorrect"},
        )
        self.assertEqual(invalid_response.status_code, 200)
        self.assertContains(invalid_response, "Please enter a correct username and password.")

        valid_response = self.client.post(
            reverse("handlelogin"),
            {"username": "asha_guest", "password": "SuiteStay!2026"},
        )
        self.assertRedirects(valid_response, reverse("index"))
        self.assertTrue(self.client.session.get("_auth_user_id"))

    def test_logout_clears_session_and_returns_home(self):
        user = User.objects.create_user(username="asha_guest", password="SuiteStay!2026")
        self.client.force_login(user)

        response = self.client.get(reverse("handlelogout"))

        self.assertRedirects(response, reverse("index"))
        self.assertNotIn("_auth_user_id", self.client.session)


class ContactFormTests(TestCase):
    def test_contact_message_is_saved(self):
        message_text = ("Please tell me about booking options. " * 20).strip()
        response = self.client.post(
            reverse("insert1data"),
            {
                "name1": "Asha Sharma",
                "emaild": "asha@example.com",
                "msg": message_text,
            },
        )

        self.assertRedirects(response, reverse("contact"))
        message = Contact1.objects.get()
        self.assertEqual(message.name1, "Asha Sharma")
        self.assertEqual(message.emaild, "asha@example.com")
        self.assertEqual(message.msg, message_text)

    def test_invalid_contact_email_is_rejected_without_saving(self):
        response = self.client.post(
            reverse("insert1data"),
            {
                "name1": "Asha Sharma",
                "emaild": "not-an-email",
                "msg": "I have a question about my stay.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address.")
        self.assertEqual(Contact1.objects.count(), 0)

    def test_contact_submission_route_rejects_get_requests(self):
        response = self.client.get(reverse("insert1data"))

        self.assertRedirects(response, reverse("contact"))


@override_settings(RAZORPAY_KEY_ID="rzp_test_key", RAZORPAY_KEY_SECRET="test_secret")
class RazorpayCheckoutTests(TestCase):
    def make_pending_booking(self):
        arrival = timezone.localdate() + timedelta(days=30)
        return reservation2.objects.create(
            fname="Asha",
            lname="Sharma",
            phone="+91 01234 56789",
            email="asha@example.com",
            room="Deluxe",
            date=arrival,
            checkout_date=arrival + timedelta(days=2),
            amount_paise=500000,
            payment_order_id="order_test_123",
            status=reservation2.Status.PENDING,
        )

    @staticmethod
    def payment_signature(payment_id):
        return hmac.new(
            b"test_secret",
            f"order_test_123|{payment_id}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

    def test_payment_page_displays_order_and_total(self):
        booking = self.make_pending_booking()

        response = self.client.get(reverse("payment", args=(booking.checkout_token,)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "₹5000.00")
        self.assertContains(response, 'data-order="order_test_123"')
        self.assertContains(response, "Razorpay")

    @override_settings(RAZORPAY_KEY_SECRET="test_secret")
    @patch(
        "app.views.fetch_razorpay_payment",
        return_value={
            "status": "captured",
            "order_id": "order_test_123",
            "amount": 500000,
            "currency": "INR",
        },
    )
    def test_valid_captured_payment_confirms_booking(self, fetch_payment):
        booking = self.make_pending_booking()
        payment_id = "pay_test_123"

        response = self.client.post(
            reverse("verify_payment", args=(booking.checkout_token,)),
            {
                "razorpay_order_id": "order_test_123",
                "razorpay_payment_id": payment_id,
                "razorpay_signature": self.payment_signature(payment_id),
            },
        )

        booking.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("payment", args=(booking.checkout_token,)),
        )
        self.assertEqual(booking.status, reservation2.Status.CONFIRMED)
        self.assertEqual(booking.payment_id, payment_id)
        fetch_payment.assert_called_once_with(payment_id)

    @override_settings(RAZORPAY_KEY_SECRET="test_secret")
    @patch("app.views.fetch_razorpay_payment")
    def test_invalid_signature_does_not_confirm_booking(self, fetch_payment):
        booking = self.make_pending_booking()

        response = self.client.post(
            reverse("verify_payment", args=(booking.checkout_token,)),
            {
                "razorpay_order_id": "order_test_123",
                "razorpay_payment_id": "pay_test_123",
                "razorpay_signature": "invalid",
            },
            follow=True,
        )

        booking.refresh_from_db()
        self.assertEqual(booking.status, reservation2.Status.PENDING)
        self.assertContains(response, "Payment verification failed")
        fetch_payment.assert_not_called()

    @override_settings(RAZORPAY_KEY_SECRET="test_secret")
    @patch(
        "app.views.fetch_razorpay_payment",
        return_value={
            "status": "authorized",
            "order_id": "order_test_123",
            "amount": 500000,
            "currency": "INR",
        },
    )
    def test_uncaptured_payment_does_not_confirm_booking(self, fetch_payment):
        booking = self.make_pending_booking()
        payment_id = "pay_test_123"

        response = self.client.post(
            reverse("verify_payment", args=(booking.checkout_token,)),
            {
                "razorpay_order_id": "order_test_123",
                "razorpay_payment_id": payment_id,
                "razorpay_signature": self.payment_signature(payment_id),
            },
            follow=True,
        )

        booking.refresh_from_db()
        self.assertEqual(booking.status, reservation2.Status.PENDING)
        self.assertContains(response, "Payment has not been captured")

    def test_expired_payment_page_releases_the_room_hold(self):
        booking = self.make_pending_booking()
        reservation2.objects.filter(pk=booking.pk).update(
            created_at=timezone.now() - timedelta(minutes=16)
        )

        response = self.client.get(
            reverse("payment", args=(booking.checkout_token,)),
            follow=True,
        )

        booking.refresh_from_db()
        self.assertEqual(booking.status, reservation2.Status.FAILED)
        self.assertContains(response, "payment session expired")

    @override_settings(RAZORPAY_KEY_SECRET="test_secret")
    @patch(
        "app.views.fetch_razorpay_payment",
        return_value={
            "status": "captured",
            "order_id": "order_test_123",
            "amount": 500000,
            "currency": "INR",
        },
    )
    def test_late_captured_payment_confirms_when_dates_remain_available(
        self, fetch_payment
    ):
        booking = self.make_pending_booking()
        booking.status = reservation2.Status.FAILED
        booking.created_at = timezone.now() - timedelta(minutes=16)
        booking.save(update_fields=("status", "created_at"))
        payment_id = "pay_late_123"

        response = self.client.post(
            reverse("verify_payment", args=(booking.checkout_token,)),
            {
                "razorpay_order_id": "order_test_123",
                "razorpay_payment_id": payment_id,
                "razorpay_signature": self.payment_signature(payment_id),
            },
        )

        booking.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("payment", args=(booking.checkout_token,)),
        )
        self.assertEqual(booking.status, reservation2.Status.CONFIRMED)
        self.assertEqual(booking.payment_id, payment_id)
        fetch_payment.assert_called_once_with(payment_id)

    @override_settings(RAZORPAY_KEY_SECRET="test_secret")
    @patch(
        "app.views.fetch_razorpay_payment",
        return_value={
            "status": "captured",
            "order_id": "order_test_123",
            "amount": 500000,
            "currency": "INR",
        },
    )
    @patch(
        "app.views.refund_razorpay_payment",
        return_value={"id": "rfnd_test_123", "status": "processed"},
    )
    def test_late_captured_payment_is_refunded_when_dates_were_rebooked(
        self, refund_payment, fetch_payment
    ):
        booking = self.make_pending_booking()
        booking.status = reservation2.Status.FAILED
        booking.created_at = timezone.now() - timedelta(minutes=16)
        booking.save(update_fields=("status", "created_at"))
        reservation2.objects.create(
            fname="Other",
            lname="Guest",
            phone="0123456789",
            email="other@example.com",
            room=booking.room,
            date=booking.date,
            checkout_date=booking.checkout_date,
            amount_paise=booking.amount_paise,
            status=reservation2.Status.CONFIRMED,
        )
        payment_id = "pay_late_123"

        response = self.client.post(
            reverse("verify_payment", args=(booking.checkout_token,)),
            {
                "razorpay_order_id": "order_test_123",
                "razorpay_payment_id": payment_id,
                "razorpay_signature": self.payment_signature(payment_id),
            },
            follow=True,
        )

        booking.refresh_from_db()
        self.assertEqual(booking.status, reservation2.Status.REFUNDED)
        self.assertEqual(booking.payment_id, payment_id)
        refund_payment.assert_called_once_with(payment_id, booking.amount_paise)
        fetch_payment.assert_called_once_with(payment_id)
        self.assertContains(response, "The refund has been processed")
