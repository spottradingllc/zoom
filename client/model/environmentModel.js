define(['knockout', 'service' ], function(ko, service) {
    var environment = {};
    environment.env = ko.observable('Unknown');
    
    var envColor = {
        staging: '#FFDA47',
        stagText: '#000000',
        production: '#E64016',
        prodText: '#FFFFFF',
        unknown: '#FF33CC'
     };

    environment.envType = {
        stg: 'staging',
        uat: 'uat',
        prod: 'production'
    };

    environment.envColor = ko.computed(function() {
        switch (environment.env().toLowerCase()) {
            case environment.envType.stg:
                return envColor.staging;
            case environment.envType.uat:
                return envColor.uat;
            case environment.envType.prod:
                return envColor.production;
            default:
                return envColor.unknown;
        }
    });

    environment.envTextColor = ko.computed(function() {
        switch (environment.env().toLowerCase()) {
            case environment.envType.prod:
                return envColor.prodText;
            default:
                return envColor.stagText;
        }
    });

    var onSuccess = function(data) {
        environment.env(data.environment);
        var stylename = data.environment.toLowerCase().concat('_style');
        document.getElementById(stylename).removeAttribute('disabled');
    };

    var onFailure = function(data) {
        swal('Well shoot...', 'There was an error getting environment', 'error');
    };

    service.get('api/v1/environment/', onSuccess, onFailure);

    return environment;
});
