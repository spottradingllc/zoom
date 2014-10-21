define(
    [
        'durandal/app',
        'knockout',
        'service',
        'jquery',
        'd3',
        'model/loginModel',
        'model/ApplicationStateModel',
        'model/GlobalMode',
        'bindings/radio'
    ],
    function(app, ko, service, $, d3, login, ApplicationStateModel, GlobalMode) {
        var self = this;
        self.login = login;
        self.appStateModel = new ApplicationStateModel(self.login);
        self.mode = GlobalMode;

        var connection;
        $(document).ready(function() {
            connection = new WebSocket('ws://' + document.location.host + '/zoom/ws');

            connection.onopen = function() {
                console.log('websocket connected');

            };

            connection.onclose = function(evt) {
                console.log('websocket closed');
                document.getElementById("application_state_page").style.backgroundColor = '#FF7BFE';
                swal('Uh oh...', 'You will need to refresh the page to receive updates.', 'error');
            };

            connection.onmessage = function(evt) {
                // console.log('websocket message: ' + evt.data);
                var message = JSON.parse(evt.data);

                if ('update_type' in message) {

                    if (message.update_type === 'application_state') {

                        $.each(message.application_states, function() {
                            self.appStateModel.handleApplicationStatusUpdate(this);
                        });

                        // resort the column, holding its sorted direction
                        self.appStateModel.holdSortDirection(true);
                        self.appStateModel.sort(self.appStateModel.activeSort());
                    }

                    else if (message.update_type === 'global_mode') {
                        self.mode.handleModeUpdate(message);
                    }
                    else if (message.update_type === 'timing_estimate') {
                        self.mode.handleTimingUpdate(message);
                    }
                    else if (message.update_type === 'application_dependency') {
                        self.appStateModel.handleApplicationDependencyUpdate(message);
                    }
                    else {
                        console.log('unknown type in message: ' + message.update_type);
                    }
                }
                else {
                    console.log('no type in message');
                }
            };
        });

        self.attached = function() {
            self.appStateModel.loadApplicationStates();  // load initial data
            self.appStateModel.loadApplicationDependencies();  // load initial data
            self.appStateModel.dependencyMaps.showView(self.appStateModel.currentView());
        };

        self.detached = function() {
            self.appStateModel.clearGroupControl();
            self.appStateModel.dependencyMaps.closeAllViews();
        };

        return {
            appStateModel: self.appStateModel,
            mode: self.mode,
            login: self.login,
            detached: self.detached,
            attached: self.attached
        };
    });
