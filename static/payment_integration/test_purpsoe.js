// Create order with Razorpay
$('.pay_with_razorpay').click(function (e) {
    e.preventDefault();
    var csrftoken = $('input[name=csrfmiddlewaretoken]').val();
    var selectedAddress = $('input[name="selected_address"]:checked');
    var selectedAddressId = selectedAddress.val();
    var grandTotalText = $('.grand_total').text();
    var grandTotalNumeric = parseFloat(grandTotalText.replace('₹', ''));
    var checkoutData = $('#checkout-data');
    var email = checkoutData.attr('data-email');
    var name = checkoutData.attr('data-name');
    // var payment_mode = $(this).val();
    // var neworder = $(this).data('neworder');
    // console.log(neworder)
    // console.log(payment_mode)
    // console.log(selectedAddress.val())

    if (!selectedAddress.val()) {
        swal.fire({
            icon: 'error',
            title: 'Select an address',
            timer: 1000
        })
        return false
    }
    else {
        $.ajax({
            url: "create-order",
            type: "POST",
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
                "selected_address": selectedAddress.val(),
            },
            data: JSON.stringify({ selected_address_id: selectedAddressId }),
        })
            .done(function (data) {
                var options = {
                    key: 'rzp_test_1DBm3kToLW56S3',
                    amount: grandTotalNumeric * 100,
                    currency: "INR",
                    name: "Quality Traders",
                    description: "Order Payment",
                    order_id: data.order_id,
                    t_no: data.tracking_no,
                    "prefill": {
                        "name": name,
                        "email": email,
                    },
                    handler: function (response) {
                        console.log(response)
                        var razorpay_order_id = response.razorpay_order_id;
                        var razorpay_payment_id = response.razorpay_payment_id;
                        console.log(razorpay_order_id, razorpay_payment_id)

                        $.ajax({
                            url: "handle-payment",
                            type: "POST",
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrftoken
                            },
                            data: JSON.stringify({
                                order_id: razorpay_order_id,
                                payment_id: razorpay_payment_id
                            })
                        })
                            .done(function (data) {
                                if (data.message === 'Payment Successful') {
                                    Swal.fire({
                                        icon: "success",
                                        title: data.message,
                                        timer: 1500
                                    }).then((result) => {
                                        window.location.href = 'view-order/' + options.t_no;
                                    })
                                } else if (data.message === 'Payment Failed') {
                                    Swal.fire({
                                        icon: "error",
                                        title: data.message,
                                        timer: 1500
                                    }).then((result) => {
                                        window.location.href = 'view-order/' + options.t_no;
                                    })
                                }
                            })
                            .fail(function (jqXHR, textStatus, errorThrown) {
                                console.error('An error occurred while processing the payment.', jqXHR);
                                Swal.fire({
                                    icon: "error",
                                    title: "Payment Failed",
                                    text: "There was an issue processing your payment. Please try again.",
                                    timer: 1500
                                })
                            });
                    }
                };
                var rzp1 = new Razorpay(options);
                rzp1.open();

            })
            .fail(function (jqXHR, textStatus, errorThrown) {
                console.error('Error creating order:', jqXHR);
                Swal.fire({
                    icon: "error",
                    title: "Order creation Failed",
                    text: jqXHR.responseJSON.error,
                    timer: 1500
                })
            })

    }
}
);