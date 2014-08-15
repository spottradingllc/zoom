function AndPredicate() {
    this.predType = "and";
    this.predicates = ko.observableArray();

    // add two predicates by default
    this.predicates.push(new Predicate());
    this.predicates.push(new Predicate());

    this.addPredicate = function() {
        this.predicates.push(new Predicate());
    };

    this.createPredicateXML = function() {
        var XML = "";
        var header = ["<Predicate type='and'>",
                      "<Operands>"].join('\n');
        header = header.replace(/(\r\n|\n|\r)/gm,"");
        XML = XML.concat(header);

        for (var i = 0; i < this.predicates().length; i++) {
            XML = XML.concat(this.predicates()[i].createPredicateXML());
        }

        var footer = "</Operands></Predicate>";
        XML = XML.concat(footer);

        return XML;
    };
}