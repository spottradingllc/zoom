define(['knockout', './Action'],
    function(ko, Action) {
        return function Component(parent) {
            var self = this;
            self.TreeViewModel = parent;
            self.expanded = ko.observable(true);
            self.ID = ko.observable(null);
            self.compType = ko.observable(null);
            self.script = ko.observable(null);
            self.command = ko.observable(null);
            self.restartmax = ko.observable(null);
            self.restartoncrash = ko.observable(null);
            self.registrationpath = ko.observable(null);
            // TODO: Pull this from some central location
            self.appPath = '/spot/software/state/application/';

            self.actions = ko.observableArray();

            self.addAction = function() {
                self.expanded(true);
                self.actions.push(new Action(self));
            };

            self.remove = function() {
                self.TreeViewModel.components.remove(self);
                self.TreeViewModel.createXML();
            };

            self.toggleExpanded = function() {
                self.expanded(!self.expanded());
                ko.utils.arrayForEach(self.actions(), function(action) {
                    action.toggleExpanded(self.expanded());
                });
            };

            var checkNull = function(param) {
                return (param !== null && param !== '');
            };

            var getErrors = function() {
                // return only errors related to this object
                var errors = [];

                if (self.actions().length < 1) {
                    errors.push('You should probably add an Action.');
                }
                if (!checkNull(self.ID()) || !checkNull(self.compType())) {
                    errors.push('Component ID and type cannot be null.');
                }
                if (self.compType() === 'job' && !checkNull(self.command()) ) {
                    errors.push('Component command cannot be null for jobs.');
                }
                else if (self.compType() === 'application' && !checkNull(self.script())) {
                    errors.push('Component script is null.');
                }

                return errors;
            };

            self.error = ko.computed(function() {
                var e = getErrors();
                return e.join(', ');
            });

            self.validate = function() {
                // return errors for this object and all child objects
                var allErrors = getErrors();

                ko.utils.arrayForEach(self.actions(), function(action) {
                    allErrors = allErrors.concat(action.validate());
                });

                return allErrors;
            };

            self.createComponentXML = function() {
                var XML = '<Component ';
                XML = XML.concat('id="' + self.ID() + '" ');
                XML = XML.concat('type="' + self.compType() + '" ');

                if (checkNull(self.script())) {
                    XML = XML.concat('script="' + self.script() + '" ');
                }

                if (checkNull(self.registrationpath())) {
                    XML = XML.concat('registrationpath="' + self.registrationpath() + '" ');
                }

                if (checkNull(self.command())) {
                    var command = self.command().replace(/"/g, '&quot;');
                    self.command(command);
                    XML = XML.concat('command="' + self.command() + '" ');
                }
                if (checkNull(self.restartmax())) {
                    XML = XML.concat('restartmax="' + self.restartmax() + '" ');
                }
                if (checkNull(self.restartoncrash())) {
                    XML = XML.concat('restartoncrash="' + self.restartoncrash() + '" ');
                }
                XML = XML.concat('>');

                // create XML for actions
                var actionsHeader = '<Actions>';
                XML = XML.concat(actionsHeader);
                for (var i = 0; i < self.actions().length; i++) {
                    XML = XML.concat(self.actions()[i].createActionXML());
                }

                var actionsFooter = '</Actions>';
                XML = XML.concat(actionsFooter);

                var footer = '</Component>';
                XML = XML.concat(footer);

                return XML;
            };

            self.loadXML = function(node) {
                self.ID(node.getAttribute('id'));
                self.compType(node.getAttribute('type'));
                self.script(node.getAttribute('script'));
                self.command(node.getAttribute('command'));
                self.restartmax(node.getAttribute('restartmax'));
                self.restartoncrash(node.getAttribute('restartoncrash'));
                self.registrationpath(node.getAttribute('registrationpath'));

                self.actions.removeAll();
                var actions = node.getElementsByTagName('Action');
                for (var i = 0; i < actions.length; i++) {
                    var action = new Action(self);
                    action.loadXML(actions[i]);
                    self.actions.push(action);
                }

            };
        };
    });
