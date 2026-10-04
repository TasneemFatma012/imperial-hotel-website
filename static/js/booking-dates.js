(() => {
  const arrival = document.getElementById("booking-date");
  const checkout = document.getElementById("booking-checkout-date");
  if (!(arrival instanceof HTMLInputElement) || !(checkout instanceof HTMLInputElement)) {
    return;
  }

  const updateCheckoutDate = () => {
    const minCheckout = arrival.value || arrival.min;
    if (!minCheckout) return;

    const nextDay = new Date(`${minCheckout}T00:00:00`);
    nextDay.setDate(nextDay.getDate() + 1);
    checkout.min = [
      nextDay.getFullYear(),
      String(nextDay.getMonth() + 1).padStart(2, "0"),
      String(nextDay.getDate()).padStart(2, "0"),
    ].join("-");

    if (checkout.value && checkout.value < checkout.min) {
      checkout.value = "";
    }
  };

  arrival.addEventListener("change", updateCheckoutDate);
  updateCheckoutDate();
})();
