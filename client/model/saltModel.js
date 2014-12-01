define([
        'knockout',
        'plugins/router',
        'service',
        'jquery',
        'bindings/uppercase'
    ],
    function(ko, router, service, $) {
        return function saltModel() {
            var self = this;

            var _valdata = function(update_type, data_type, data_delta, value, project, zk) {
                var self = this;
                self.type = update_type;
                self.data = data_type;
                self.key = data_delta;
                self.value = value;
                self.project = project;
                self.zk = zk;
            };

            self.validate = function(update_list, update_type, data_type, data_delta, value, project) {
                var target = update_list;
                var run_func = "";
                var run_arg = "zookeeper_pillar:" + project;
                var zk = "zookeeper_pillar";

                var _pass = new _valdata(update_type, data_type, data_delta, value, project, zk);

                if (data_type === 'node') {
                    run_func = "test.ping";
                }
                else { //create/update/delete key/value/project
                    run_func = "pillar.items";
                }

                $('#validateVisual').modal('show');
                var cmds = {
                    'fun': run_func,
                    'expr_form': 'list',
                    'tgt': target,
                    'username': 'salt',
                    'password': 'salt',
                    'eauth': 'pam',
                    'client': 'local'
                };

                $.ajax({
                    url: "http://saltStaging:8000/run",
                    type: 'POST',
                    data: cmds,
                    args: _pass,
                    headers: {'Accept': 'application/json'}
                })
                    .fail(function(data) {
                        swal("Error", "Failed to get data used to validate changes", 'error');
                        $('#validateVisual').modal('hide');
                    })
                    .done(function(data) {
                        // check if the data returned is correct
                        var validationFailure = false;
                        var dataset = data.return[0];
                        var thisProject;

                        if (this.args.type === 'update') {
                            for (var i in dataset) {
                                if (dataset.hasOwnProperty(i)) {
                                    thisProject = dataset[i][this.args.zk][this.args.project];
                                    // check if project exists
                                    if (!thisProject) {
                                        validationFailure = true;
                                    }
                                    // check if the value is correct and exists
                                    var key = this.args.key;
                                    if (this.args.value && thisProject[key] !== this.args.value) {
                                        validationFailure = true;
                                    }
                                }
                            }
                        }
                        else if (this.args.type === 'delete') {
                            // corner case if deleting one node and it is successful...
                            // shouldn't be a problem with this structure

                            for (var j in dataset) {
                                if (dataset.hasOwnProperty(j)) {
                                    if (this.args.data === 'key') {
                                        thisProject = dataset[j][this.args.zk][this.args.project];
                                        if (thisProject[this.args.key]) {
                                            validationFailure = true;
                                        }
                                    }
                                    else if (this.args.data === 'project') {
                                        if (dataset[j][this.args.zk][this.args.project]) {
                                            validationFailure = true;
                                        }
                                    }
                                    else if (this.args.data === 'node') {
                                        if (!($.isEmptyObject(dataset))) {
                                            validationFailure = true;
                                        }
                                    }
                                }
                            }
                        }

                        else if (this.args.type === 'create') {
                            if ($.isEmptyObject(data.return[0])) {
                                validationFailure = true;
                            }
                        }

                        $('#validateVisual').modal('hide');
                        if (validationFailure) {
                            swal("Fatal", "Validation returned negative, please make sure to refresh your minions", 'error');
                        }
                    });
            };

            self.updateMinion = function(ko_array_to_update, single_update, update_type, data_type, data_delta, value, project) {
                var all = "";
                // create comma-delimited 'list' to send
                var first = true;

                if (single_update) {
                    all = ko_array_to_update;
                }
                else {
                    ko.utils.arrayForEach(ko_array_to_update(), function(_assoc) {
                        if (!first) {
                            all += "," + _assoc.name;
                        }
                        else {
                            all += _assoc.name;
                            first = false;
                        }
                    });
                }

                $('#loadVisual').modal('show');

                var cmds = {
                    'fun': 'saltutil.refresh_pillar',
                    'expr_form': 'list',
                    'tgt': all,
                    'username': 'salt',
                    'password': 'salt',
                    'eauth': 'pam'
                };

                $.ajax({
                    url: "http://saltStaging:8000/run",
                    type: 'POST',
                    data: cmds,
                    headers: {'Accept': 'application/json'}
                })
                    .fail(function(data) {
                        $('#loadVisual').modal('hide');
                        swal("Critical", "Salt was not able to update - pillar will not be applied", 'error');
                    })
                    .done(function(data) {
                        $('#loadVisual').modal('hide');
                        self.validate(all, update_type, data_type, data_delta, value, project);
                    });

            };
        };
    }
);