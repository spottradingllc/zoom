define(
    [
        'plugins/router',
        'durandal/app',
        'jquery',
        'knockout',
        'service',
        'model/loginModel',
        'model/adminModel',
        'model/environmentModel',
        'model/pillarModel',
        'bootstrap'
    ],
    function(router, app, $, ko, service, login, admin, environment, pillar) {
        var self = this;
        self.connection = {};

        // Create the websocket right away so we know if we lose connection to server on any page
        $(document).ready(function() {
            self.connection = new WebSocket('ws://' + document.location.host + '/zoom/ws');

            self.connection.onopen = function() {
                console.log('websocket connected');
            };

            self.connection.onclose = function(evt) {
                console.log('websocket closed');
                document.getElementById("applicationHost").style.backgroundColor = '#FF7BFE';
                swal('Uh oh...', 'You will need to refresh the page to receive updates.', 'error');
            };
        });

        return {
            router: router,
            login: login,
            admin: admin,
            environment: environment,
            pillar: pillar,
            connection: self.connection,
            isFAQ: function(title) {
                return title.search('FAQ') !== -1;
            },
            activate: function() {
                router.map([
                    { route: '', title: 'Application State', moduleId: 'viewmodels/applicationState', nav: true },
                    { route: 'config(/:server)', title: 'Server Config', moduleId: 'viewmodels/serverConfig', nav: true, hash: '#config' },
                    { route: 'pillar', title: 'Pillar Config', moduleId: 'viewmodels/pillarConfig', nav: true },
                    { route: 'appFAQ', title: 'App State FAQ', moduleId: 'viewmodels/faq/applicationState', nav: true },
                    { route: 'configFAQ', title: 'Server Config FAQ', moduleId: 'viewmodels/faq/serverConfig', nav: true }
                ]).buildNavigationModel();

                return router.activate();
            }
        };
    });
