define(
    [
        'knockout',
        'service',
        'jquery'
    ],
    function(ko, service, $) {
        return function pillarApiModel(pillarModel) {
            var self = this;
            var pillarURI = "api/pillar/";

            // Updates data for a node - either the entire node or adding a project
            self.api_post_json = function(_assoc, update_salt, array_to_update, data_type, project){
                var update_phrase = "";
                if (data_type === 'project') {
                    update_phrase = "Created project " + pillarModel.new_project();
                }
                else if (data_type === 'wholeTable') {
                    update_phrase = "Updated pillar: " + _assoc.pillar();
                }

                var _projdata = {
                    "minion": _assoc.name,
                    "data": _assoc.edit_pillar(),
                    "username": pillarModel.login.elements.username(),
                    "update_phrase": update_phrase
                };

                $.ajax({
                    type: "POST",
                    url: pillarURI,
                    data: JSON.stringify(_projdata),
                    dataType: 'json'
                })
                    .fail(function(data) {
                        swal("Error", "The data failed to update. Error message: " + data, 'error');
                    })
                    .success(function(data) {
                        self.updateChecked();

                        if (update_salt) {
                            pillarModel.saltModel.updateMinion(array_to_update, 'update', data_type, project);
                        }
                    });
            };

            // only used for node creation
            self.api_post = function(node) {
                var uri = pillarURI + node;
                var _postdata = {
                    "username": pillarModel.login.elements.username()
                };

                $.ajax({
                    url: uri,
                    data: JSON.stringify(_postdata),
                    type: "POST",
                    dataType: 'json'
                })
                    .fail(function(data) {
                        swal("failed to create", JSON.stringify(data), 'error');
                    })
                    .done(function(data) {
                        var singleItem = "";
                        singleItem = node;
                        pillarModel.saltModel.updateMinion(singleItem, 'postCreate', 'node', null);
                        self.loadServers();
                    });
            };

            // Deletes either projects or keys from a node.
            self.api_delete = function(level_to_delete, _proj, key) {
                var num_left = _proj.hasProject.length;
                var del_phrase = "";
                _proj.hasProject.forEach(function(_assoc) {
                    var uri = pillarURI + _assoc.name;
                    if (level_to_delete === "project") {
                        uri += "/" + _proj.proj_name;
                        del_phrase = "Deleted project: " + _proj.proj_name;
                    }
                    else if (level_to_delete === "key") {
                        uri += "/" + _proj.proj_name;
                        uri += "/" + key;
                        del_phrase = "Deleted key: " + key;
                    }

                    var _deldata = {
                        "username": pillarModel.login.elements.username(),
                        "del_phrase": del_phrase
                    };
                    $.ajax({
                        url: uri,
                        type: "DELETE",
                        data: JSON.stringify(_deldata)
                    })
                        .fail(function(data) {
                            swal("Failed", "Delete failed", 'error');
                        })
                        .done(function(data) {
                            // if the last one, notify on it only
                            if (num_left === 1) {
                                swal("Success", "Successfully deleted", 'success');
                                pillarModel.saltModel.updateMinion(_proj.hasProject, 'delete', level_to_delete, _proj.proj_name);
                            }
                            num_left--;

                            self.updateChecked();
                        });
                });
            };


            // Deletes the ZKnode for the selected server
            self.delPillar = function() {
                swal({
                        title: "Confirm",
                        text: "Are you sure you want to delete " + pillarModel.checkedNodes().length + " servers and ALL of their zookeeper pillar data?",
                        showCancelButton: true,
                        confirmButtonText: "Yes"
                    },
                    function(isConfirm) {
                        if (isConfirm) {
                            var left = pillarModel.checkedNodes().length;
                            ko.utils.arrayForEach(pillarModel.checkedNodes(), function(_assoc) {
                                var uri = pillarURI + _assoc.name;

                                var _deldata = {
                                    "username": pillarModel.login.elements.username(),
                                    "del_phrase": "Deleted server node: "
                                };

                                $.ajax({
                                    url: uri,
                                    type: "DELETE",
                                    data: JSON.stringify(_deldata),
                                    args: _assoc.name
                                })
                                    .fail(function(data) {
                                        swal("Delete Failed", "Failed to delete pillar(s)", 'error');
                                    })
                                    .done(function(data) {
                                        if (left === 1) {
                                            swal("Delete successful", "Pillar(s) deleted", 'success');
                                            pillarModel.loadServers();
                                            var singleItemArr = [];
                                            singleItemArr.push(this.args);
                                            pillarModel.saltModel.updateMinion(singleItemArr, 'delete', 'node', null);
                                        }
                                        left--;
                                    });
                            });
                        }
                    });
            };

            // Makes sure that the checked nodes are updated with the latest data after a change
            self.updateChecked = function() {
                ko.utils.arrayForEach(pillarModel.checkedNodes(), function(_alloc) {
                    $.ajax({
                        url: pillarURI + _alloc.name,
                        type: "GET"
                    })
                        .fail(function(data) {
                            swal("Error", "There was an error retrieving SELECTED pillar data", 'error');
                        })
                        .done(function(data) {
                            // does_not_exist is set, returned from the API, makes sure that we delete
                            // when a minion no longer exists.
                            if (data.DOES_NOT_EXIST) {
                                pillarModel.allNodes.remove(_alloc);
                                pillarModel.checkedNodes.remove(_alloc);
                            }
                            else {
                                var index = pillarModel.allNodes.indexOf(_alloc);
                                _alloc.pillar(data);
                                pillarModel.createObjForProjects(_alloc);
                                pillarModel.allNodes.replace(pillarModel.allNodes()[index], _alloc);
                                pillarModel.refreshTable(_alloc);
                            }
                        });
                });
                ko.utils.arrayForEach(pillarModel.editingNodes(), function(_alloc) {
                    $.ajax({
                        url: pillarURI + _alloc.name,
                        type: "GET"
                    })
                        .fail(function(data) {
                            swal("Error", "There was an error retrieving SELECTED pillar data", 'error');
                        })
                        .done(function(data) {
                            // does_not_exist is set, returned from the API, makes sure that we delete
                            // when a minion no longer exists.
                            if (data.DOES_NOT_EXIST) {
                                pillarModel.allNodes.remove(_alloc);
                                pillarModel.editingNodes.remove(_alloc);
                            }
                            else {
                                var index = pillarModel.allNodes.indexOf(_alloc);
                                _alloc.pillar(data);
                                pillarModel.createObjForProjects(_alloc);
                                pillarModel.allNodes.replace(pillarModel.allNodes()[index], _alloc);
                                pillarModel.refreshTable(_alloc);
                            }
                        });
                });
                pillarModel.allNodes.valueHasMutated();
            };

            // objOrName is either the name of the node to retrieve or the _assoc object
            self.getPillar = function(objOrName, create_new) {
                var uri;
                var name;
                var _assoc;
                if (create_new) {
                    name = objOrName;
                    uri = pillarURI + name;
                }
                else {
                    _assoc = objOrName;
                    uri = pillarURI + _assoc.name;
                }
                $.get(uri, function() {
                })
                    .fail(function(data) {
                        swal("Error", "There was an error retrieving pillar data", 'error');
                    })
                    .done(function(data) {
                        if (create_new) {
                            var entry = new pillarModel._assoc(name, data);
                            pillarModel.createObjForProjects(entry);
                            pillarModel.allNodes.push(entry);
                        }
                        else {
                            var indexAll = pillarModel.allNodes.indexOf(_assoc);
                            var indexChecked = pillarModel.checkedNodes.indexOf(_assoc);
                            _assoc.pillar(data);
                            pillarModel.createObjForProjects(_assoc);
                            pillarModel.allNodes.replace(pillarModel.allNodes()[indexAll], _assoc);
                            if (indexChecked !== -1) {
                                pillarModel.checkedNodes.replace(pillarModel.checkedNodes()[indexChecked], _assoc);
                            }
                        }
                    });
            };

            var updateAllAdditions = function() {
                pillarModel.nodeNames.forEach(function (server_name) {
                    var serverAlreadyExists = false;
                    ko.utils.arrayForEach(pillarModel.allNodes(), function (_assoc) {
                        if (server_name === _assoc.name) {
                            self.getPillar(_assoc, false);
                            serverAlreadyExists = true;
                        }
                    });
                    if (serverAlreadyExists === false){
                        self.getPillar(server_name, true);
                    }
                });
            };

            var updateAllDeletions = function() {
                ko.utils.arrayForEach(pillarModel.allNodes(), function (_assoc) {
                    var serverAlreadyExists = false;
                    if (typeof _assoc !== "undefined"){
                        pillarModel.nodeNames.forEach(function (name) {
                            if (_assoc.name === name)
                                serverAlreadyExists = true;
                        });
                        if (!serverAlreadyExists) {
                            pillarModel.allNodes.remove(_assoc);
                        }
                    }
                });
            };

            var updateAllProjects = function() {
                pillModel.allProjects.push()
            }

            var onSuccess = function (data) {
                // get all server data
                pillarModel.nodeNames = data;
                // update anything that was added, create new as necessary
                updateAllAdditions();
                // remove if any nodes are now gone
                updateAllDeletions();
                // update what is shown
                self.updateChecked();
            };

            var onFailure = function() {
                console.log('failed to get list of servers');
            };

            self.loadServers = function () {
                service.get('api/pillar/list_servers/', onSuccess, onFailure);
            };
        };
    }
);
