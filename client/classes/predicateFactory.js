define(['knockout', 'classes/LogicPredicate', 'classes/Predicate'],
function(ko, LogicPredicate, Predicate){

    var Factory = new Object();
    Factory.newPredicate = function(parent, type){
        if(type == 'and' || type =='or' || type == 'not'){
            pred = new LogicPredicate(Factory, type);
        }
        else{
            pred = new Predicate(Factory);
        }
        pred.parent = parent;
        return pred
    };

    Factory.firstChild = function(node){
        var child = node.firstChild;
        while(child != null && child.nodeType != 1){ 
            child = child.nextSibling;
        }
        return child;
    }

    Factory.nextChild = function(child){
        child = child.nextSibling;
        while(child != null && child.nodeType != 1){
            child = child.nextSibling;
        }
        return child
    }
    return Factory;

});
