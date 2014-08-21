define(['knockout'],
function(ko){
return function OrPredicate(Factory) {
    var self = this;
    self.expanded = ko.observable(false);
    self.predType = "or";
    self.title = "OR"
    self.predicates = ko.observableArray();

    self.addPredicate = function(type) {
        var pred = Factory.newPredicate(self,type);
        self.expanded(true);
        self.predicates.push(pred);
    };

    self.error = ko.computed(function(){
        if(self.predicates().length < 2){
            return "OR needs two or more predicates";
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

        if(!valid){
            self.expandUp();
        }
        return valid;
    }

    self.createPredicateXML = function() {
        var XML = "";
        var header = ["<Predicate type='or'>",
                      "<Operands>"].join('\n');
        header = header.replace(/(\r\n|\n|\r)/gm,"");
        XML = XML.concat(header);

        for (var i = 0; i < self.predicates().length; i++) {
            XML = XML.concat(self.predicates()[i].createPredicateXML());
        }

        var footer = "</Operands></Predicate>";
        XML = XML.concat(footer);

        return XML;
    };

    self.loadXML = function(node){
        var operands = node.getElementsByTagName("Operands")[0]
        self.predicates.removeAll();
        var child = Factory.firstChild(operands);
        while(child != null){
            var type = child.getAttribute('type');
            var predicate = Factory.newPredicate(self,type);
            predicate.loadXML(child);
            self.predicates.push(predicate);
            child = Factory.nextChild(child);
        }
    }
}});
