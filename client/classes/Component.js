define(['knockout', './Action', 'model/constants', 'bindings/tooltip'],
    function(ko, Action, constants) {
        return function Component(parent) {
            var self = this;
            self.TreeViewModel = parent;
            self.expanded = ko.observable(true);
            self.ID = ko.observable(null);
            self.compType = ko.observable(null);
            self.script = ko.observable(null);
            self.startCommand = ko.observable(null);
            self.stopCommand = ko.observable(null);
            self.statusCommand = ko.observable(null);
            self.postStopSleep = ko.observable(null)
            self.restartmax = ko.observable(null);
            self.restartOnCrash = ko.observable(null);
            self.registrationpath = ko.observable(null);
            self.pdServiceName = ko.observable(null);
            self.pagerdutyService = ko.observable(null);
            self.actions = ko.observableArray();

            self.pdNameLookup = ko.computed(function() {
                if (self.pagerdutyService()) {
                    var ret = '';
                    var dict = self.TreeViewModel.pagerDutyServices;
                    for (var prop in dict) {
                        if(dict.hasOwnProperty(prop)) {
                            if (dict[prop] === self.pagerdutyService()) {
                                ret = prop;
                            }
                        }
                    }
                    self.pdServiceName(ret);
                }
            });

            self.setPDService = function(name) {
                self.pdServiceName(name);
                self.pagerdutyService(self.TreeViewModel.pagerDutyServices[name])
            };

            self.addAction = function() {
                self.expanded(true);
                self.actions.unshift(new Action(self));  // add to front of array
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

            var sanitizeXML = function(someString) {
                var comEdit1 = someString.replace(/"/g, '&quot;');
                var comEdit2 = comEdit1.replace(/'/g, '&apos;');
                var comEdit3 = comEdit2.replace(/</g, '&lt;');
                var comEdit4 = comEdit3.replace(/>/g, '&gt;');
                return comEdit4.replace(/&(?=[a-z_0-9]+=)/g, '&amp;');
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
                if (checkNull(self.startCommand())) {
                    // replace xml entities
                    self.startCommand(sanitizeXML(self.startCommand()));
                    XML = XML.concat('start_cmd="' + self.startCommand() + '" ');
                }
                if (checkNull(self.stopCommand())) {
                    // replace xml entities
                    self.stopCommand(sanitizeXML(self.stopCommand()));
                    XML = XML.concat('stop_cmd="' + self.stopCommand() + '" ');
                }
                if (checkNull(self.statusCommand())) {
                    // replace xml entities
                    self.statusCommand(sanitizeXML(self.statusCommand()));
                    XML = XML.concat('status_cmd="' + self.statusCommand() + '" ');
                }
                if (checkNull(self.restartmax())) {
                    XML = XML.concat('restartmax="' + self.restartmax() + '" ');
                }
                if (checkNull(self.restartOnCrash())) {
                    XML = XML.concat('restart_on_crash="' + self.restartOnCrash() + '" ');
                }
                if (checkNull(self.pagerdutyService())) {
                    XML = XML.concat('pagerduty_service="' + self.pagerdutyService() + '" ');
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
                self.startCommand(node.getAttribute('start_cmd'));
                self.stopCommand(node.getAttribute('stop_cmd'));
                self.statusCommand(node.getAttribute('status_cmd'));
                self.postStopSleep(node.getAttribute('post_stop_sleep'));
                self.restartmax(node.getAttribute('restartmax'));
                self.restartOnCrash(node.getAttribute('restart_on_crash'));
                self.registrationpath(node.getAttribute('registrationpath'));
                self.pagerdutyService(node.getAttribute('pagerduty_service'));

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
