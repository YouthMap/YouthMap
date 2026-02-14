// Hijack the posting of the form to instead send the POST asynchronously and show the form-success or form-error
// elements
function submitForm(action) {
    event.preventDefault();

    // If the action is not "Delete", apply the form validity check. (A form for an item you're going to delete
    // anyway doesn't need a validity check.)
    var ok = true;
    if (action != "Delete") {
        if (!form.checkValidity()) {
            form.reportValidity();
            ok = false;
        }
    }

    if (ok) {
        // Prepare the form data to send
        var formData = "action=" + action + "&" + $("#form").serialize();

        // Perform the post request
        $.post(window.location.href, formData)
            .done(function(response) {
                $("#form-error").hide();
                if ("message" in response) {
                    $("#form-success").show();
                    $("#form-success-text").text(response["message"]);
                    $("#form-success").get(0).scrollIntoView({behavior: 'smooth'});
                }
                if ("redirect_url" in response) {
                    setTimeout(function() { window.location.href = response["redirect_url"] }, ("message" in response) ? 2000 : 0);
                }
            })
            .fail(function(xhr) {
                response = JSON.parse(xhr.responseText);
                $("#form-success").hide();
                if ("message" in response) {
                    $("#form-error").show();
                    $("#form-error-text").text(response["message"]);
                    $("#form-error").get(0).scrollIntoView({behavior: 'smooth'});
                }
                if ("redirect_url" in response) {
                    setTimeout(function() { window.location.href = response["redirect_url"] }, ("message" in response) ? 2000 : 0);
                }
            });
    }
    return false;
}