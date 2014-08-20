define(['knockout'],
function(ko){
return function NotPredicate(Factory) {
    var self = this;
    self.expanded = ko.observable(false);
    self.predType = "not";
    self.title = "NOT"
    self.predicates = ko.observableArray();

    self.addPredicate = function(type) {
        var pred = Factory.newPredicate(self,type);
        self.predicates.push(pred);
    };


    self.error = ko.computed(function(){
        if(self.predicates().length != 1){
            return "NOT needs a predicate";
        }
        else{
            return "";
        }
    });

    self.remove = function(){
        self.parent.predicates.remove(self);
    }

    self.expandUp = function(){
        self.expanded(true);
        self.parent.expandUp();
    }
    self.validate = function() {
        var valid = true;
        if(self.error() != ""){
            valid = false;
        }
        for (var i = 0; i < self.predicates().length; i++) {
            if(!self.predicates()[i].validate()){
                valid = false;
            }
        }
        return valid;
    }

    self.createPredicateXML = function() {
        var XML = "";
        var header = "<Predicate type='not'>";
        XML = XML.concat(header);

        for (var i = 0; i < self.predicates().length; i++) {
            XML = XML.concat(self.predicates()[i].createPredicateXML());
        }

        var footer = "</Predicate>";
        XML = XML.concat(footer);

        return XML;
    };

    self.loadXML = function(node){
        self.predicates.removeAll();
        var child = Factory.firstChild(node);
        while(child != null){
            var type = child.getAttribute('type');
            var predicate = Factory.newPredicate(self,type);
            predicate.loadXML(child);
            self.predicates.push(predicate);
            child = Factory.nextChild(child);
        }
        
    }
}});
