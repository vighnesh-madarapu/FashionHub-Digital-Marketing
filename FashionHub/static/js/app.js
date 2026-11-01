document.addEventListener("DOMContentLoaded", function () {

    // Automatically close flash messages
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {
        setTimeout(function () {
            if (typeof bootstrap !== "undefined") {
                const alertInstance =
                    bootstrap.Alert.getOrCreateInstance(alert);
                alertInstance.close();
            }
        }, 4000);
    });

    // Confirm logout
    const logoutLinks = document.querySelectorAll(".logout-link");

    logoutLinks.forEach(function (link) {
        link.addEventListener("click", function (event) {
            const confirmed = confirm("Are you sure you want to logout?");

            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    console.log("FashionHub JavaScript loaded successfully!");
});