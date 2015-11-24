define(['jquery', 'knockout', './alertsViewModel', './treeViewModel', 'model/constants', 'vkbeautify'],
    function($, ko, AlertsViewModel, TreeViewModel, constants) {

        /******* SEARCH AND UPDATE VIEW MODEL *******/
        return function SearchUpdateViewModel(SentinelConfigViewModel) {
            var self = this;

            self.sentinelConfig = ko.observable('');
            self.visible = ko.computed(function() {
                return self.sentinelConfig() !== '';
            });
            self.guiEdit = ko.observable(false);
            self.treeViewModel = new TreeViewModel(self);
            self.parent = SentinelConfigViewModel;

            self.search = function() {
                if (SentinelConfigViewModel.serverName() === '') {
                    AlertsViewModel.displayError('You must enter a server name!');
                }
                else {
                    // get XML configuration, catch callback message (allow editing on success)
                    $.get('/api/v1/config/' + SentinelConfigViewModel.serverName(), function(data) {
                        if (data !== 'Node does not exist.') {
                            self.setXML(data);
                        }
                        else {
                            AlertsViewModel.displayError('Node ' + SentinelConfigViewModel.serverName() + ' does not exist!');
                            SentinelConfigViewModel.serverList.remove(SentinelConfigViewModel.serverName());
                        }
                    }).fail(function(data) {
                        swal('Failed Get Config', data.responseText, 'error');
                    });
                }
            };

            self.setXML = function(data) {
                self.sentinelConfig(vkbeautify.xml(data));
                self.treeViewModel.loadXML();
            };

            self.pushConfig = function() {
                // post JSON dictionary to server, catch callback message
                // update existing config
                swal({
                    title: 'Config Change!',
                    text: 'Are you sure you want to push the configuration for ' + SentinelConfigViewModel.serverName() + '?',
                    type: 'warning',
                    confirmButtonText: 'Push it real good!',
                    confirmButtonColor: constants.colors.confirmgreen,
                    cancelButtonText: 'Cancel',
                    showCancelButton: true,
                    closeOnConfirm: true,
                    closeOnCancel: true,
                    allowOutsideClick: true
                }, function (isConfirm) {
                    if (isConfirm) {
                        var params = {
                            'XML': self.sentinelConfig(),
                            'serverName': SentinelConfigViewModel.serverName()
                        };
                        $.ajax({
                                url: '/api/v1/config/' + SentinelConfigViewModel.serverName(),
                                type: 'PUT',
                                data: JSON.stringify(params),
                                success: function (returnData) {
                                    if (returnData === 'Node successfully updated.') {
                                        AlertsViewModel.displaySuccess('Node ' + SentinelConfigViewModel.serverName() + ' was successfully updated!');
                                    }
                                    else {
                                        AlertsViewModel.displayError(returnData);
                                    }
                                },
                                error: function (jqxhr) {
                                    return alert(jqxhr.responseText);
                                }
                            });
                    }
                })
            };

            self.validateXML = function() {
                // parse XML doc and see if it has parsing errors
                if (self.guiEdit()) {
                    self.treeViewModel.createXML()
                }
                var XMLParser = new DOMParser();
                var XMLDoc = XMLParser.parseFromString(self.sentinelConfig(), 'text/xml');

                if (XMLDoc.getElementsByTagName('parsererror').length > 0) {
                    var XMLString = new XMLSerializer().serializeToString(XMLDoc.documentElement);
                    AlertsViewModel.displayError('Error detected in XML syntax!');
                }
                else if (self.treeViewModel.validate()) {
                    self.pushConfig();
                }
            };

            self.deleteConfig = function() {
                swal({
                    title: 'Config Delete!',
                    text: 'Are you sure you want to delete the configuration for ' + SentinelConfigViewModel.serverName() + '?',
                    type: 'warning',
                    confirmButtonText: 'Delete it!',
                    confirmButtonColor: constants.colors.errorRed,
                    cancelButtonText: 'Cancel',
                    showCancelButton: true,
                    closeOnConfirm: true,
                    closeOnCancel: true,
                    allowOutsideClick: true
                }, function (isConfirm) {
                    if (isConfirm) {
                        // attempt to delete the sentinel configuration, catch callback message
                        $.ajax({
                            url: '/api/v1/config/' + SentinelConfigViewModel.serverName(),
                            type: 'DELETE',
                            success: function (data) {
                                if (data === 'Node successfully deleted.') {
                                    AlertsViewModel.displaySuccess('Node ' + SentinelConfigViewModel.serverName() + ' was successfully deleted!');
                                    SentinelConfigViewModel.getAllServerNames();
                                }
                                else {
                                    AlertsViewModel.displayError(data);
                                }
                            }
                        });
                        self.search();  // get new empty config
                    }
                })
            };

            self.editedConfig = function() {
                var sentinelConfigDiv = document.getElementsByName('server-config')[0];
                var newConfig = sentinelConfigDiv.textContent;

                self.setXML(newConfig);
            };

            self.toggleGuiEdit = function() {
                if (self.guiEdit()) {
                    self.treeViewModel.createXML()
                }
                else {
                    self.editedConfig()
                }

                self.guiEdit(!self.guiEdit());
            };

            self.closeAlerts = function() {
                AlertsViewModel.closeAlerts();
            };

            self.tearDown = function() {
                self.sentinelConfig('');
            };

            self.setDefault = function() {
                // TODO: Move this string to its own file?
                self.setXML('<?xml version="1.0" encoding="UTF-8"?><Application><Automation></Automation></Application>');
                self.treeViewModel.addComponent();
            };
        };
    });
