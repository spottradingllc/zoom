define(['knockout', './Action'],
function(ko, Action){
return function Component(parent) {
    var self = this;
    self.expanded = ko.observable(true);
    self.ID = ko.observable(null);
    self.compType = ko.observable(null);
    self.script = ko.observable(null);
    self.command = ko.observable(null);
    self.restartmax = ko.observable(null);
    self.registrationpath = ko.observable(null);

    self.actions = ko.observableArray();

    self.addAction = function() {
        self.actions.push(new Action(self));
    };

    self.remove = function(){
        parent.components.remove(self);
    }

    self.expandUp = function(){
        self.expanded(true);
    }

    self.validate = function() {
        var valid = true;
        if(self.ID() == null ||
           self.script() == null ||
           self.compType() == null ){
            self.expandUp();
            valid = false
        }
        for (var i = 0; i < self.actions().length; i++) {
            if(!self.actions()[i].validate()){
                valid = false;
            }
        }
        return valid;
    }

    self.createComponentXML = function() {
        var XML = "<Component ";
        XML = XML.concat("id='"+self.ID()+"' ");
        XML = XML.concat("type='"+self.compType()+"' ");
        XML = XML.concat("script='"+self.script()+"' ");

        if(self.registrationpath() != null){
            XML = XML.concat("registrationpath='"+self.registrationpath()+"' ");
        }

        if(self.command() != null){
            XML = XML.concat("command='"+self.command()+"' ");
        }
        if(self.restartmax() != null){
            XML = XML.concat("restartmax='"+self.restartmax()+"' ");
        }
        XML = XML.concat(">");

        // create XML for actions
        var actionsHeader = "<Actions>";
        XML = XML.concat(actionsHeader);
        for (var i = 0; i < self.actions().length; i++) {
            XML = XML.concat(self.actions()[i].createActionXML());
        }

        var actionsFooter = "</Actions>";
        XML = XML.concat(actionsFooter);

        var footer = "</Component>";
        XML = XML.concat(footer);

        return XML;
    };

    self.loadXML = function(node){
        self.ID(node.getAttribute('id'))
        self.compType(node.getAttribute('type'))
        self.script(node.getAttribute('script'))
        self.command(node.getAttribute('command'))
        self.restartmax(node.getAttribute('restartmax'))
        self.registrationpath(node.getAttribute('registrationpath'))

        self.actions.removeAll()
        var actions = node.getElementsByTagName("Action");
        for(var i = 0; i < actions.length; i++){
            var action = new Action(self);
            action.loadXML(actions[i]);
            self.actions.push(action);
        }

    };
}});
