function NotPredicate() {
    this.predType = "not";
    this.predicate = ko.observable(new Predicate());

    this.createPredicateXML = function() {
        var XML = "";
        var header = "<Predicate type='not'>";
        XML = XML.concat(header);

        XML = XML.concat(this.predicate().createPredicateXML());

        var footer = "</Predicate>";
        XML = XML.concat(footer);

        return XML;
    };
}