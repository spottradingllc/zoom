function Action() {
    this.ID = ko.observable("");
    this.staggerpath = ko.observable("");
    this.staggertime = ko.observable("");
    this.allowedinstances = ko.observable("");

    this.predicates = ko.observableArray();

    this.addPredicate = function() {
        this.predicates.push(new Predicate());
    };

    this.addAndPredicate = function() {
        this.predicates.push(new AndPredicate());
    };

    this.addOrPredicate = function() {
        this.predicates.push(new OrPredicate());
    };

    this.addNotPredicate = function() {
        this.predicates.push(new NotPredicate());
    };

    this.createActionXML = function() {
        var XML = "";
        var header = ["<Action id='" + this.ID() + "' ",
                      "staggerpath='" + this.staggerpath() + "' ",
                      "staggertime='" + this.staggertime() + "' ",
                      "allowed_instance='" + this.allowedinstances() + "'>",
                      "<Dependency>"].join('\n');
        header = header.replace(/(\r\n|\n|\r)/gm,"");
        XML = XML.concat(header);

        // create XML for predicates
        for (var i = 0; i < this.predicates().length; i++) {
            XML = XML.concat(this.predicates()[i].createPredicateXML());
        }

        var footer = "</Dependency></Action>";
        XML = XML.concat(footer);

        return XML;
    };
}
