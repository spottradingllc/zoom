
/******* ADD VIEW MODEL *******/
function AddViewModel() {
    var self = this;

    self.serverComponents = ko.observableArray();
    self.serverXML = ko.observable("");
    self.showXML = ko.observable(false);
    self.visible = ko.observable(false);

    self.add = function() {
        AlertsViewModel.closeAlerts();

        // check if the server name is already in use
        if (ServerConfigViewModel.serverList().indexOf(ServerConfigViewModel.serverName()) >= 0) {
            AlertsViewModel.displayError("Node " + ServerConfigViewModel.serverName() + " already exists!");
            self.hide();
        }
        else if (ServerConfigViewModel.serverName() == ""){
            AlertsViewModel.displayError("You must enter a server name!");
            self.hide();
        }
        else {
            self.show();
        }
    };

    self.addComponent = function() {
        self.serverComponents.push(new Component());
    };

    self.createXML = function() {
        var XML = "";
        var header = '<?xml version="1.0" encoding="UTF-8"?>\
                        <Application>\
                            <Automation>';
        XML = XML.concat(header);

        // build XML string from the inside out
        for (var i = 0; i < self.serverComponents().length; i++) {
            XML = XML.concat(self.serverComponents()[i].createComponentXML());
        }

        var footer = '</Automation></Application>';
        XML = XML.concat(footer);

        self.serverXML(vkbeautify.xml(XML));
        self.showXML(true);
    };

    self.pushConfig = function() {
        // post JSON dictionary to server, catch callback message
        var data = {
            "XML" : self.serverXML(),
            "serverName" : ServerConfigViewModel.serverName()
        };

        $.post("/api/config/" + ServerConfigViewModel.serverName(), data, function(data) {
            if (data == "Node successfully added.") {
                ServerConfigViewModel.getAllServerNames();
                ServerConfigViewModel.search();
                AlertsViewModel.displaySuccess("Node " + ServerConfigViewModel.serverName() + " was successfully added!");
            }
            else {
                AlertsViewModel.displayError(data);
            }
        });
    };

    self.hide = function() {
        self.visible(false);
    };

    self.show = function() {
        self.visible(true);
    };

    self.tearDown = function() {
        self.serverComponents.removeAll();
        self.serverXML("");
        self.showXML(false);
        self.hide();
    };
}