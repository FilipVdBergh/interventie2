function confirm_redirect(message, confirmed_url) {
    var result = confirm(message);
    if (result == true) { window.location.href = confirmed_url } 
}