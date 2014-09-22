define(['knockout', 'service' ], function (ko, service) {

    var env = ko.observable("Unknown");

    var onSuccess = function(data) {
        env(data.environment);
        var stylename = data.environment.toLowerCase().concat('_style');
        document.getElementById(stylename).removeAttribute('disabled');
    };


    var onFailure = function(data) {
        alert("There was an error getting environment");
    };

    service.get('api/environment/', onSuccess, onFailure);

    return env;
});
