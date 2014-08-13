define(['durandal/app', 
        'knockout', 
        'service', 
        'jquery', 
        'd3', 
        'model/loginModel', 
        'model/ApplicationStateModel', 
        'model/GlobalMode',
        'bindings/radio'], function (app, ko, service, $, d3, login, ApplicationStateModel, GlobalMode) {

    var self = this;
    self.login = login;
    self.applicationState = new ApplicationStateModel(service, ko, $, self.login, d3);
    self.mode = new GlobalMode(service, ko, $, self.login);

    var connection;
    $(document).ready(function () {
        connection = new WebSocket('ws://' + document.location.host + '/zoom/ws');
        
        connection.onopen = function () {
            console.log("websocket connected");
        };

        connection.onclose = function (evt) {
            console.log("websocket closed");
            alert("The connection to the server has closed.\nYou will need to refresh the page to receive updates.")
        };

        connection.onmessage = function (evt) {
            console.log("websocket message: " + evt.data);
            var message = JSON.parse(evt.data);

            if ('update_type' in message) {

                if (message.update_type == 'application_state') {

                    $.each(message.application_states, function() {
                        self.applicationState.handleApplicationStatusUpdate(this)
                    });

                    // resort the column, holding its sorted direction
                    self.applicationState.holdSortDirection(true);
                    self.applicationState.sort(self.applicationState.activeSort());
                }

                else if (message.update_type == 'global_mode') {
                    self.mode.fnHandleModeUpdate(message)
                }
                else if (message.update_type == 'timing_estimate') {
                    self.mode.fnHandleTimingUpdate(message);
                }
                else if (message.update_type == 'application_dependency') {
                    self.applicationState.handleApplicationDependencyUpdate(message);
                }
                else
                {
                    console.log('unknown type in message: ' + message.update_type);
                }
            }
            else
            {
                console.log('no type in message');
            }
        }
    });


    return {
        applicationState: self.applicationState,
        mode: self.mode,
        login: self.login
    };
});
