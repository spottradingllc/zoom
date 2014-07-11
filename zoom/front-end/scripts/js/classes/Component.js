function Component() {
    this.ID = ko.observable("");
    this.compType = ko.observable("");
    this.script = ko.observable("");
    this.command = ko.observable("");
    this.restartmax = ko.observable("");
    this.registrationpath = ko.observable("");

    this.actions = ko.observableArray();

    this.addAction = function() {
        this.actions.push(new Action());
    };

    this.createComponentXML = function() {
        var XML = "";
        var header = ["<Component id='" + this.ID() + "' ",
                      "type='" + this.compType() + "' ",
                      "script='" + this.script() + "' ",
                      "command='" + this.command() + "' ",
                      "restartmax='" + this.restartmax() + "' ",
                      "registrationpath='" + this.registrationpath() + "'>"].join('\n');
        header = header.replace(/(\r\n|\n|\r)/gm,"");
        XML = XML.concat(header);

        // create XML for actions
        var actionsHeader = "<Actions>";
        XML = XML.concat(actionsHeader);
        for (var i = 0; i < this.actions().length; i++) {
            XML = XML.concat(this.actions()[i].createActionXML());
        }

        var actionsFooter = "</Actions>";
        XML = XML.concat(actionsFooter);

        var footer = "</Component>";
        XML = XML.concat(footer);

        return XML;
    };
}