define(['knockout'],
function(ko){
    var AlertsViewModel = {
        successMode : ko.observable(false),
        successText : ko.observable(""),
        errorMode : ko.observable(false),
        errorText : ko.observable("")
    };

    AlertsViewModel.closeAlerts = function() {
        AlertsViewModel.closeError();
        AlertsViewModel.closeSuccess();
    };

    AlertsViewModel.displaySuccess = function(successMessage) {
        AlertsViewModel.closeAlerts();
        AlertsViewModel.successMode(true);
        AlertsViewModel.successText(successMessage);
    };

    AlertsViewModel.displayError = function(errorMessage) {
        //TODO: float alerts for visibility
        AlertsViewModel.closeAlerts();
        AlertsViewModel.errorMode(true);
        AlertsViewModel.errorText(errorMessage);
    };

    AlertsViewModel.closeSuccess = function() {
        AlertsViewModel.successMode(false);
        AlertsViewModel.successText("");
    };

    AlertsViewModel.closeError = function() {
        AlertsViewModel.errorMode(false);
        AlertsViewModel.errorText("");
    };
    return AlertsViewModel
});
