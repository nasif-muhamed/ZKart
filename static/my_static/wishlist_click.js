$(document).ready(function() {
    $('.wishlist-icon').click(function(e) {
        e.preventDefault();
        var aTag = $(this);
        var productId = $(this).data('product-id');

        if (user == 'AnonymousUser'){
            alert("Login to use wishlist function")
            return;
            
        }else{
            $.ajax({
                method: 'POST',
                url: toggle_wishlist_url,  // Make sure to create this URL in your Django URLs
                data: {
                    'product_id': productId,
                    'csrfmiddlewaretoken': csrf_token
                },
                success: function(response) {
                    if (response.action === 'added') {
                        aTag.css({
                            'color': 'red',
                        });
                    } else {
                        aTag.css({
                            'color': '#a8aeb3',
                        });
                    }
                },
                error: function(xhr, status, error) {
                    console.error(xhr.responseText);
                }
            });
        }
        
    });
});