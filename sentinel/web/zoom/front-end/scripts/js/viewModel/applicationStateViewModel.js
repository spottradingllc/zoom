define(
    ['jquery', 'knockout', 'service', 'sammyApp', 'd3',
        'model/clsApplicationStateModel',
        'model/clsGlobalMode',
        'model/clsApplicationState',
        'classes/clsCustomFilter',
        'classes/dependency-maps/clsDependencyMaps',
        'classes/dependency-maps/clsIndentedDependencyTree',
        'classes/dependency-maps/clsPartitionChart'],
function($, ko, service, sam, d3) {

    function ViewModel() {
        var self = this;
        self.login = new LoginModel(service, ko, sam);
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
    }

    return {
        application_state: function (context) {
            context.view = "application_state";
            return context.viewModel = new ViewModel();
        }
    };
});
