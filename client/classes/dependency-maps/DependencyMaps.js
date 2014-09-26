define(['jquery',
        'knockout',
        'd3',
        'classes/dependency-maps/IndentedDependencyTree',
        'classes/dependency-maps/PartitionChart' ],
function($, ko, d3, IndentedDependencyTree, PartitionChart){

return function DependencyMaps(parent) {

	var self = this;
	self.parent = parent;
	self.colors = {green : "#64FF74", yellow : "#FFE033", red : "#E85923"};

	self.applicationStateArray = ko.computed(function()	{
		return self.parent.filteredItems().slice();
	});

	self.createDependentsDict = function(appState) {
		var name = appState.configurationPath.substring(appState.configurationPath.indexOf("application/") + "application/".length);
		if (appState.requiredBy().length == 0) {
			return {name : name, 
				    status : appState.applicationStatus(), 
				    size : appState.requiredBy().length + 1};
		}
		else {
			return {name : name, 
				    children : ko.utils.arrayMap(appState.requiredBy(), function(dependent) {
						return self.createDependentsDict(dependent);
					}), 
					status : appState.applicationStatus(),
					size : appState.requiredBy().length + 1
					};
		}
	};

	self.createRequirementsDict = function(appState) {
		var name = appState.configurationPath.substring(appState.configurationPath.indexOf("application/") + "application/".length);
		if (appState.requires().length == 0) {
			return {name : name, 
				    status: appState.applicationStatus(), 
				    size : appState.requires().length + 1, 
				    errorState : appState.errorState()};
		}
		else {
			return {name : name,
					children : ko.utils.arrayMap(appState.requires(), function(requirement) {
						return self.createRequirementsDict(requirement);
					}),
					status : appState.applicationStatus(),
					size : appState.requires().length + 1,
					errorState : appState.errorState()
					};
		}
	};

	// check if some appState's dependents contain a particular appState
	self.dependentsContainAppState = function(parent, appState) {
		var result;

		if (parent.requiredBy().indexOf(appState) != -1 || parent == appState) {
			return true;
		}
		else {
			for(var i = 0; i < parent.requiredBy().length; i++) {
				result = self.dependentsContainAppState(parent.requiredBy()[i], appState);
				if (result) {
					return result;
				}
			}
			return false;
		}
	};

	// maps the above function over an array of appStates
	self.arrayDependentsContainAppState = function(arr, appState) {
		if (arr.indexOf(appState) != -1) {
			return true;
		}
		else {
			for(var i = 0; i < arr.length; i++) {
				if(self.dependentsContainAppState(arr[i], appState)) {
					return true;
				}
			}
		}
		return false;
	};

	self.dependents = ko.computed(function() {
		var dict = ko.observableArray([]);

		// sort app states based on number of requirements
		var sortedAppStates = self.applicationStateArray().slice().sort(function(left, right) {
								if (left.requiredBy().length == right.requiredBy().length) {
									return 0;
								}
								else if (left.requiredBy().length < right.requiredBy().length) {
									return 1;
								}
								else {
									return -1;
								}
		});

		// filter the sorted app states so no dependencies are included more than once
		var filteredAppStates = ko.observableArray([]);
		ko.utils.arrayForEach(sortedAppStates, function(appState){
			// include no app state at some level if it is included at some deeper level
			if (!self.arrayDependentsContainAppState(filteredAppStates(), appState)) {
				filteredAppStates.push(appState);
			}
		});	

		// create the dependents dictionary for each dependence relationship
		ko.utils.arrayForEach(filteredAppStates(), function(appState) {
			dict.push(self.createDependentsDict(appState));
		});

		return {name : 'Zoom', children: dict.slice(), status : "running", size : dict.length + 1};
	}).extend({rateLimit: 2000});

	self.requirements = ko.computed(function() {
		var dict = ko.observableArray([]);

		// sort app states based on status, then whether or not their requirements are up, then alphabetically
		var sortedAppStates = self.applicationStateArray().slice().sort(function(left, right) {
			if (left.applicationStatus() == right.applicationStatus()) {
				if (left.requirementsAreUp() == right.requirementsAreUp()) {
					if (left.configurationPath < right.configurationPath) {
						return -1;
					}
					else if (left.configurationPath > right.configurationPath) {
						return 1;
					}
					else {
						return 0;
					}
				}
				else if (left.requirementsAreUp() && !right.requirementsAreUp()) {
					return 1;
				}
				else {
					return -1;
				}
			}
			else if (left.applicationStatus() == "running") {
				return 1;
			}
			else {
				return -1;
			}
		});

		ko.utils.arrayForEach(sortedAppStates, function(appState) {
			dict.push(self.createRequirementsDict(appState));
		});

		return {name : 'Zoom', children: dict.slice(), status : "running", errorState : "ok"};
	}).extend({rateLimit: 1000});

	// VIEW OPERATIONS
	self.views = ko.observableArray([]);

	self.dependencyDrawer = new IndentedDependencyTree(d3, ko, self, "dependency-drawer");
	self.views.push(self.dependencyDrawer);
	self.parent.views.push(self.dependencyDrawer);

	self.partitionChart = new PartitionChart(d3, ko, self, "partition-chart");
	self.views.push(self.partitionChart);
	self.parent.views.push(self.partitionChart);

    self.showView = function(newView) {
		self.closeAllViews();
		if (newView != parent) {
			newView.show();
		}
	};

	parent.currentView.subscribe(self.showView);

	self.closeAllViews = function() {
		ko.utils.arrayForEach(self.views(), function(view) {
			view.hide();
		});

		d3.select("#d3-view-area").attr("display", "none");
	};

	// send live updates to the dependency drawer and partition chart
	self.requirements.subscribe(function(newDict) {
		self.dependencyDrawer.inputJSON(newDict);
	});

	self.dependents.subscribe(function(newDict) {
		self.partitionChart.inputJSON(newDict);
	});
}});
