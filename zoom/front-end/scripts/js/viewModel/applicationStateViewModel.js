define(['jquery', 'knockout', 'service',
        'model/clsApplicationStateModel',
        'model/clsGlobalMode',
        'model/clsApplicationState',
        'classes/clsCustomFilter'],
function($, ko, service) {

    function ViewModel() {
        var self = this;
        self.applicationState = new ApplicationStateModel(service, ko, $);
        self.mode = new GlobalMode(service, ko, $);

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

                if ('type' in message) {

                    if (message['type'] == 'application_state') {
                        // This should always be one update.
                        var item = message.payload.application_states[0];
                        // Search the array for row with matching path
                        var row = ko.utils.arrayFirst(self.applicationState.applicationStates(), function (currentRow) {
                            return currentRow.configurationPath == item.configuration_path;
                        });
                        // If row was found in the lookup
                        if (row) {
                            row.applicationStatus(item.application_status);
                            row.startTime(item.start_time);
                            row.applicationHost(item.application_host);
                            row.errorState(item.error_state)
                        }
                        else {
                            console.log('No rows in the array match the update');
                        }

                        // resort the column, holding its sorted direction
                        self.applicationState.holdSortDirection(true);
                        self.applicationState.sort(self.applicationState.activeSort());
                    }

                    else if (message['type'] == 'global_mode') {
                        payload = JSON.parse(message.payload);
                        if (payload.mode == 'manual') {
                            self.mode.current('Ignoring ZK changes.');
                        }
                        else if (payload.mode == 'auto') {
                            self.mode.current('Reacting to ZK changes.');
                        }
                    }
                }
            }
        });


        return {
            applicationState: self.applicationState,
            mode: self.mode
        };
    }

    return {
        application_state: function (context) {
            context.view = "application_state";
            return context.viewModel = new ViewModel();
        }
    };
});