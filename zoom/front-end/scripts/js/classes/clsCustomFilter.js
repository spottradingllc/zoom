function CustomFilter(ko, parent) {
    var self = this;
    var parent = parent;
       
    self.parameter = ko.observable("");
    self.searchTerm = ko.observable("");

    self.enabled = ko.observable(false);
    self.inversed = ko.observable(false);

    self.customFilteredItems = ko.observableArray([]);
    self.pushMatchedItem = function(item) {
        // push only unique items
        if (self.customFilteredItems.indexOf(item) == -1){
            self.customFilteredItems.push(item);
        }
    }

    self.setParameter = function(param) {
        self.parameter(param);
        self.tearDown();
    };

    self.tearDown = function() {
      self.searchTerm("");
      self.enabled(false);
      self.inversed(false);
      self.customFilteredItems.removeAll();
    }

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
    }

    self.toggleInversed = function() {
        self.inversed(!self.inversed());
    }

    self.deleteFilter = function() {
        parent.customFilters.remove(self);
    };

    self.applyFilter = ko.computed(function() {
        self.customFilteredItems.removeAll();

        if (self.enabled()) {
            // check each application state for matches, perform appropriate filtering technique
            ko.utils.arrayForEach(parent.applicationStates(), function(appState) {
                var appParameter;

                if (self.parameter() == "applicationStatus") {
                    self.applyLogicalFilter(appState.applicationStatus().toLowerCase(), appState);
                }
                else if (self.parameter() == "configurationPath") {
                    self.applyLogicalFilter(appState.configurationPath, appState);
                }
                else if (self.parameter() == "applicationHost") {
                    self.searchTerm(self.searchTerm().toUpperCase());
                    self.applyLogicalFilter(appState.applicationHost().toUpperCase(), appState);
                }
                else if (self.parameter() == "startTime") {
                    self.applyLogicalFilter(appState.startTime().toLowerCase(), appState);
                }
                else if (self.parameter() == "errorState") {
                    self.applyLogicalFilter(appState.errorState().toLowerCase(), appState);
                }
                else { // perform dependency filtering
                    self.applyDependencyFilter(appState);
                }
            });
        }
    });

    self.applyLogicalFilter = function(appParameter, appState) {
        if (appParameter.indexOf(self.searchTerm()) > -1 && !self.inversed()) {
            self.pushMatchedItem(appState);
        }
        else if (appParameter.indexOf(self.searchTerm()) == -1 && self.inversed()) {
            self.pushMatchedItem(appState);
        }
        else {
            // do nothing
        }
    };

    self.applyDependencyFilter = function(appState) {
        if (self.parameter() == "requires" && !self.inversed()) {
            ko.utils.arrayForEach(appState.requires(), function(requirement) {
                if (requirement.configurationPath.indexOf(self.searchTerm()) > -1 && !self.inversed()){
                    self.pushMatchedItem(appState);
                }
            });    
        }
        else if (self.parameter() == "requiredBy" && !self.inversed()) {
            ko.utils.arrayForEach(appState.requiredBy(), function(dependent) {
                if (dependent.configurationPath.indexOf(self.searchTerm()) > -1 && !self.inversed()){
                    self.pushMatchedItem(appState);
                }
            });
        }
        else if (self.parameter() == "requires" && self.inversed()) {
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
                self.pushMatchedItem(appState);
            }
        }
        else { // (self.parameter() == "requiredBy" && self.inversed()) case
            // generate an array of the config paths of each dependent
            var dependentConfigPaths = ko.utils.arrayMap(appState.requiredBy(), function(dependent) {
                return dependent.configurationPath;
            });

            // check if any dependent config path contains the search term
            var matchingConfigPath = ko.utils.arrayFirst(dependentConfigPaths, function(configPath) {
                return (configPath.indexOf(self.searchTerm()) > -1);
            });

            // if no dependent config path contains the search term, push the application state
            if (!matchingConfigPath) {
                self.pushMatchedItem(appState);
            }
        }
    };
}