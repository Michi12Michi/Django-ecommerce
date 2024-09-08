var updateButtons = document.querySelectorAll(".update-cart");

if (updateButtons) {
    updateButtons.forEach(element => {
        element.addEventListener("click", function(){
            var productId = this.dataset.product;
            var action = this.dataset.action;
            if (user == 'AnonymousUser') {
                window.location.href = "/login";
            } else {
                updateUserOrder(productId, action);
            }
        });
    });
}

function updateUserOrder(productId, action) {
    var url = '/update-item/';
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken, 
        },
        body: JSON.stringify({
            'productID': productId, 
            'action': action
        })
    }).then((response) => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }).then((data) => {
        location.reload();
    }).catch((error) => {
        console.error('There was a problem with the fetch operation:', error);
    });
};