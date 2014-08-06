function CustomFilter(ko, $, parent) {
    var self = this;

    // trickle-down dictionaries
    self.parameters = {
        applicationStatus : "applicationStatus", configurationPath : "configurationPath",
        applicationHost : "applicationHost", startTime : "startTime", errorState : "errorState",
        dependency : "dependency", requires : "requires", requiredBy : "requiredBy"
    };

    self.searchTerms = {
        running : "running", stopped : "stopped", unknown : "unknown", ok : "ok",
        starting : "starting", stopping : "stopping", error : "error"
    };

    // member variables and getters/setters
    self.filterName = ko.observable("");
    self.parameter = ko.observable("");
    self.searchTerm = ko.observable("");
    self.enabled = ko.observable(false);
    self.inversed = ko.observable(false);
    self.numberPassed = ko.observable("");

    self.tearDown = function() {
      self.searchTerm("");
      self.enabled(false);
      self.inversed(false);
    };

    self.setParameter = function(param) {
        self.parameter(param);
        self.tearDown();
    };

    self.setSearchTerm = function(term) {
        self.searchTerm(term);
    };

    // tear down the filter whenever the search term is blank
    self.searchTerm.subscribe(function(term) {
      self.enabled(true);

      if (term == "") {
        self.tearDown();
      }
    });

    self.toggleEnabled = function() {
        self.enabled(!self.enabled());
    };

    self.toggleInversed = function() {
        self.inversed(!self.inversed());
    };

    self.deleteFilter = function() {
        parent.customFilters.remove(self);
    };

    self.openFilter = function() {
        parent.customFilters.push(self);
    };

    self.filter = function(ret) {

        if (self.enabled()) {
            ret = ko.utils.arrayFilter(ret, function(item){
                return self.passes(item);
            });

            self.numberPassed(ret.length);
        }
        return ret;
    };

    self.passes = function(appState) {

        if (self.parameter() == self.parameters.applicationStatus) {
            return self.applyLogicalFilter(appState.applicationStatus().toLowerCase(), appState);
        }
        else if (self.parameter() == self.parameters.configurationPath) {
            return self.applyLogicalFilter(appState.configurationPath, appState);
        }
        else if (self.parameter() == self.parameters.applicationHost) {
            self.searchTerm(self.searchTerm().toUpperCase());
            return self.applyLogicalFilter(appState.applicationHost().toUpperCase(), appState);
        }
        else if (self.parameter() == self.parameters.startTime) {
            return self.applyLogicalFilter(appState.startTime().toLowerCase(), appState);
        }
        else if (self.parameter() == self.parameters.errorState) {
            return self.applyLogicalFilter(appState.errorState().toLowerCase(), appState);
        }
        else { // perform dependency filtering
            return self.applyDependencyFilter(appState);
        }
    };

    self.applyLogicalFilter = function(appParameter, appState) {
        if (appParameter.indexOf(self.searchTerm()) > -1 && !self.inversed()) {
            return true;
        }
        else if (appParameter.indexOf(self.searchTerm()) == -1 && self.inversed()) {
            return true;
        }
        else {
            return false;
        }
    };

    self.applyDependencyFilter = function(appState) {
        if (self.parameter() == self.parameters.requires && !self.inversed()) {
            ko.utils.arrayForEach(appState.requires(), function(requirement) {
                if (requirement.configurationPath.indexOf(self.searchTerm()) > -1 && !self.inversed()){
                    return true;
                }
            });    
        }
        else if (self.parameter() == self.parameters.requiredBy && !self.inversed()) {
            ko.utils.arrayForEach(appState.requiredBy(), function(dependent) {
                if (dependent.configurationPath.indexOf(self.searchTerm()) > -1 && !self.inversed()){
                    return true;
                }
            });
        }
        else if (self.parameter() == self.parameters.requires && self.inversed()) {
            // generate an array of the config paths of each requirement
            var requirementConfigPaths = ko.utils.arrayMap(appState.requires(), function(requirement) {
                return requirement.configurationPath;
            });

            // check if any required config path contains the search term
            var matchingConfigPath = ko.utils.arrayFirst(requirementConfigPaths, function(configPath) {
                return (configPath.indexOf(self.searchTerm()) > -1);
            });

            // if no required config path contains the search term, push the application state
            if (!matchingConfigPath) {
                return true;
            }
        }
        else { // (self.parameter() == "requiredBy" && self.inversed()) case
            // generate an array of the config paths of each dependent
            var dependentConfigPaths = ko.utils.arrayMap(appState.requiredBy(), function(dependent) {
                return dependent.configurationPath;
            });

            // if no dependent config path contains the search term, push the application state
            if (!matchingConfigPath) {
                return true;
            }
        }

        return false;
    };

    // Operations for remote saving/deleting
    self.saveFilterRemotely = function() {
        var dict = {
            operation: 'add',
            name : self.filterName(),
            loginName : parent.login.elements.username(),
            parameter : self.parameter(),
            searchTerm : self.searchTerm(),
            inversed : self.inversed()
        };

        if (self.filterName() == "") {
            alert("You must enter a filter name in order to save the filter remotely.");
        }
        else {
            $.post("/api/filters/", dict, function(data) {
                alert(data);
            });
        }
    };

    self.deleteFilterRemotely = function() {
        var dict = {
            operation: 'remove',
            name : self.filterName(),
            loginName : parent.login.elements.username(),
            parameter : self.parameter(),
            searchTerm : self.searchTerm(),
            inversed : self.inversed()
        };
        $.post("/api/filters/", dict, function (returnData) {
                    alert(returnData);
        });

    };

    self.canBeAlteredRemotely = ko.computed(function() {
        return !!(self.parameter() != "" && self.searchTerm() != "");
    });
}
