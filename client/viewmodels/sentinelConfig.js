define(
    [
        'jquery',
        'knockout',
        'plugins/router',
        'viewmodels/sentinelConfig/alertsViewModel',
        'viewmodels/sentinelConfig/searchUpdateViewModel'
    ],
    function($, ko, router, AlertsViewModel, SearchUpdateViewModel) {

        var SentinelConfigViewModel = {
            // view models
            alertsViewModel: AlertsViewModel,

            // variables
            serverList: ko.observableArray(),
            serverName: ko.observable('')
        };

        SentinelConfigViewModel.activate = function(server) {
            if (server !== null) {
                SentinelConfigViewModel.serverName(server);
                SentinelConfigViewModel.search();
            }
        };

        SentinelConfigViewModel.searchUpdateViewModel = new SearchUpdateViewModel(SentinelConfigViewModel);

        SentinelConfigViewModel.getAllServerNames = function() {
            $.getJSON('/api/config/list_servers/', function(data) {
                SentinelConfigViewModel.serverList.removeAll();
                for (var i = 0; i < data.length; i++) {
                    SentinelConfigViewModel.serverList.push(data[i]);
                }
                SentinelConfigViewModel.serverList.sort();
            }).fail(function(data) {
                swal('Failed Get for list servers',JSON.stringify(data), 'error');
            });
        };

        SentinelConfigViewModel.serverOptions = ko.computed(function() {

            if (SentinelConfigViewModel.serverList() === []) { return []; }

            if (SentinelConfigViewModel.serverName() === null || SentinelConfigViewModel.serverName() === '') {
                return SentinelConfigViewModel.serverList();
            }

            return ko.utils.arrayFilter(SentinelConfigViewModel.serverList(), function(path) {
                return path.toLowerCase().indexOf(SentinelConfigViewModel.serverName().toLowerCase()) !== -1;
            });
        });

        // subscribe to changes in the server name
        SentinelConfigViewModel.serverName.subscribe(function() {
            SentinelConfigViewModel.searchUpdateViewModel.tearDown();
        });

        SentinelConfigViewModel.capitalizeServerName = function() {
            SentinelConfigViewModel.serverName(SentinelConfigViewModel.serverName().toUpperCase());
        };

        SentinelConfigViewModel.search = function() {
            SentinelConfigViewModel.alertsViewModel.closeAlerts();
            router.navigate('#config/' + SentinelConfigViewModel.serverName(), { replace: true, trigger: false });
            SentinelConfigViewModel.searchUpdateViewModel.search();
        };

        SentinelConfigViewModel.add = function() {
            SentinelConfigViewModel.alertsViewModel.closeAlerts();
            if (SentinelConfigViewModel.serverList().indexOf(SentinelConfigViewModel.serverName()) >= 0) {
                AlertsViewModel.displayError('Node ' + SentinelConfigViewModel.serverName() + ' already exists!');
            }
            else if (SentinelConfigViewModel.serverName() === '') {
                AlertsViewModel.displayError('You must enter a server name!');
            }
            else {
                SentinelConfigViewModel.serverList().push(SentinelConfigViewModel.serverName());
                SentinelConfigViewModel.searchUpdateViewModel.setDefault();
            }
        };

        SentinelConfigViewModel.clearPage = function() {
            SentinelConfigViewModel.serverName('');
            SentinelConfigViewModel.searchUpdateViewModel.tearDown();
            SentinelConfigViewModel.alertsViewModel.closeAlerts();
        };

        SentinelConfigViewModel.keyPressed = function(data, event) {
            if (event.keyCode === 13) {
                SentinelConfigViewModel.search();
            }
            return true;
        };

        SentinelConfigViewModel.getAllServerNames();

        return SentinelConfigViewModel;

    });
