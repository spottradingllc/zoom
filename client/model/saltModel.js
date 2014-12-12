define([
        'knockout',
        'jquery',
    ],
    function(ko, $) {
        return function saltModel(pillarModel) {
            var self = this;

            var _valdata = function(update_list, pillar_lookup, update_type, data_type, data_delta, value, project, zk) {
                var self = this;
                self.list = update_list;
                self.pillar = pillar_lookup;
                self.type = update_type;
                self.data = data_type;
                self.key = data_delta;
                self.value = value;
                self.project = project;
                self.zk = zk;
            };

            self.validate = function(update_list, pillar_lookup, update_type, data_type, data_delta, value, project) {
                var target = update_list;
                var run_func = "";
                var zk = "zookeeper_pillar";

                var _pass = new _valdata(update_list, pillar_lookup, update_type, data_type, data_delta, value, project, zk);

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
                        var errorMsg;
                        var dataset = data.return[0];
                        var zkPillar;

                        // check if we get an empty object - failure!!
                        if ($.isEmptyObject(dataset)) {
                            validationFailure = true;
                        }

                        // any sort of update
                        if (this.args.data !== 'node') {
                            try {
                                for (var i in dataset) {
                                    if (dataset.hasOwnProperty(i)) {
                                        zkPillar = dataset[i][this.args.zk];
                                        // check if the pillars have the same value
                                        // TODO: skeptical if lookup will work correctly
                                        var expected_pillar = this.args.pillar_lookup[i];
                                        if (zkPillar !== cur_pillar) {
                                            validationFailure = true;
                                            errorMsg = "Salt pillar and updated pillar do not match, manual refresh required";
                                        }
                                    }
                                }
                            } catch(err) {
                                if (err.type === 'TypeErr') {
                                    console.log("TypeError caught, Salt config likely missing data");
                                }
                                else {
                                    console.log("Unexpected error caught: " + err.type);
                                }
                                validationFailure = true;
                            }

                        }
                        else { // create or delete a node
                            try {
                                if (this.args.data === 'preCreate') {
                                    // check if the ping is true
                                    if (!dataset[0]){
                                        validationFailure = true;
                                        errorMsg = "Server not found in Salt, please make sure this server is in Salt"
                                    }
                                    // call api post
                                    self.pillarModel.pillarApiModel.
                                }
                                else if (this.args.data === 'delete') {
                                    // make sure zkpillar is gone
                                    if (!$.isEmptyObject(dataset[0][this.args.zk])) {
                                        validationFailure = true;
                                        errorMsg = "ZK Pillar still exists";
                                    }
                                }
                                else if (this.args.data === 'postCreate') {
                                    // make sure zkpillar is there
                                    if ($.isEmptyObject(dataset[0][this.args.zk])) {
                                        validationFailure = true;
                                        errorMsg = "ZK Pillar does not exist";
                                    }
                                }

                            } catch(err) {
                                if (err.type === 'TypeErr') {
                                    console.log("TypeError caught, Salt config likely missing data");
                                }
                                else {
                                    console.log("Unexpected error caught: " + err.type);
                                }
                                validationFailure = true;
                            }
                        }
                        
                        $('#validateVisual').modal('hide');
                        if (validationFailure) {
                            swal("Fatal", "Validation returned negative, please make sure to refresh your minions", 'error');
                        }
                    });
            };

            self.updateMinion = function(array_to_update, single_update, update_type, data_type, data_delta, value, project) {
                var all = "";
                var first = true;

                var pillar_lookup = {};

                // creating a single node...
                if (single_update) {
                    all = array_to_update;
                }
                else {
                    array_to_update.forEach(function(_assoc) {
                        // create a salt-readable list for sending through the API
                        if (!first) {
                            all += "," + _assoc.name;
                        }
                        else {
                            all += _assoc.name;
                            first = false;
                        }
                        // we need a way of determining if the pillar is updated and has the correct
                        // data in salt!
                        pillar_lookup[_assoc.name] = _assoc.pillar;
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
                        self.validate(all, pillar_lookup, update_type, data_type, data_delta, value, project);
                    });

            };
        };
    }
);
