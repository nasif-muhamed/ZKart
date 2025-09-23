

$(document).ready(function() {
    $('.payWithRazorpay').click(function(e) {
        e.preventDefault();

        var selectedAddress = $('input[name="selectedAddress"]:checked').val();
        var specialInstruction = $('input[name="special_instructions"]').val();

        if (selectedAddress) {
            
            $.ajax({
                method: 'POST', 
                url: razorpayUrl,
                data: JSON.stringify({'selectedAddress': selectedAddress}),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                success: function(response) {
                    console.log(response);
                    response.total_amount = parseInt(response.total_amount/10, 10);
                    var options = {
                        "key": response.api_key, 
                        "name": "Z kart", 
                        "description": "Wishing You a Happy Shopping",
                        "image": "https://example.com/your_logo",
                        "order_id": response.order_id,
                        "handler": function (responseb){
                            console.log('responseee', response)
                            data = {
                                'selectedAddress': selectedAddress,
                                'selectedPayment' : 'razorpay',
                                'special_instructions':specialInstruction,
                                'payment_id' : responseb.razorpay_payment_id,
                                csrfmiddlewaretoken : csrftoken,
                            }

                            $.ajax({
                                method: 'POST', 
                                url: checkoutUrl,
                                data: data,
                                success: function(responsec) {
                                    alert(`Your order is successful. Thank You for Shopping with us`)
                                    alert(`Your Payment ID:${responseb.razorpay_payment_id}`);
                                    window.location.href = statusPageUrl.replace('0', responsec.order_id)
                                },

                                error: function(xhr, status, error) {
                                    console.error(xhr.responseText);
                                    alert('Oops something went wrong')
                                    location.reload()
                                },
                            });


                        },
                        "prefill": { 
                            "name": response.name, 
                            "email": response.email, 
                            "contact": response.contact  
                        },
                        
                        "theme": {
                            "color": "#3399cc"
                        }
                    };

                    var rzp1 = new Razorpay(options);

                    rzp1.on('payment.failed', function (response){
                        data = {
                            'selectedAddress': selectedAddress,
                            'selectedPayment' : 'razorpay',
                            'special_instructions':specialInstruction,
                            'payment_id' : response.error.metadata.payment_id,
                            'payment_failed' : true,
                            csrfmiddlewaretoken : csrftoken,
                        }

                        $.ajax({
                            method: 'POST', 
                            url: checkoutUrl,
                            data: data,
                            success: function(responsed) {
                                alert(`Your Payment is Failed. Continue payment from My Orders`)
                                window.location.href = statusPageUrl.replace('0', responsed.order_id)
                            },

                            error: function(xhr, status, error) {
                                console.error(xhr.responseText);
                                alert('Oops something went wrong, Contact costomer Care if your amount is debited')
                                location.reload()
                            },
                        });

                    });

                    rzp1.open();
                },

                error: function(xhr, status, error) {
                    try {
                        let response = JSON.parse(xhr.responseText);
                        if (response.reason) {
                            alert(`Error: ${response.reason}`);
                        } else {
                            console.error(xhr.responseText);
                            alert(`something went wrong, Contact costomer Care if your amount is debited`)        
                        }
                    } catch (e) {
                        console.error('Failed to parse JSON response:', e);
                        alert('something went wrong, Contact customer care if your amount is debited');
                    }
                },
            });

        } else {
            alert('Please select an address before proceeding.');
        }
        
    });



    $('.payWithRazorpayFromOrder').click(function(e) {

        e.preventDefault();
        data = {
            "order_id" : orderId,
            csrfmiddlewaretoken : csrftoken,
        }
        $.ajax({
            method: 'POST', 
            url: retryStockCheckUrl,
            data: data,
            success: function(response) {
                order_identifier = response.order_identifier
                var options = {
                    "key": "rzp_test_7YmhE9KuV2iwwZ", 
                    "name": "Z kart", 
                    "description": "Wishing You a Happy Shopping",
                    "image": "https://example.com/your_logo",
                    "order_id": order_identifier,
                    "handler": function (responseb){
                        data = {
                            // 'selectedAddress': selectedAddress,
                            // 'selectedPayment' : 'razorpay',
                            // 'special_instructions':specialInstruction,
                            'payment_id' : responseb.razorpay_payment_id,
                            'order_identifier' : order_identifier,
                            csrfmiddlewaretoken : csrftoken,
                        }
        
                        $.ajax({
                            method: 'POST', 
                            url: retryPaymentUrl.replace('0', orderId),
                            data: data,
                            success: function(responsec) {
                                alert(`Your order is successful. Thank You for Shopping with us`)
                                alert(`Your Payment ID:${responseb.razorpay_payment_id}`);
                                location.reload()
                                // window.location.href = `/order-success/${responsec.order_id}/`
                            },
        
                            error: function(xhr, status, error) {
                                console.error(xhr.responseText);
                                alert('Oops something went wrong. Contact costomer Care if your amount is debited')
                                location.reload()
                            },
                        });
        
                    },
                    "prefill": { 
                        "name": response.name, 
                        "email": response.email, 
                        "contact": response.contact, 
                    },
                    
                    "theme": {
                        "color": "#3399cc"
                    }
                };
        
                var rzp1 = new Razorpay(options);
        
                rzp1.on('payment.failed', function (response){
                    alert('Contact costomer Care if your amount is debited')
                });
        
                rzp1.open();        

            },

            error: function(xhr, status, error) {
                console.log(status)
                try {
                    let response = JSON.parse(xhr.responseText);
                    if (response.reason) {
                        alert(`${response.reason}`);
                    } else {
                        console.error(xhr.responseText);
                        alert(`something went wrong, Contact costomer Care if your amount is debited`)        
                    }
                } catch (e) {
                    console.error('Failed to parse JSON response:', e);
                    alert('something went wrong, Contact customer care if your amount is debited');
                }
                location.reload()
            },
        });



    });

});
