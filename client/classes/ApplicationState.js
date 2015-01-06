define(
    [
        'jquery',
        'knockout',
        'classes/applicationStateArray',
        'model/graphiteModel',
        'model/appInfoModel',
        'model/dependencyModel',
        'model/constants'
    ],
    function($, ko, ApplicationStateArray, GraphiteModel, AppInfoModel, DependencyModel, constants) {
        return function ApplicationState(data, parent) {
            var self = this;

            self.componentId = data.application_name;
            self.configurationPath = data.configuration_path;
            self.applicationStatus = ko.observable(data.application_status);
            self.applicationHost = ko.observable(data.application_host);
            self.applicationHostShort = ko.computed(function() {
                return self.applicationHost().split('.')[0].toUpperCase();
            });
            self.triggerTime = ko.observable(data.trigger_time);
            self.completionTime = ko.observable(data.completion_time);
            self.errorState = ko.observable(data.error_state);
            self.mode = ko.observable(data.local_mode);
            self.mtime = Date.now();
            self.platform = ko.observable(data.platform);
            self.graphite = new GraphiteModel(parent.environment.env().toLowerCase(), self.applicationHostShort(), self.configurationPath, self.platform());
            self.appInfo = new AppInfoModel(self.configurationPath, parent.login);
            self.dependencyModel = new DependencyModel(parent.applicationStateArray, self);
            self.loginUser = ko.observable(data.login_user);
            self.lastCommand = ko.observable(data.last_command);
            self.grayed = ko.observable(data.grayed);
            self.pdDisabled = ko.observable(data.pd_disabled);


            self.applicationStatusClass = ko.computed(function() {
                var ret;

                if (self.applicationStatus().toLowerCase() === constants.applicationStatuses.running) {
                    ret = constants.glyphs.runningCheck;
                }
                else if (self.applicationStatus().toLowerCase() === constants.applicationStatuses.stopped) {
                    ret = constants.glyphs.stoppedX;
                }
                else {
                    ret = constants.glyphs.unknownQMark;
                }
                // add the cursor-pointer css class so it appears as clickable
                return ret + ' cursor-pointer';
            }, self);

            self.applicationStatusBg = ko.computed(function() {
                if (self.grayed()) { return constants.colors.disabledGray; }
                else if (self.applicationStatus().toLowerCase() === constants.applicationStatuses.running) {
                    return constants.colors.successTrans;
                }
                else if (self.applicationStatus().toLowerCase() === constants.applicationStatuses.stopped) {
                    return constants.colors.errorRed;
                }
                else {
                    return constants.colors.unknownGray;
                }
            }, self);

            self.modeClass = ko.computed(function() {
                if (self.mode() === parent.globalMode.current()) {
                    return '';
                }
                else if (self.mode() === 'auto') {
                    return constants.glyphs.modeAuto;
                }
                else if (self.mode() === 'manual') {
                    return constants.glyphs.modeManual;
                }
                else {
                    return constants.glyphs.runningCheck;
                }

            });

            self.errorStateClass = ko.computed(function() {
                if (self.grayed()) { return constants.glyphs.grayed; }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.ok) {
                    return constants.glyphs.thumpsUp;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.starting) {
                    return constants.glyphs.startingRetweet;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.stopping) {
                    return constants.glyphs.stoppingDown;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.error) {
                    return constants.glyphs.errorWarning;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.notify) {
                    return constants.glyphs.notifyExclamation;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.configErr) {
                    return constants.glyphs.configErr;
                }
                else {
                    return constants.glyphs.unknownQMark;
                }
            }, self);

            self.pdDisabledClass = ko.computed(function() {
                if (self.pdDisabled()) { return constants.glyphs.pdWrench; }
                else { return ""; }
            });

            self.errorStateBg = ko.computed(function() {
                if (self.grayed()) { return constants.colors.disabledGray; }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.ok) {
                    if (self.mode() !== parent.globalMode.current()) {
                        return constants.colors.warnOrange;
                    }

                    return constants.colors.successTrans;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.starting) {
                    return constants.colors.actionBlue;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.stopping) {
                    return constants.colors.actionBlue;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.error) {
                    return constants.colors.errorRed;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.notify) {
                    return constants.colors.warnOrange;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.configErr) {
                    return constants.colors.configErrPink;
                }
                else {
                    return constants.colors.unknownGray;
                }
            }, self);

            self.triggerTimeTitle = ko.computed(function() {
                return 'Last Command: ' + self.lastCommand() + '\nTriggered by: ' + self.loginUser();
            });

            // Creates group for sending commands
            self.groupControlStar = ko.computed(function() {
                if (parent.groupControl.indexOf(self) === -1) {
                    return constants.glyphs.emptyStar;
                }
                else {
                    return constants.glyphs.filledStar;
                }
            });

            self.groupControlStar.extend({rateLimit: 10});

            self.toggleGroupControl = function() {
                if (parent.groupControl.indexOf(self) === -1) {
                    parent.groupControl.push(self);
                }
                else {
                    parent.groupControl.remove(self);
                }
            };

            self.toggleGrayed = function() {
                var dict = {
                    'key': 'grayed',
                    'value': !self.grayed()
                };
                $.post('/api/application/states' + self.configurationPath, JSON.stringify(dict))
                    .fail(function(data) { swal('Failure Toggling grayed ', JSON.stringify(data)); });
            };

            self.togglePDDisabled = function() {
                var method;
                if (self.pdDisabled()) {
                    method = 'DELETE';
                }
                else {
                    method = 'POST';
                }

                $.ajax({
                    url: '/api/pagerduty/exceptions/' + self.componentId,
                    type: method,
                    success: function(data) { self.pdDisabled(!self.pdDisabled()); },
                    error: function(data) { swal('Failure Toggling pdDisabled ', JSON.stringify(data.responseText)); }
                });

            };

            self.onControlAgentError = function() {
                swal('Error controlling agent.');
            };

            var deleteFromZK = function() {
                // delete path from Zookeeper
                var dict = {
                    'loginName': parent.login.elements.username(),
                    'delete': self.configurationPath
                };

                $.ajax({
                    url: '/api/delete/',
                    async: false,
                    data: dict,
                    type: 'POST',
                    error: function(data) {
                        swal('Error deleting path.', JSON.stringify(data.responseText), 'error');
                    }
                });
            };

            var deleteFromConfig = function() {
                // try to remove component from server config
                $.get('/api/config/' + self.applicationHost(), function(data) {
                    if (data !== 'Node does not exist.') {
                        var parser = new DOMParser();
                        var xmlDoc = parser.parseFromString(data, 'text/xml');
                        var found = 0;
                        var x = xmlDoc.getElementsByTagName('Component');
                        for (var i = 0; i < x.length; i++) {
                            var id = x[i].getAttribute('id');
                            if (self.configurationPath.indexOf(id, self.configurationPath.length - id.length) !== -1) {
                                x[i].parentNode.removeChild(x[i]);
                                found = found + 1;
                                i = i - 1;
                            }
                        }

                        if (found === 0) {
                            swal('Missing component', 'Didn\'t find component ' + self.configurationPath + ' in ' +
                                self.applicationHost() + '\'s config. Simply deleted the row.');
                        }
                        else if (found === 1) {
                            var oSerializer = new XMLSerializer();
                            var sXML = oSerializer.serializeToString(xmlDoc);
                            var params = {
                                'XML': sXML,
                                'serverName': self.applicationHost()
                            };
                            $.ajax(
                                {
                                    url: '/api/config/' + self.applicationHost(),
                                    async: false,
                                    type: 'PUT',
                                    data: JSON.stringify(params),
                                    error: function(data) {
                                        swal('Failed putting Config', JSON.stringify(data), 'error');
                                    }
                                });
                        }
                        else {
                            swal('Multiple matches', 'Multiple components matched ' + self.configurationPath +
                                ' in ' + self.applicationHost() + '\'s config. Not deleting.');
                        }
                    }
                    else {
                        // host config did not exist. No Component to remove
                        swal('No data', 'No data for host ' + self.applicationHost());
                    }
                }).fail(function(data) {
                    swal('Failed Get Config', JSON.stringify(data));
                });
            };


            self.deleteRow = function() {
                // delete an application row on the web page
                // parses the config and deletes the component with a matching id
                // deletes the path in zookeeper matching the configurationPath
                if (self.dependencyModel.requiredBy().length > 0) {
                    var message = 'Are you sure?\n';
                    ko.utils.arrayForEach(self.dependencyModel.requiredBy(), function(applicationState) {
                        message = message + applicationState.configurationPath + '\n';
                    });
                    swal({
                        title: 'Someone depends on this!',
                        text: message,
                        type: 'warning',
                        showCancelButton: true,
                        confirmButtonText: 'Yes, delete it!',
                        cancelButtonText: 'It\'s a trap, abort!',
                        closeOnConfirm: false,
                        closeOnCancel: false
                    }, function(isConfirm) {
                        if (isConfirm) {
                            deleteFromConfig();
                            // give the agent time to clean up the old config
                            setTimeout(function() { deleteFromZK(); }, 2000);
                            swal('Deleting', 'Give us a few seconds to clean up.');
                        }
                        else {
                            swal('Cancelled', 'Nothing was deleted.');
                        }
                    });
                }
                else if (self.applicationHost() === '') {
                    swal({
                        title: 'Are you sure?',
                        text: self.configurationPath + ' has no Host listed, this delete is mostly aesthetic. Continue?',
                        type: 'warning',
                        showCancelButton: true,
                        confirmButtonText: 'Yes, delete it!',
                        cancelButtonText: 'It\'s a trap, abort!',
                        closeOnConfirm: false,
                        closeOnCancel: false
                    }, function(isConfirm) {
                        if (isConfirm) {
                            ApplicationStateArray.remove(self);
                        }
                        else {
                            swal('Cancelled', 'Nothing was deleted.');
                        }
                    });
                }
                else {
                    swal({
                        title: 'Are you sure?',
                        text: self.configurationPath + ' will be deleted, and its dependency configuration lost. Continue?',
                        type: 'warning',
                        showCancelButton: true,
                        confirmButtonText: 'Yes, delete it!',
                        cancelButtonText: 'It\'s a trap, abort!',
                        closeOnConfirm: false,
                        closeOnCancel: false
                    }, function(isConfirm) {
                        if (isConfirm) {
                            deleteFromConfig();
                            // give the agent time to clean up the old config
                            setTimeout(function() { deleteFromZK(); }, 2000);
                            swal('Deleting', 'Give us a few seconds to clean up.');
                        }
                        else {
                            swal('Cancelled', 'Nothing was deleted.');
                        }
                    });
                }
            };
        };
    });

