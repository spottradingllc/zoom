define(
    [
        'jquery',
        'knockout',
        'plugins/router',
        'viewmodels/serverConfig/alertsViewModel',
        'viewmodels/serverConfig/searchUpdateViewModel',
        'bindings/uppercase'
    ],
    function($, ko, router, AlertsViewModel, SearchUpdateViewModel) {

        var ServerConfigViewModel = {
            // view models
            alertsViewModel: AlertsViewModel,

            // variables
            serverList: ko.observableArray(),
            serverName: ko.observable('')
        };

        ServerConfigViewModel.activate = function(server) {
            if (server !== null) {
                ServerConfigViewModel.serverName(server);
                ServerConfigViewModel.search();
            }
        };

        ServerConfigViewModel.searchUpdateViewModel = new SearchUpdateViewModel(ServerConfigViewModel);

        ServerConfigViewModel.getAllServerNames = function() {
            $.getJSON('/api/config/list_servers/', function(data) {
                ServerConfigViewModel.serverList.removeAll();
                for (var i = 0; i < data.length; i++) {
                    ServerConfigViewModel.serverList.push(data[i]);
                }
            }).fail(function(data) {
                alert('Failed Get for list servers ' + JSON.stringify(data));
            });
            ServerConfigViewModel.serverList.sort();
        };

        // extend the server name to be all caps
        ServerConfigViewModel.serverName.extend({ uppercase: true });

        // subscribe to changes in the server name
        ServerConfigViewModel.serverName.subscribe(function() {
            ServerConfigViewModel.searchUpdateViewModel.tearDown();
        });

        ServerConfigViewModel.capitalizeServerName = function() {
            ServerConfigViewModel.serverName(ServerConfigViewModel.serverName().toUpperCase());
        };

        ServerConfigViewModel.search = function() {
            ServerConfigViewModel.alertsViewModel.closeAlerts();
            router.navigate('#config/' + ServerConfigViewModel.serverName(), { replace: true, trigger: false });
            ServerConfigViewModel.searchUpdateViewModel.search();
        };

        ServerConfigViewModel.add = function() {
            ServerConfigViewModel.alertsViewModel.closeAlerts();
            if (ServerConfigViewModel.serverList().indexOf(ServerConfigViewModel.serverName()) >= 0) {
                AlertsViewModel.displayError('Node ' + ServerConfigViewModel.serverName() + ' already exists!');
            }
            else if (ServerConfigViewModel.serverName() === '') {
                AlertsViewModel.displayError('You must enter a server name!');
            }
            else {
                ServerConfigViewModel.serverList().push(ServerConfigViewModel.serverName());
                ServerConfigViewModel.searchUpdateViewModel.setDefault();
            }
        };

        ServerConfigViewModel.clearPage = function() {
            ServerConfigViewModel.serverName('');
            ServerConfigViewModel.searchUpdateViewModel.tearDown();
            ServerConfigViewModel.alertsViewModel.closeAlerts();
        };

        ServerConfigViewModel.keyPressed = function(data, event) {
            if (event.keyCode === 13) {
                ServerConfigViewModel.search();
            }
            return true;
        };

        ServerConfigViewModel.getAllServerNames();

        return ServerConfigViewModel;

    });
