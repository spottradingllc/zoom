define(['knockout', 'service' ], function (ko, service) {

    var env = {};

    var onSuccess = function(data) {
        var environment = data.environment;
        env.environment = environment;

        var stylename = environment.toLowerCase().concat('_style');
        document.getElementById(stylename).removeAttribute('disabled');
    };


    var onFailure = function(data) {
        alert("There was an error getting environment");
    };

    service.get('api/environment/', onSuccess, onFailure);

    return env;
});
