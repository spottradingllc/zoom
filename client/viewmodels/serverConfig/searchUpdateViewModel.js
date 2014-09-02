define(['knockout', './alertsViewModel', './treeViewModel', 'vkbeautify'],
function(ko, AlertsViewModel, TreeViewModel){

/******* SEARCH AND UPDATE VIEW MODEL *******/
return function SearchUpdateViewModel(ServerConfigViewModel) {
    var self = this;

    self.serverConfig = ko.observable("");
    self.visible = ko.computed(function(){
        return self.serverConfig() != "";
    });
    self.treeViewModel = new TreeViewModel(self);
    self.parent = ServerConfigViewModel;

    self.search = function() {
        if (ServerConfigViewModel.serverName() == "") {
            AlertsViewModel.displayError("You must enter a server name!");
        }
        else {
            // get XML configuration, catch callback message (allow editing on success)
            $.get("/api/config/" + ServerConfigViewModel.serverName(), function(data) {
                if (data != "Node does not exist.") {
                    self.setXML(data);
                }
                else {
                    AlertsViewModel.displayError("Node " + ServerConfigViewModel.serverName() + " does not exist!");
                    ServerConfigViewModel.serverList.remove(ServerConfigViewModel.serverName());
                }
            }).fail(function(data){
                alert("Failed Get Config " + JSON.stringify(data));
            });
        }
    };

    self.setXML = function(data){
        self.serverConfig(vkbeautify.xml(data));
        self.treeViewModel.loadXML();
    };

    self.pushConfig = function() {
        // post JSON dictionary to server, catch callback message
        // update existing config
        var params = {
            "XML" : ServerConfigViewModel.serverConfig(),
            "serverName" : ServerConfigViewModel.serverName()
        };

        $.ajax({
                url: "/api/config/" + ServerConfigViewModel.serverName(),
                type: 'PUT',
                data: JSON.stringify(params),
                success: function (returnData) {
                    if (returnData == "Node successfully updated.") {
                        AlertsViewModel.displaySuccess("Node " + ServerConfigViewModel.serverName() + " was successfully updated!");
                    }
                    else {
                        AlertsViewModel.displayError(returnData);
                    }
                },
                error: function(jqxhr) {
                    return alert(jqxhr.responseText);
                }
            }
        )
    };

    self.validateXML = function() {
        // parse XML doc and see if it has parsing errors
        var XMLParser = new DOMParser();
        var XMLDoc = XMLParser.parseFromString(self.serverConfig(),"text/xml");

        if (XMLDoc.getElementsByTagName("parsererror").length > 0) {
            var XMLString = new XMLSerializer().serializeToString(XMLDoc.documentElement);
            AlertsViewModel.displayError("Error detected in XML syntax!");
        }
        else if(self.treeViewModel.validate()){
            self.pushConfig();
        }
    };

    self.deleteConfig = function() {
        if (confirm("Please confirm that you want to delete the configuration for " + ServerConfigViewModel.serverName() + " by pressing OK.")) {
            // attempt to delete the server configuration, catch callback message
            $.ajax({
                url: "/api/config/" + ServerConfigViewModel.serverName(),
                type: 'DELETE',
                success: function (data) {
                    if (data == 'Node successfully deleted.') {
                        AlertsViewModel.displaySuccess("Node " + ServerConfigViewModel.serverName() + " was successfully deleted!");
                        ServerConfigViewModel.getAllServerNames();
                    }
               else {
                        AlertsViewModel.displayError(data);
                    }
                }
            })
        }
    };

    self.editedConfig = function() {
        var serverConfigDiv = document.getElementsByName("server-config")[0];
        var newConfig = serverConfigDiv.textContent;

        self.setXML(newConfig);
    };

    self.closeAlerts = function() {
        AlertsViewModel.closeAlerts();
    };

    self.tearDown = function() {
        self.serverConfig("");
    };

    self.setDefault = function(){
        // TODO: Move this string to its own file?
        self.setXML('<?xml version="1.0" encoding="UTF-8"?> <Application> <Automation> <Component id="" type="application" script="" restartmax="3" allowed_instances="1" registrationpath="" restartoncrash="False"> <Actions> <Action id="start" mode_controlled="True" staggerpath="" staggertime=""> <Dependency> <Predicate type="and"> <Operands> <Predicate type="not"> <Predicate type="ZookeeperNodeExists" path="/spot/software/signal/killall" /></Predicate> <Predicate type="not"> <Predicate type="process" interval="5" /></Predicate> </Operands> </Predicate> </Dependency> </Action> <Action id="stop" mode_controlled="True"> <Dependency> <Predicate type="ZookeeperNodeExists" path="/spot/software/signal/killall" /> </Dependency> </Action> <Action id="register"> <Dependency> <Predicate type="process" interval="5" /> </Dependency> </Action> <Action id="unregister"> <Dependency> <Predicate type="not"> <Predicate type="process" interval="5" /></Predicate> </Dependency> </Action> </Actions> </Component> </Automation> </Application>');
    }
}});
