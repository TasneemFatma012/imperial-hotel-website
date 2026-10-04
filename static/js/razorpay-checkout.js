(() => {
  const button = document.getElementById("razorpay-pay-button");
  const verificationForm = document.getElementById("razorpay-verification-form");
  const errorMessage = document.getElementById("payment-error");
  if (!(button instanceof HTMLButtonElement) || !(verificationForm instanceof HTMLFormElement)) {
    return;
  }

  const showError = (message) => {
    errorMessage.textContent = message;
    errorMessage.hidden = false;
  };

  button.addEventListener("click", () => {
    if (typeof window.Razorpay !== "function") {
      showError("Secure checkout could not load. Please refresh this page and try again.");
      return;
    }

    const checkout = new window.Razorpay({
      key: button.dataset.key,
      order_id: button.dataset.order,
      amount: Number(button.dataset.amount),
      currency: "INR",
      name: "Imperial Hotel",
      description: "Room reservation",
      prefill: {
        name: button.dataset.name,
        email: button.dataset.email,
        contact: button.dataset.phone,
      },
      theme: { color: "#19352d" },
      handler(response) {
        for (const [name, value] of Object.entries({
          razorpay_payment_id: response.razorpay_payment_id,
          razorpay_order_id: response.razorpay_order_id,
          razorpay_signature: response.razorpay_signature,
        })) {
          const input = verificationForm.elements.namedItem(name);
          if (input instanceof HTMLInputElement) input.value = value;
        }
        verificationForm.requestSubmit();
      },
    });

    checkout.on("payment.failed", (response) => {
      showError(
        response.error?.description
          || "Payment was not completed. You can try again before this reservation hold expires."
      );
    });
    checkout.open();
  });
})();
