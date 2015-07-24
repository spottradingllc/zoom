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
        'viewmodels/navbar',
        'bindings/radio',
        'bindings/tooltip'
    ],
    function(app, ko, service, $, d3, login, ApplicationStateModel, GlobalMode, navbar) {
        var self = this;
        self.navbar = navbar;
        self.login = login;
        self.appStateModel = new ApplicationStateModel(self.login);
        self.mode = GlobalMode;
        self.initialLoad = ko.observable(false);

        var callbackInstance = {};
        var callbackObj = function() {
            this.callback = function() {
                self.navbar.connection.onmessage = function (evt) {
                    var message = JSON.parse(evt.data);

                    if ('update_type' in message) {

                        if (message.update_type === 'application_state') {

                            $.each(message.application_states, function () {
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
            };
        };


        self.attached = function() {
            if (!self.initialLoad()) {
                self.initialLoad(true);
                self.appStateModel.loadApplicationStates();  // load initial data
                self.appStateModel.loadApplicationDependencies();  // load initial data
                // resort after all the dependencies trickle in.
                setTimeout(function() { self.appStateModel.sort(self.appStateModel.headers[0]); }, 3000);
                callbackInstance = new callbackObj;
                callbackInstance.callback();
            }

        };

        self.detached = function() {
            self.appStateModel.clearGroupControl();
        };

        return {
            appStateModel: self.appStateModel,
            mode: self.mode,
            login: self.login,
            detached: self.detached,
            attached: self.attached
        };
    });
