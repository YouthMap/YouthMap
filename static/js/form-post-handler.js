// Hijack the posting of the form to instead send the POST asynchronously and show the form-success or form-error
// elements. If a reCAPTCHA element is on the page, it will call its code as part of the submission process,
function submitForm(action) {
    event.preventDefault();

    // Display status on the form as "in progress"
    $("#form-progress").show();
    $("#form-success").hide();
    $("#form-error").hide();
    $("#form-progress").get(0).scrollIntoView({behavior: 'smooth'});

    // Determine if we should use CAPTCHA or not when submitting the form
    if (typeof captchaOnThisPage !== 'undefined' && captchaOnThisPage) {
        grecaptcha.ready(function() {
          grecaptcha.execute(recaptchaSiteKey, {action: 'submit'}).then(function(token) {
              submitFormInner(action, token);
          });
        });
    } else {
        submitFormInner(action, null);
    }
}

// "Inner" submit method. This is either called directly if no CAPTCHA is in use, or after the CAPTCHA process if it is.
// recaptchaToken is only required if a CAPTCHA is in use.
function submitFormInner(action, recaptchaToken) {
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
        // Prepare the form data to send. FormData handles both regular and file inputs.
        var formData = new FormData(document.getElementById("form"));
        formData.append("action", action);
        if (recaptchaToken) {
            formData.append("recaptcha_token", recaptchaToken);
        }

        // Perform the post request
        $.ajax({ url: window.location.href, type: 'POST', data: formData, processData: false, contentType: false })
            .done(function(response) {
                $("#form-error").hide();
                $("#form-progress").hide();
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
                // Hopefully we should have a proper JSON structure here that we designed and deliberately sent. However
                // if the web server throws some error before producing the JSON, we might just get some text, so show
                // that instead.
                try {
                    response = JSON.parse(xhr.responseText);
                } catch (error) {
                    response = {"message": xhr.responseText};
                }

                $("#form-success").hide();
                $("#form-progress").hide();
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