define(['knockout',
        'viewmodels/server_config/alertsViewModel',
        'viewmodels/server_config/addViewModel',
        'viewmodels/server_config/searchUpdateViewModel',
        'classes/Action',
        'classes/Component',
        'classes/Predicate',
        'classes/NotPredicate',
        'classes/AndPredicate',
        'classes/OrPredicate'],
function(ko, AlertsViewModel, AddViewModel, SearchUpdateViewModel){

    var ServerConfigViewModel = {
        // view models
        addViewModel : new AddViewModel(),
        alertsViewModel : AlertsViewModel,

        // variables
        serverList : ko.observableArray(),
        serverName : ko.observable("")
    };

    ServerConfigViewModel.searchUpdateViewModel = new SearchUpdateViewModel(ServerConfigViewModel),
    ServerConfigViewModel.addViewModel = new AddViewModel(ServerConfigViewModel),

    ServerConfigViewModel.getAllServerNames = function () {
        $.getJSON("/api/config/list_servers/", function(data) {
            ServerConfigViewModel.serverList.removeAll();
            for (i = 0; i < data.length; i++) {
                ServerConfigViewModel.serverList.push(data[i]);
            }
        }).fail(function(data){
            alert("Failed Get for list servers " + JSON.stringify(data));
        });
        ServerConfigViewModel.serverList.sort();
    };

    // subscribe to changes in the server name
    ServerConfigViewModel.serverName.subscribe(function() {
        ServerConfigViewModel.capitalizeServerName();
        ServerConfigViewModel.searchUpdateViewModel.hide();
        ServerConfigViewModel.addViewModel.hide();
    });

    ServerConfigViewModel.capitalizeServerName = function() {
        ServerConfigViewModel.serverName(ServerConfigViewModel.serverName().toUpperCase());
    };

    ServerConfigViewModel.search = function() {
        ServerConfigViewModel.tearDown();
        ServerConfigViewModel.searchUpdateViewModel.search();
    };

    ServerConfigViewModel.add = function() {
        ServerConfigViewModel.tearDown();
        ServerConfigViewModel.addViewModel.add();
    };

    ServerConfigViewModel.clearPage = function() {
        ServerConfigViewModel.tearDown();
        ServerConfigViewModel.serverName("");
    };

    ServerConfigViewModel.tearDown = function() {
        ServerConfigViewModel.searchUpdateViewModel.tearDown();
        ServerConfigViewModel.addViewModel.tearDown();
        ServerConfigViewModel.alertsViewModel.closeAlerts();
    };

    ServerConfigViewModel.getAllServerNames();

    return ServerConfigViewModel;

});
