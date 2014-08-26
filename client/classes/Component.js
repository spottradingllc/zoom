define(['knockout', './Action', './applicationStates'],
function(ko, Action, ApplicationStates){
return function Component(parent) {
    var self = this;
    self.expanded = ko.observable(true);
    self.ID = ko.observable(null);
    self.compType = ko.observable(null);
    self.script = ko.observable(null);
    self.command = ko.observable(null);
    self.restartmax = ko.observable(null);
    self.registrationpath = ko.observable(null);
    self.appPath = "/spot/software/state/application/"

    self.actions = ko.observableArray();

    self.error = ko.computed(function(){
        if(self.actions().length < 1){
            return "You have to have an Action";
        }
        else{
            return "";
        }
    });

    self.addAction = function() {
        self.expanded(true);
        self.actions.push(new Action(self));
    };

    self.remove = function(){
        parent.components.remove(self);
    }

    self.IDOptions = ko.computed(function(){

        var paths =  ko.utils.arrayMap(ApplicationStates(), function(state){
            return state.configurationPath.replace(self.appPath, "");
        }); 

        paths.sort();

        if(self.ID() == null) return paths;

        return ko.utils.arrayFilter(paths, function(path){
            return (path.slice(0, self.ID().length) == self.ID()); 
        });
    });


    self.expandUp = function(){
        self.expanded(true);
    }

    self.validate = function() {
        var valid = true;

        if(self.error() != ""){
            valid = false;
        }
        if(self.ID() == null || self.ID() == '' ||
           self.script() == null || self.script() == '' ||
           self.compType() == null || self.compType == ''){
            valid = false
        }
        for (var i = 0; i < self.actions().length; i++) {
            if(!self.actions()[i].validate()){
                valid = false;
            }
        }
        if(!valid){
            self.expandUp();
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
