define( [
        'knockout',
        'plugins/router',
        'service',
        'jquery',
        'model/pillarApiModel',
        'bindings/uppercase'
    ],
    function(ko, router, service, $, pillarApiModel) {
        return function pillarModel(login) {
    
            var self = this;
            self.login = login;

            self.servers = ko.observableArray([]);
            self.allInfo = ko.observableArray([]);//.extend({rateLimit: 100});
            self.checked_servers = ko.observableArray([]).extend({rateLimit: 100});
            self.show_allInfo = ko.observableArray([]);
            self.allProjects = ko.observableArray([]);
            self.allKeys= ko.observableArray([]);
            self.missingProject = ko.observableArray([]);
            self.hasProject = ko.observableArray([]);

            self.searchVal = ko.observable(""); 
            self.fieldOneVal = ko.observable("").extend({uppercase: true});
            self.selectedOption = ko.observable("Modify Pillar(s)").extend({rateLimit: 100});
            self.selectedProject = ko.observable("").extend({notify: "always"});
            self.selectedKey = ko.observable("").extend({notify: "always"});
            self.new_key = ko.observable("");
            self.new_value = ko.observable("");
            self.new_project = ko.observable("");
            self.edit_value = ko.observable("");
            self.selectedModify = ko.observable("Existing project");

            self.pillarOptions = ko.observableArray(["Modify Pillar(s)", "Create Pillar", "View Pillar(s)"]);//, "Delete Pillar(s)" ]);
            self.modifyOptions = ko.observableArray(["Existing project", "New project"]);
            self.new_pairs = ko.observableArray([{"key": "subtype", "value": ""}, {"key": "version", "value": ""}]); 

            self.alphaNum = /^[a-zA-Z0-9]+$/;

            self.pillarApiModel = new pillarApiModel(self);

            self._assoc = function(server_name, pillar_data) {
                var self = this;
                self.name = server_name;
                self.pillar = pillar_data;
                self.checked = ko.observable(false);
                self.prior = false;
                self.projects = {};
                // _assoc object also has dynamically created
            };

            var resetFields = function () {
                self.selectedProject(null);
                self.selectedKey(null);
                self.new_key("");
                self.new_value("");
                self.new_project("");
                self.edit_value("");
                self.allKeys([]);
            };

            self.refreshTable = function(_assoc) {
                self.allKeys([]);
                self.allProjects([]);
                addProjects(_assoc);
                self.missingProject([]);
                self.hasProject([]);
            };

            $(document).on('change keyup keydown paste cut', '.textarea', function() {
                $(this).height(0).height(this.scrollHeight);
            }).find('textarea').change();

            $(document).on('click', '#allDrop', function() {
                self.selectedProject($(this).text());
                // reset so it can be calculated for the new project
                self.allKeys([]);
                self.missingProject([]);
                self.hasProject([]);
            });

            $(document).on('click', '#allKey', function() {
                self.selectedKey($(this).text());
            });

            self.toggleSearch = function() {
                $('#searchPane').toggle(200);
            };

            self.removeQuery = function() {
                self.searchVal("");
            };

            self.addPair = function() {
                self.new_pairs.push({"key": "", "value": ""});
            };

            self.removePair = function() {
                if (self.new_pairs().length > 2) {
                    var remove = self.new_pairs.pop();
                    self.new_pairs.remove(remove);
                }
            };

            // ensure that no project is selected when moving to the New project tab
            self.properNewView = ko.computed(function() {
                if (self.selectedModify() === 'New project') { 
                    self.selectedProject(null);
                    self.selectedKey(null);
                }
            });

            self.validateNewPair = ko.computed(function() {
                if (self.new_key() !== "" && !self.alphaNum.test(self.new_key())) {
                    swal("Error", "Your key cannot contain non-alphanumerics", 'error');
                    self.new_key("");
                    return false;
                }

                return true;
            });

            var validateNewProject = function() {
                if (self.new_project() === ""){
                    swal("Error", "Please enter a project name", 'error');
                    return false;
                }
                ko.utils.arrayForEach(self.new_pairs(), function(pair){
                    if (pair.key !== "" && !self.alphaNum.test(pair.key)){
                        swal("Error", "Your key cannot contain non-alphanumerics", 'error');
                        pair.key = "";
                        return false;
                    }
                });               
                return true;
            };

            self.getValues = function (_assoc, field) {
                var ret = "";
                if (typeof self.selectedProject() === 'undefined' || self.selectedProject() === null)
                    return "Select a project";
                try {
                    ret = _assoc.projects[self.selectedProject()]()[field];
                    if (self.hasProject().indexOf(_assoc) === -1)
                        self.hasProject().push(_assoc);
                } catch(err) {
                    if (err.name === 'TypeError') {
                        ret = "Project Does Not Exist";
                        if (self.missingProject().indexOf(_assoc) === -1)
                            self.missingProject().push(_assoc);
                    }
                    else
                        ret = "An unexpected error occured";
                }

                return ret;
            };

            var JSONcreateProject = function (_assoc) {
                var pairs = {};
                ko.utils.arrayForEach(self.new_pairs(), function(pair) {
                    pairs[pair.key] = pair.value;
                });

                _assoc.pillar[self.new_project()] = pairs;
            };

            var JSONupdate = function(_assoc, update_type) {
                if (update_type === 'value')
                    _assoc.pillar[self.selectedProject()][self.selectedKey()] = self.edit_value();
                else if (update_type === 'key')
                    _assoc.pillar[self.selectedProject()][self.new_key()] = self.new_value();
            };

            self.uncheckAll = function() {
                ko.utils.arrayForEach(self.allInfo(), function(_assoc) {
                    _assoc.checked(false);
                });
            };
            
            // Performance issues, currently limited to 8 selected
            self.checkAll = function(check) {
                if (self.show_allInfo().length > 8){
                    swal("Sorry", "Please narrow-down your search results to less than 8 visible servers.", 'Error');
                    return;
                }
                var arrayCopy = self.show_allInfo();
                for(var inc = 0; inc < arrayCopy.length; inc++){
                    arrayCopy[inc].checked(true);
                }
                self.show_allInfo(arrayCopy);
                self.show_allInfo.valueHasMutated();
            };

            var switchViewToProject = function(project_name) {
                if (typeof project_name === 'undefined')
                    console.log("no project");
                else { 
                    self.selectedProject(project_name);
                    self.selectedModify("Existing project");
                }
            };

            self.createProjectWrapper = function(data) {
                var left = self.checked_servers().length;
                var refresh_salt = false;
                ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                    if (typeof _assoc.projects[data] !== "undefined"){
                        swal("Warning", "Project already exists on " + _assoc.name, 'error');
                        left--;
                    }
                    else if (validateNewProject()){
                        // only refresh salt after the last one is updated 
                        if (left == 1) refresh_salt = true; 
                        left--;
                        JSONcreateProject(_assoc);
                        self.pillarApiModel.api_post_json(_assoc, refresh_salt, self.checked_servers, 'project');
                        switchViewToProject(data);
                    }
                });
            };

            self.updateProjectWrapper = function(update_type, data_type) {
                var alertText = "";
                var alertTitle = "";
                if (self.missingProject().length > 0) {
                    alertText = self.missingProject().length + " server(s) are missing the " + data_type + ", proceed to " + update_type + " anyway?";
                    alertTitle = "Hmm...";
                }
                else {
                    alertText = "Are you sure you want to " + update_type + " the " + data_type + " on " + self.hasProject().length + " servers?";
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
                        if (update_type === 'delete')  
                            self.pillarApiModel.api_delete(data_type);
                        else {
                            var refresh_salt = false;
                            for (var each in self.hasProject()) {
                                if (each === (self.hasProject().length-1).toString()) {
                                    refresh_salt = true;
                                }
                                JSONupdate(self.hasProject()[each], data_type);
                                self.pillarApiModel.api_post_json(self.hasProject()[each], refresh_salt, self.hasProject, data_type);
                            }
                        }
                    }
                });
            };

            var addProjects = function(_assoc) {
                for (var each in _assoc.pillar){
                    if (self.allProjects.indexOf(each) < 0){
                        //console.log(each);
                        self.allProjects.push(each);
                    }
                }
                try { 
                    for (var each in _assoc.pillar[self.selectedProject()]){
                        if (self.allKeys.indexOf(each) < 0){
                            self.allKeys.push(each);
                        }
                    }
                } catch(err) {
                    if (err.name === "TypeError")
                        console.log("Race condition, not an issue");

                }

            };

            self.objProjects = function (_assoc) {
                //delete existing!!!
                _assoc.projects = [];
                for (var each in _assoc.pillar){
                    _assoc.projects[each] = ko.observable("");
                    _assoc.projects[each](_assoc.pillar[each]);
                }
            };

            self.checked_server_data = ko.computed(function() {
                ko.utils.arrayForEach(self.allInfo(), function(_assoc) {
                    if (_assoc.checked()){
                        if (!_assoc.prior){
                            addProjects(_assoc);
                            self.checked_servers.push(_assoc);
                            _assoc.prior = true;
                        }
                        else {
                            self.allProjects([]);
                            ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                                 addProjects(_assoc);
                                 self.objProjects(_assoc);
                            });
                        }
                    }
                    else if (!_assoc.checked()) {
                        if (_assoc.prior){
                            // remove from the array based on the server name
                            self.checked_servers.remove(_assoc);
                            //TODO: remove all each time and re-calculate based on what is now selected
                            self.allProjects([]);
                            ko.utils.arrayForEach(self.checked_servers(), function(_assoc) {
                                addProjects(_assoc);
                            });

                            // selected project may no longer be in the all projects array
                            var proj_exist = ko.utils.arrayFirst(self.allProjects(), function(project) {
                                return project === self.selectedProject();
                            });

                            if (!proj_exist) { 
                                self.selectedProject(null);
                                self.selectedKey(null);
                            }

                            _assoc.prior = false;
                            // if this is the last to be un-checked, reset all fields
                            if (self.checked_servers().length == 0){
                                resetFields();
                            }
                        }
                    }
                });
            });

            self.show_allInfo = ko.computed(function() {
                var query = self.searchVal().toLowerCase();
                if (query === ""){
                    return self.allInfo();
                }
                return ko.utils.arrayFilter(self.allInfo(), function(_assoc) {
                    //TODO: is this necessary?
                    try {
                        //return if the project exists
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
            }, self);

            var updateAllAdditions = function() {
                ko.utils.arrayForEach(self.servers(), function (server_name) {
                    var serverAlreadyExists = false;
                    //console.log(server_name);
                    ko.utils.arrayForEach(self.allInfo(), function (_assoc) {
                        if (server_name === _assoc.name) {
                            self.pillarApiModel.getPillar(_assoc, false);
                            serverAlreadyExists = true;
                        }
                    });
                    if (serverAlreadyExists === false){
                        self.pillarApiModel.getPillar(server_name, true);
                        //get pillar and create new _assoc object, push onto allInfo
                    }
                });
            };

            var updateAllDeletions = function() {
                ko.utils.arrayForEach(self.allInfo(), function (_assoc) {
                    var serverAlreadyExists = false;
                    //TODO: getting undefined here for some reason????
                    if (typeof _assoc !== "undefined"){
                        ko.utils.arrayForEach(self.servers(), function (name) {
                            if (_assoc.name === name)
                                serverAlreadyExists = true;
                        });
                        if (!serverAlreadyExists)
                            self.allInfo.remove(_assoc);
                    }
                });
            };
                            
            var onSuccess = function (data) {
                self.servers(data);
                updateAllAdditions();
                updateAllDeletions();
                self.pillarApiModel.updateChecked('get_list');
            };
            
            var onFailure = function() {
                console.log('failed to get list of servers');
            };

            self.loadServers = function () {
                service.get('api/pillar/list_servers/', onSuccess, onFailure);
            };   
        };
    });
