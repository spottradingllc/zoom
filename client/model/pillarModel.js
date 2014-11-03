define( [
        'knockout',
        'plugins/router',
        'service',
        'jquery',
        'model/environmentModel',
        'model/adminModel',
        'model/GlobalMode',
        'model/customFilterModel',
    ],
    function(ko, router, service, $,  environment, admin, GlobalMode,
             CustomFilterModel) {
        return function pillarModel() {
    
            var self = this;

            self.servers = ko.observableArray([]);
            self.allInfo = ko.observableArray([]);
            self.show_pillar = ko.observable("");
            self.show_allInfo = ko.observableArray([]);

            self.searchVal = ko.observable(""); 

            self.pillarOptions = ko.observableArray(["", "Create Pillar", "Delete Pillar"]);

            self.fieldOneVal = ko.observable("");
            self.selectedOption = ko.observable("");

            self.domain = ".spottrading.com";

            self.checked_servers = ko.observableArray([]);

            function _assoc(server_name, pillar_data) {
                var self = this;
                self.name = server_name;
                self.pillar = pillar_data;
                self.checked = ko.observable(false);
                self.prior = false;
            };

            self.diff_and_show = ko.computed(function() {
                var firstRun = true;
                var compare = "";
                ko.utils.arrayForEach(self.allInfo(), function(_assoc) {
                    if (_assoc.checked()){
                        if (!_assoc.prior){
                            self.show_pillar(_assoc.pillar);
                            self.checked_servers.push(_assoc.pillar);
                            _assoc.prior = true;
                        } 
                        if (firstRun){
                            firstRun = false;
                            compare = _assoc.pillar;
                        }
                        else {
                            if (ko.toJSON(compare) != ko.toJSON(_assoc.pillar)){
                                console.log("not the same!");
                                self.show_pillar("");
                            }    
                        }
                    }
                    else {
                        if (assoc_prior){
                            
                });
            });

            // calls create minion from api
            self.newPillar = function () {
                console.log(self.fieldOneVal());
                $.post("api/pillar/" + self.fieldOneVal() + self.domain, function(){
                })
                .fail(function(data) {
                    console.log("failed to create new pillar for a new minion");
                })
                .done(function(data) {
                    console.log("succeeded making new pillar");
                });
            };

           // self.delPillar = function() {
           //     var response = confirm("Delete pillar for {0} servers?".format(self.numSelected()));
           //     if (response) {
           //         $.blah
           //     else
           //         return
           // };

            self.show_allInfo = ko.computed(function() {
                var query = self.searchVal().toLowerCase();
                if (query === ""){
                    return self.allInfo();
                }
                return ko.utils.arrayFilter(self.allInfo(), function(_assoc) {
                    console.log(_assoc.name);
                    if (_assoc.name.toLowerCase().indexOf(query) >= 0){
                        console.log("found match: " + _assoc.name.toLowerCase());
                    }
                    return _assoc.name.toLowerCase().indexOf(query) >= 0;
                });
            }, self);

            self.associatePillars = ko.computed(function() {
                //TODO: error handling for http get
                ko.utils.arrayForEach(self.servers(), function(server) {
                    $.get("api/pillar/" + server, function (){
                    })
                    .fail(function(data) {
                        console.log("failed to get server pillars");
                    })
                    .done(function(data) {
                        if ($.isEmptyObject(data)){
                            console.log("Pillar data is empty for server: " + server);
                            console.log(data);
                        }
                        else {
                            //var entry = {'name': server, 'pillar': data};
                            var entry = new _assoc(server, data);
                            self.allInfo.push(entry);
                        }
                    });

                });
            });

            var onSuccess = function (data) { 
                console.log(data);
                self.servers(data);
            };
            
            var onFailure = function() {
                console.log('failed to get list of servers');
            };

            self.loadServers = function () {
                service.get('api/pillar/list_servers/', onSuccess, onFailure);
            };   
        

        };
    });
