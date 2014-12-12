define( [
        'knockout',
        'service',
        'jquery',
        'model/pillarApiModel',
        'model/saltModel',
        'bindings/uppercase',
        'bindings/pillarEditor'
    ],
    function(ko, service, $, pillarApiModel, saltModel) {
        return function pillarModel(login) {
    
            var self = this;
            self.login = login;

            // stores list of node names returned from API
            self.nodeNames = [];

            // nodes with their associated data in _assoc
            self.allNodes = ko.observableArray([]);//.extend({rateLimit: 100});

            // nodes from allNodes that should be shown based on the current query 
            self.queriedNodes = ko.observableArray([]);

            // nodes from allNodes that are checked
            self.checkedNodes = ko.observableArray([]);//.extend({rateLimit: 100});
            
            // all projects for a  
            self.allProjects = ko.observableArray([]);
            self.allKeys= ko.observableArray([]);

            self.pillarOptions = ko.observableArray(["Modify Pillar(s)", "Create Pillar", "View Pillar(s)"]);//, "Delete Pillar(s)" ]);
            self.modifyOptions = ko.observableArray(["Existing project", "New project"]);
            self.new_pairs = ko.observableArray(newPairDefault); 

            self.searchVal = ko.observable(""); 
            self.newNodeName= ko.observable("").extend({uppercase: true});
            self.selectedOption = ko.observable("Modify Pillar(s)").extend({rateLimit: 100});
            self.selectedModify = ko.observable("Existing project");
            self.new_key = ko.observable("");
            self.new_project = ko.observable("");
            
            self.pillarApiModel = new pillarApiModel(self);
            self.saltModel = new saltModel(self);

            self.tableEditing = false;
            var alphaNum = /^[a-zA-Z0-9]+$/;

            self._assoc = function(server_name, pillar_data) {
                var self = this;
                self.name = server_name;
                self.pillar = pillar_data;
                self.edit_pillar = {};
                self.projects = {};
                self.checked = ko.observable(false);
                self.editable = ko.observable(false);
                self.prior = false;
            };

            self._proj = function(name) {
                var self = this;
                self.proj_name = name;
                self.keys = ko.observableArray([]);
                self.edit_keys = ko.observableArray([]);
                self.hasProject = [];
                self.new_key = ko.observable("");
                self.editing = ko.observable(false);
                // need a way of keeping track of the number of servers
                // which have that project, when it reaches zero: remove
                self.freq = 0;
            };

            var resetFields = function () {
                self.new_project("");
                self.allKeys([]);
            };

            self.refreshTable = function(_assoc) {
                self.allKeys([]);
                self.allProjects([]);
                addProjects(_assoc);
            };

            self.toggleSearch = function() {
                $('#searchPane').toggle(200);
            };

            self.removeQuery = function() {
                self.searchVal("");
            };

            self.addPair = function() {
                self.new_pairs.push({"key": null, "value": null});
            };

            self.removePair = function() {
                if (self.new_pairs().length > 2) {
                    var remove = self.new_pairs.pop();
                    self.new_pairs.remove(remove);
                }
            };

            var validateNewPair = ko.computed( function() {
                if (self.new_key() !== "" && !alphaNum.test(self.new_key())) {
                    swal("Error", "Your key cannot contain non-alphanumerics", 'error');
                    self.new_key("");
                    return false;
                }
                if (self.new_project() !== "" && !alphaNum.test(self.new_project())) {
                    swal("Error", "Your project name cannot contain non-alphnumerics", 'error');
                    self.new_project("");
                    return false;
                }
                return true;
            });

            var validateNewProject = function() {
                if (self.new_project() === ""){
                    swal("Error", "Please enter a project name", 'error');
                    return false;
                }
                var ret = true;

                var parsed_pairs = $.extend(true, [], self.new_pairs());
                ko.utils.arrayForEach(self.new_pairs(), function(pair){
                    if (pair.key !== "" && !alphaNum.test(pair.key)){
                        swal("Error", "Your key cannot contain non-alphanumerics", 'error');
                        pair.key = "";
                        ret = false;
                    }
                    if (typeof pair.value !== 'undefined' && pair.value !== "") { 
                        try {
                            // make sure we can parse it later
                            var parsed = JSON.parse(pair.value);
                        } catch(err) {
                            swal("Error", "Please make sure your values consist of valid JSON", 'error');
                            ret = false;
                        }
                    }
                
                });               
                return ret;
            };


            self.getValues = function (_assoc, _proj, field) {
                var ret = "";
                try {
                    ret = JSON.stringify(_assoc.projects[_proj.proj_name]()[field]);
                    if (_proj.hasProject.indexOf(_assoc) === -1)
                        _proj.hasProject.push(_assoc);
                } catch(err) {
                    if (err.name === 'TypeError') {
                        ret = "Project Does Not Exist";
                    }
                    else
                        ret = "An unexpected error occured";
                }
                return ret;
            };

            self.makeEditable = function (_assoc) {
                // find this _assoc in checked servers...
                var index = self.checkedNodes.indexOf(_assoc);
                self.checkedNodes()[index].editable(true);
            };

            self.doneEditing = function (_updatingassoc) {
                ko.utils.arrayForEach(self.checkedNodes(), function(_assoc) {
                    if (_assoc !== _updatingassoc) {
                        if (_assoc.editable) _assoc.editable(false); 
                    }
                });
            };

            self.showEdit = function(html_proj) {
                html_proj.editing(true);
                // get latest pillar data and place into edit_pillar:
                // deep copy
                ko.utils.arrayForEach(self.checkedNodes(), function(_assoc) {
                    _assoc.edit_pillar = $.extend(true, {}, _assoc.pillar);
                });
                // deep copy equivalent
                html_proj.edit_keys([]);
                ko.utils.arrayForEach(html_proj.keys(), function(key) {
                    html_proj.edit_keys.push(key);
                });
            };

            self.cancelEditing = function(html_proj) {
                html_proj.editing(false);
            };
                        
            self.visualUpdate = function(update_type, data_type, _proj, key) {
                if (update_type === 'create') {
                    if (data_type === 'key') {
                        var new_key = _proj.new_key();
                        if (new_key === "") {
                            swal("Error", "Please enter a value for the new key", 'error');
                            return;
                        }
                        _proj.hasProject.forEach(function(_assoc) {
                            // essentially the same as json update
                            _assoc.edit_pillar[_proj.proj_name][new_key] = null;
                        });
                        _proj.edit_keys.push(new_key);
                    }
                }
                else if (update_type === 'delete') {
                    if (data_type === 'key') {
                        _proj.hasProject.forEach(function(_assoc) {
                            delete _assoc.edit_pillar[_proj.proj_name][key];
                        });
                        var i = _proj.edit_keys.indexOf(key);
                        // delete and update array
                        _proj.edit_keys.splice(i, 1); 
                    }
                }
            }; 

            var JSONcreateProject = function (_assoc) {
                var pairs = {};
                ko.utils.arrayForEach(self.new_pairs(), function(pair) {
                    pairs[pair.key] = JSON.parse(pair.value);
                });
                // deep copy
                _assoc.edit_pillar = $.extend(true, {}, _assoc.pillar);
                _assoc.edit_pillar[self.new_project()] = pairs;
            };

            self.uncheckAll = function() {
                ko.utils.arrayForEach(self.allNodes(), function(_assoc) {
                    _assoc.checked(false);
                });
            };

            self.checkAll = function() {
                if (self.show_allNodes().length > 8){
                    swal("Sorry", "Please narrow-down your search results to less than 8 visible servers.", 'error');
                    return;
                }
                ko.utils.arrayForEach(self.show_allNodes(), function(_assoc) {
                    _assoc.checked(true);
                });
            };
            
            var switchViewToProject = function(project_name) {
                if (typeof project_name === 'undefined') {
                    console.log("no project");
                }
                else { 
                    self.selectedModify("Existing project");
                }
            };

            self.createProjectWrapper = function(data) {
                var left = self.checkedNodes().length;
                var refresh_salt = false;

                // validate once, even if multiple servers since using the same data.
                if (validateNewProject() === false) return;

                // check if validate worked 
                ko.utils.arrayForEach(self.checkedNodes(), function(_assoc) {
                    if (typeof _assoc.projects[data] !== "undefined"){
                        swal("Warning", "Project already exists on " + _assoc.name, 'error');
                        left--;
                    }
                
                    else {
                        // only refresh salt after the last one is updated 
                        if (left == 1) {
                            refresh_salt = true; 
                        }
                        left--;
                        JSONcreateProject(_assoc);
                        self.pillarApiModel.api_post_json(_assoc, refresh_salt, self.checkedNodes(), 'project');
                        switchViewToProject(data);
                    }
                });
            };

            self.updateProjectWrapper = function(update_type, data_type, _proj, key) {
                var alertText = "";
                var alertTitle = "";
                if (_proj.hasProject.length < self.checkedNodes()) {
                    alertText = "Only " + _proj.has_project().length + " server(s) have the " + data_type + ", proceed to " + update_type + " anyway?";
                    alertTitle = "Hmm...";
                }
                else {
                    alertText = "Are you sure you want to " + update_type + " the " + data_type + " on " +  _proj.hasProject.length + " servers?";
                    alertTitle = "Confirm";
                }
                swal({
                    title: alertTitle,
                    text: alertText,
                    showCancelButton: true,
                    confirmButtonText: "Yes"
                }, 
                function(isConfirm){
                    if (isConfirm) {
                        if (update_type === 'delete') {
                            self.pillarApiModel.api_delete(data_type, _proj, key);
                        } 
                        else {
                            var refresh_salt = false;
                            for (var each in _proj.hasProject) {
                                if (each === (_proj.hasProject.length-1).toString()) {
                                    refresh_salt = true;
                                }
                                // ONLY send the salt refresh command after the last post has been made, to avoid spamming the salt master
                                self.pillarApiModel.api_post_json(_proj.hasProject[each], refresh_salt, _proj.hasProject, data_type);
                            }
                        }
                    }
                });
            };

            var addProjects = function(_assoc) {
                $.each(_assoc.pillar, function(proj_name, keyVals) {
                    var found = false;
                    for (var i in self.allProjects()) {
                        if (self.allProjects()[i].proj_name === proj_name) {
                            self.allProjects()[i].freq++; 
                            found = true;
                        }
                    } 
                    if (!found) {
                        var new_proj = new self._proj(proj_name);
                        new_proj.freq = 1;
                        $.each(keyVals, function(key, value) {
                            new_proj.keys.push(key);
                        }); 
                        self.allProjects.push(new_proj);
                    }
                });
            };

            self.createObjForProjects = function (_assoc) {
                //delete existing!!!
                _assoc.projects = [];
                for (var each in _assoc.pillar){
                    _assoc.projects[each] = ko.observable("");
                    _assoc.projects[each](_assoc.pillar[each]);
                }
            };

            // Computed function that is called whenever a server in allNodes 

            self.checked_server_data = ko.computed(function() {
                ko.utils.arrayForEach(self.allNodes(), function(_assoc) {
                    if (_assoc.checked()){
                        if (!_assoc.prior){
                            addProjects(_assoc);
                            self.checkedNodes.push(_assoc);
                            _assoc.prior = true;
                        }
                        else {
                            //TODO: significant performance hit
                            self.allProjects([]);
                            ko.utils.arrayForEach(self.checkedNodes(), function(_assoc) {
                                 addProjects(_assoc);
                                 self.createObjForProjects(_assoc);
                            });
                        }
                    }
                    else if (!_assoc.checked()) {
                        if (_assoc.prior){
                            self.checkedNodes.remove(_assoc);
                            //TODO: significant perormance hit
                            self.allProjects([]);
                            ko.utils.arrayForEach(self.checkedNodes(), function(_assoc) {
                                addProjects(_assoc);
                            });

                            _assoc.prior = false;
                            // if this is the last to be un-checked, reset all fields
                            if (self.checkedNodes().length === 0){
                                resetFields();
                            }
                        }
                    }
                });
            });

            self.show_allNodes= ko.computed(function() {
                var query = self.searchVal().toLowerCase();
                if (query === ""){
                    return self.allNodes();
                }
                return ko.utils.arrayFilter(self.allNodes(), function(_assoc) {
                    try {
                        for (var each in _assoc.projects){
                            if (each.toLowerCase().indexOf(query) >= 0){
                                return _assoc;
                            }
                        }
                    } catch (err){
                        if (err.type === "TypeErr"){
                            console.log("Proj DNE");
                        }
                        else {
                            console.log(err);
                        }
                    } 

                    return _assoc.name.toLowerCase().indexOf(query) >= 0;
                });
            });

            var updateAllAdditions = function() {
                self.nodeNames.forEach(function (server_name) {
                    var serverAlreadyExists = false;
                    ko.utils.arrayForEach(self.allNodes(), function (_assoc) {
                        if (server_name === _assoc.name) {
                            self.pillarApiModel.getPillar(_assoc, false);
                            serverAlreadyExists = true;
                        }
                    });
                    if (serverAlreadyExists === false){
                        self.pillarApiModel.getPillar(server_name, true);
                    }
                });
            };

            var updateAllDeletions = function() {
                ko.utils.arrayForEach(self.allNodes(), function (_assoc) {
                    var serverAlreadyExists = false;
                    if (typeof _assoc !== "undefined"){
                        self.nodeNames.forEach(function (name) {
                            if (_assoc.name === name)
                                serverAlreadyExists = true;
                        });
                        if (!serverAlreadyExists) {
                            self.allNodes.remove(_assoc);
                        }
                    }
                });
            };
                            
            var onSuccess = function (data) {
                // get all server data
                self.nodeNames = data;
                // update anything that was added, create new as necessary
                updateAllAdditions();
                // remove if any nodes are now gone
                updateAllDeletions();
                // update what is shown
                self.pillarApiModel.updateChecked();
            };
            
            var onFailure = function() {
                console.log('failed to get list of servers');
            };

            self.loadServers = function () {
                service.get('api/pillar/list_servers/', onSuccess, onFailure);
            };   
        };
    });
