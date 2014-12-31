define([
        'knockout',
        'jquery',
        'service',
        'model/environmentModel'
    ],
    function(ko, $, service, environment) {
        return function saltModel(pillarModel) {
            var self = this;

            var saltParams = {};
            var saltMaster = "";

            var onSuccess = function(data) {
                try {
                    saltParams = data.salt;
                    if (environment.env().toLowerCase() === environment.envType.stg) {
                        saltMaster = saltParams.staging;
                    }
                    // UAT and Production both point to the Production Salt Master
                    else if (environment.env().toLowerCase() === environment.envType.uat ||
                        environment.env().toLowerCase() === environment.envType.prod) {
                        saltMaster = saltParams.production;
                    }
                    else {
                        swal("Error", "Environment not set", 'error');
                    }
                } catch(err) {
                    swal("Error", "Unable to parse Salt API parameters", 'error');
                }
            }

            var onFailure = function(data) {
                swal("Error", "Unable to retrieve Salt API parameters", 'error');
                console.log(data);
            }
                
            service.get('api/saltmaster/', onSuccess, onFailure);

            var _valdata = function(update_list, pillar_lookup, update_type, data_type, project, zk) {
                var self = this;
                self.list = update_list;
                self.pillar = pillar_lookup;
                self.type = update_type;
                self.data = data_type;
                self.project = project;
            };

            var checkObjContents = function(obj1, obj2) {
                var ret = true;
                for (var each in obj1) {
                    if (obj2.hasOwnProperty(each)) {
                        if (typeof obj1[each] === 'object') {
                            ret = checkObjContents(obj1[each], obj2[each]);
                        }
                        else if (obj1[each] !== obj2[each]) { 
                            ret = false;
                        }
                    }
                    else ret = false;
                }
                return ret;
            };

            self.validate = function(update_list, pillar_lookup, update_type, data_type, project) {
                var target = update_list;
                var run_func = "";
                var domain = ".spottrading.com";

                if (data_type === 'node') {
                    if (update_type === 'preCreate') {
                        run_func = "test.ping";
                        target += domain;
                    }
                    else if (update_type  === 'postCreate') {
                        run_func = "pillar.items";
                    }
                    else if (update_type === 'delete') {
                        run_func = "pillar.items"
                    }
                }

                else { //create/update/delete key/value/project
                    run_func = "pillar.items";
                }
                
                var _pass = new _valdata(target, pillar_lookup, update_type, data_type, project);

                $('#validateVisual').modal('show');
                var cmds = {
                    'fun': run_func,
                    'expr_form': 'list',
                    'tgt': target,
                    'username': saltParams.username,
                    'password': saltParams.password,
                    'eauth': 'pam',
                    'client': 'local'
                };

                $.ajax({
                    url: saltMaster,
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
                        var zk = "zookeeper_pillar";
                        var zkPillar;
                        var showSuccess = false;

                        // check if we get an empty object - failure!!
                        if ($.isEmptyObject(dataset)) {
                            validationFailure = true;
                        }

                        try {                        
                            if (this.args.data !== 'node') {
                                for (var i in dataset) {
                                    if (dataset.hasOwnProperty(i)) {
                                        zkPillar = dataset[i][zk];
                                        // check if the pillars have the same value
                                        // ordering of the keys may be different thanks to python
                                        var expected_pillar = this.args.pillar[i];
                                        var val1 = checkObjContents(expected_pillar, zkPillar);
                                        var val2 = checkObjContents(zkPillar, expected_pillar);
                                        if (!val1 || !val2) {
                                            validationFailure = true;
                                            errorMsg = "Salt pillar and updated pillar do not match, manual refresh required";
                                        }
                                        // Override validation failure of empty object if that's what we expect
                                        if ($.isEmptyObject(expected_pillar) && $.isEmptyObject(zkPillar)) {
                                            validationFailure = false;
                                        }
                                    }
                                }
                            }
                            else { // create or delete a node
                                if (this.args.type === 'preCreate') {
                                    // check if the ping is true
                                    if (!dataset[this.args.list]){
                                        validationFailure = true;
                                        errorMsg = "Server not found in Salt, please make sure this server is in Salt"
                                    }
                                    else {
                                        // actually create the node if ping returned - zk handles duplicates so unnecessary to check 
                                        pillarModel.pillarApiModel.api_post(this.args.list);
                                    }
                                }
                                else if (this.args.type === 'delete') {
                                    // make sure zkpillar is gone
                                    for (var server in dataset) { 
                                        // external pillar will not be completely gone from salts perspective
                                        // still appears as an empty object
                                        if (!$.isEmptyObject(dataset[server][zk])) {
                                            validationFailure = true;
                                            errorMsg = "ZK Pillar was not deleted";
                                        }
                                        else validationFailure = false;
                                    }
                                }
                                else if (this.args.type === 'postCreate') {
                                    // make sure zkpillar is there
                                    if (typeof (dataset[this.args.list][zk]) === "undefined") {
                                        validationFailure = true;
                                        errorMsg = "ZK Pillar does not exist";
                                    }
                                    else {
                                        showSuccess = true;
                                    }
                                }

                            } 
                        } catch(err) {
                            if (err.type === 'TypeErr') {
                                errorMsg = "TypeError caught, Salt config likely missing data";
                            }
                            else {
                                errorMsg = "Unexpected error caught: " + err.type;
                            }
                            validationFailure = true;
                        }
                        
                        $('#validateVisual').modal('hide');
                        // necessary due to switching contexts in async call above,
                        // not having access to validate visual fully
                        $('body').removeClass('modal-open');
                        $('.modal-backdrop').remove();

                        if (validationFailure) {
                            swal("Fatal", "Validation error: " + errorMsg, 'error');
                        }
                        else if (showSuccess) {
                            swal("Success", "External pillar zookeeper node created.", 'success');
                        }
                    });
            };

            self.updateMinion = function(array_to_update, single_update, update_type, data_type, project) {
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
                        pillar_lookup[_assoc.name] = _assoc.edit_pillar;
                    });
                }

                $('#loadVisual').modal('show');

                var cmds = {
                    'fun': 'saltutil.refresh_pillar',
                    'expr_form': 'list',
                    'tgt': all,
                    'username': saltParams.username,
                    'password': saltParams.password,
                    'eauth': 'pam'
                };

                $.ajax({
                    url: saltMaster,
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
                        self.validate(all, pillar_lookup, update_type, data_type, project);
                    });

            };
        };
    }
);
