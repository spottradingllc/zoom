define(['knockout',
        'plugins/router',
        'viewmodels/serverConfig/alertsViewModel',
        'viewmodels/serverConfig/treeViewModel',
        'viewmodels/serverConfig/searchUpdateViewModel',
        'vkbeautify',
        'classes/Action',
        'classes/Component',
        'classes/Predicate',
        'classes/NotPredicate',
        'classes/AndPredicate',
        'classes/OrPredicate',
        'bindings/uppercase'],
function(ko, router, AlertsViewModel, TreeViewModel, SearchUpdateViewModel){

    var ServerConfigViewModel = {
        // view models
        alertsViewModel : AlertsViewModel,

        // variables
        serverList : ko.observableArray(),
        serverName : ko.observable("")
    };

    ServerConfigViewModel.activate = function(server){
        if(server != null){
            ServerConfigViewModel.serverName(server);
            ServerConfigViewModel.search();
        }
    };

    ServerConfigViewModel.treeViewModel = new TreeViewModel(ServerConfigViewModel),
    ServerConfigViewModel.searchUpdateViewModel = new SearchUpdateViewModel(ServerConfigViewModel),

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

    // extend the server name to be all caps
    ServerConfigViewModel.serverName.extend({ uppercase: true });

    // subscribe to changes in the server name
    ServerConfigViewModel.serverName.subscribe(function() {
        ServerConfigViewModel.searchUpdateViewModel.hide();
    });

    ServerConfigViewModel.capitalizeServerName = function() {
        ServerConfigViewModel.serverName(ServerConfigViewModel.serverName().toUpperCase());
    };

    ServerConfigViewModel.search = function() {
        router.navigate('#config/' + ServerConfigViewModel.serverName(), { replace: true, trigger: false });
        ServerConfigViewModel.tearDown();
        ServerConfigViewModel.searchUpdateViewModel.search();
    };

    ServerConfigViewModel.add = function() {
        ServerConfigViewModel.tearDown();
        // check if the server name is already in use
        if (ServerConfigViewModel.serverList().indexOf(ServerConfigViewModel.serverName()) >= 0) {
            AlertsViewModel.displayError("Node " + ServerConfigViewModel.serverName() + " already exists!");
        }
        else if (ServerConfigViewModel.serverName() == ""){
            AlertsViewModel.displayError("You must enter a server name!");
        }
        else {
            ServerConfigViewModel.serverList().push(ServerConfigViewModel.serverName());
            ServerConfigViewModel.searchUpdateViewModel.serverConfig(vkbeautify.xml('<?xml version="1.0" encoding="UTF-8"?> <Application> <Automation> <Component id="" type="application" script="" restartmax="3" registrationpath=""> <Actions> <Action id="start" mode_controlled="True" staggerpath="" staggertime="" allowed_instances=""> <Dependency> <Predicate type="and"> <Operands> <Predicate type="not"> <Predicate type="ZookeeperNodeExists" path="/spot/software/signal/killall" /></Predicate> <Predicate type="not"> <Predicate type="process" interval="5" /></Predicate> </Operands> </Predicate> </Dependency> </Action> <Action id="stop" mode_controlled="True"> <Dependency> <Predicate type="ZookeeperNodeExists" path="/spot/software/signal/killall" /> </Dependency> </Action> <Action id="register"> <Dependency> <Predicate type="process" interval="5" /> </Dependency> </Action> <Action id="unregister"> <Dependency> <Predicate type="not"> <Predicate type="process" interval="5" /></Predicate> </Dependency> </Action> </Actions> </Component> </Automation> </Application>'));
            ServerConfigViewModel.searchUpdateViewModel.show();
            ServerConfigViewModel.treeViewModel.show();
        }
    };

    ServerConfigViewModel.clearPage = function() {
        ServerConfigViewModel.tearDown();
        ServerConfigViewModel.serverName("");
    };

    ServerConfigViewModel.serverSelected = function(selection) {
        ServerConfigViewModel.serverName(selection);
        ServerConfigViewModel.search();
    };

    ServerConfigViewModel.tearDown = function() {
        ServerConfigViewModel.searchUpdateViewModel.tearDown();
        ServerConfigViewModel.treeViewModel.tearDown();
        ServerConfigViewModel.alertsViewModel.closeAlerts();
    };

    ServerConfigViewModel.keyPressed = function(data, event) {
        if (event.keyCode == '13'){
            ServerConfigViewModel.search();
        }
        return true;
    };

    ServerConfigViewModel.getAllServerNames();

    return ServerConfigViewModel;

});
