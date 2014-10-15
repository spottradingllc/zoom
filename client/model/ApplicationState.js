define(
    [
        'jquery',
        'knockout',
        'classes/applicationStateArray',
        'model/graphiteModel',
        'model/appInfoModel',
        'model/dependencyModel'
    ],
    function($, ko, ApplicationStateArray, GraphiteModel, AppInfoModel, DependencyModel) {
        return function ApplicationState(data, parent) {
            var self = this;

            self.colors = {
                actionBlue: '#057D9F',
                errorRed: '#CC574F',
                successTrans: '',
                unknownGray: '#F7EEDA',
                warnOrange: '#FFAE2F'
            };

            self.glyphs = {
                runningCheck: 'glyphicon glyphicon-ok-circle',
                stoppedX: 'glyphicon glyphicon-remove-circle',
                unknownQMark: 'glyphicon glyphicon-question-sign',
                thumpsUp: 'glyphicon glyphicon-thumbs-up',
                startingRetweet: 'glyphicon glyphicon-retweet',
                stoppingDown: 'glyphicon glyphicon-arrow-down',
                errorWarning: 'glyphicon glyphicon-warning-sign',
                notifyExclamation: 'glyphicon glyphicon-exclamation-sign',
                filledStar: 'glyphicon glyphicon-star',
                emptyStar: 'glyphicon glyphicon-star-empty',
                modeAuto: 'glyphicon glyphicon-eye-open',
                modeManual: 'glyphicon glyphicon-eye-close'
            };

            self.applicationStatuses = {running: 'running', stopped: 'stopped', unknown: 'unknown'};
            self.errorStates = {ok: 'ok', starting: 'starting', stopping: 'stopping', error: 'error', notify: 'notify', unknown: 'unknown'};

            self.componentId = data.application_name;
            self.configurationPath = data.configuration_path;
            self.applicationStatus = ko.observable(data.application_status);
            self.applicationHost = ko.observable(data.application_host);
            self.triggerTime = ko.observable(data.trigger_time);
            self.completionTime = ko.observable(data.completion_time);
            self.errorState = ko.observable(data.error_state);
            self.mode = ko.observable(data.local_mode);
            self.mtime = Date.now();
            self.graphite = new GraphiteModel(parent.environment.env().toLowerCase(), self.applicationHost(), self.configurationPath);
            self.appInfo = new AppInfoModel(self.configurationPath, parent.login);
            self.dependencyModel = new DependencyModel(parent.applicationStateArray, self);
            self.loginUser = ko.observable(data.login_user);
            self.lastCommand = ko.observable(data.last_command);

            self.applicationStatusClass = ko.computed(function() {
                var ret;
                if (self.applicationStatus().toLowerCase() === self.applicationStatuses.running) {
                    ret = self.glyphs.runningCheck;
                }
                else if (self.applicationStatus().toLowerCase() === self.applicationStatuses.stopped) {
                    ret = self.glyphs.stoppedX;
                }
                else {
                    ret = self.glyphs.unknownQMark;
                }
                // add the cursor-pointer css class so it appears as clickable
                return ret + ' cursor-pointer';
            }, self);

            self.applicationStatusBg = ko.computed(function() {
                if (self.applicationStatus().toLowerCase() === self.applicationStatuses.running) {
                    return self.colors.successTrans;
                }
                else if (self.applicationStatus().toLowerCase() === self.applicationStatuses.stopped) {
                    return self.colors.errorRed;
                }
                else {
                    return self.colors.unknownGray;
                }
            }, self);

            self.modeClass = ko.computed(function() {
                if (self.mode() === parent.globalMode.current()) {
                    return '';
                }
                else if (self.mode() === 'auto') {
                    return self.glyphs.modeAuto;
                }
                else if (self.mode() === 'manual') {
                    return self.glyphs.modeManual;
                }
                else {
                    return self.glyphs.runningCheck;
                }

            });

            self.errorStateClass = ko.computed(function() {
                if (self.errorState() && self.errorState().toLowerCase() === self.errorStates.ok) {
                    return self.glyphs.thumpsUp;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === self.errorStates.starting) {
                    return self.glyphs.startingRetweet;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === self.errorStates.stopping) {
                    return self.glyphs.stoppingDown;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === self.errorStates.error) {
                    return self.glyphs.errorWarning;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === self.errorStates.notify) {
                    return self.glyphs.notifyExclamation;
                }
                else {
                    return self.glyphs.unknownQMark;
                }
            }, self);

            self.errorStateBg = ko.computed(function() {
                if (self.errorState() && self.errorState().toLowerCase() === self.errorStates.ok) {
                    if (self.mode() !== parent.globalMode.current()) {
                        return self.colors.warnOrange;
                    }

                    return self.colors.successTrans;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === self.errorStates.starting) {
                    return self.colors.actionBlue;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === self.errorStates.stopping) {
                    return self.colors.actionBlue;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === self.errorStates.error) {
                    return self.colors.errorRed;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === self.errorStates.notify) {
                    return self.colors.warnOrange;
                }
                else {
                    return self.colors.unknownGray;
                }
            }, self);

            self.triggerTimeTitle = ko.computed(function() {
                return 'Last Command: ' + self.lastCommand() + '\nTriggered by: ' + self.loginUser();
            });

            // Creates group for sending commands
            self.groupControlStar = ko.computed(function() {
                if (parent.groupControl.indexOf(self) === -1) {
                    return self.glyphs.emptyStar;
                }
                else {
                    return self.glyphs.filledStar;
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

            self.onControlAgentError = function() {
                alert('Error controlling agent.');
            };


            self.deleteRow = function() {
                // delete an application row on the web page
                // parses the config and deletes the component with a matching id
                // deletes the path in zookeeper matching the configurationPath
                if (self.dependencyModel.requiredBy().length > 0) {
                    var message = 'Someone depends on this! ';
                    ko.utils.arrayForEach(self.dependencyModel.requiredBy(), function(applicationState) {
                        message = message + '\n' + applicationState.configurationPath;
                    });
                    alert(message);
                }
                else if (self.applicationHost() === '') {
                    if (confirm(self.configurationPath + ' has no Host listed, this delete is mostly artificial')) {
                        ApplicationStateArray.remove(self);
                    }
                }
                else {

                    if (confirm(self.configurationPath + ' will be deleted, and its dependency configuration lost, continue?')) {

                        var dict = {
                            'loginName': parent.login.elements.username(),
                            'delete': self.configurationPath
                        };

                        var zkDeleted = true;

                        $.post('/api/delete/', dict)
                            .fail(function(data) {
                                zkDeleted = false;
                            });

                        if (zkDeleted) {
                            $.get('/api/config/' + self.applicationHost(),
                                function(data) {
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
                                            alert('Didn\'t find component ' + self.configurationPath + ' in' + self.applicationHost() + '\'s config');
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
                                                    type: 'PUT',
                                                    data: JSON.stringify(params)
                                                }).fail(function(data) {
                                                    alert('Failed putting Config ' + JSON.stringify(data));
                                                });
                                        }
                                        else {
                                            alert('Multiple components matched ' + self.configurationPath + ' in ' + self.applicationHost() + '\'s config, not acting');
                                        }
                                    }
                                    else {
                                        alert('no data for host ' + self.applicationHost());
                                    }
                                })
                                .fail(function(data) {
                                    alert('Failed Get Config ' + JSON.stringify(data));
                                });
                        }
                        else {
                            alert('Error deleting path: ' + JSON.stringify(data.responseText));
                        }

                    }
                }

            };
        };
    });

