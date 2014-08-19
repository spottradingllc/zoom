define(['knockout', 'classes/AndPredicate', 'classes/OrPredicate', 'classes/NotPredicate', 'classes/Predicate'],
function(ko, AndPredicate, OrPredicate, NotPredicate, Predicate){

    var Factory = new Object();
    Factory.newPredicate = function(parent, type){
        if(type == 'and'){
            pred = new AndPredicate(Factory);
        }
        else if(type == 'or'){
            pred = new OrPredicate(Factory);
        }
        else if(type == 'not'){
            pred = new NotPredicate(Factory);
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
