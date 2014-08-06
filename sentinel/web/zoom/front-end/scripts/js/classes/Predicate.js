function Predicate() {
    this.predType = ko.observable("");
    this.interval = ko.observable("");
    this.command = ko.observable("");
    this.path = ko.observable("");

    this.createPredicateXML = function() {
        var XML = ["<Predicate type='" + this.predType() + "' ",
                   "interval='" + this.interval() + "' ",
                   "command='" + this.command() + "' ",
                   "path='" + this.path() +"'>",
                   "</Predicate>"].join('\n');
        XML = XML.replace(/(\r\n|\n|\r)/gm,"");

        return XML;
    };
}