define(['knockout', './alertsViewModel', 'classes/Component', 'vkbeautify'],
function(ko, AlertsViewModel, Component){

return function TreeViewModel(ServerConfigViewModel){
    var self = this;
    self.components = ko.observableArray();
    self.visible = ko.observable(false);
    self.tearDown = function(){
        self.components.removeAll();
        self.hide();
    }

    self.addComponent = function(){
        self.components.push( new Component(self));
    }

    self.validate = function(){
        var valid = true;
        for (var i = 0; i < this.components().length; i++) {
            if(!self.components()[i].validate()){
                valid = false;
            }
        }

        if(!valid){
            alert("Red areas indicate errors");
        }

        return valid
    }

    self.createXML = function() {
        var XML = "";
        var header = ['<?xml version="1.0" encoding="UTF-8"?>',
                      '<Application>',
                      '<Automation>'].join('\n');
        header = header.replace(/(\r\n|\n|\r)/gm,"");
        XML = XML.concat(header);

        if(self.validate()){
            for (var i = 0; i < this.components().length; i++) {
                XML = XML.concat(this.components()[i].createComponentXML());
            }

            var actionsFooter = "</Automation>";
            XML = XML.concat(actionsFooter);

            var footer = "</Application>";
            XML = XML.concat(footer);

            console.log(vkbeautify.xml(XML));
            ServerConfigViewModel.searchUpdateViewModel.serverConfig(vkbeautify.xml(XML))
        }
    };

    self.loadXML = function() {
        var data = ServerConfigViewModel.searchUpdateViewModel.serverConfig()
        self.components.removeAll()
        parser=new DOMParser();
        xmlDoc=parser.parseFromString(data, "text/xml");
        var comps = xmlDoc.getElementsByTagName("Component");
        for(var i = 0; i < comps.length; i++){
            var comp = new Component(self);
            comp.loadXML(comps[i]);
            self.components.push(comp);
        }
        self.show()
    }

    self.hide = function() {
        self.visible(false);
    };

    self.show = function() {
        self.visible(true);
    };
}});
