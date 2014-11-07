define(['jquery', 'knockout', 'classes/CustomFilter' ], function($, ko, CustomFilter) {
    return function CustomFilterModel(parent) {
        var self = this;
        // Custom Filtering
        self.all = new ko.observableArray([]);
        self.matchIntersection = ko.observable(true);
        self.enabled = ko.computed(function() {
            return ko.utils.arrayFilter(self.all(), function(customFilter) {
                return customFilter.enabled();
            });
        });

        self.matchTypeVisible = ko.computed(function() {
            return self.all().length > 1;
        });

        self.toggleMatchIntersection = function() {
            self.matchIntersection(!self.matchIntersection());
        };

        self.allMatchedItems = ko.computed(function() {
            // first aggregate all items from all custom filters
            var allCustomFilteredItems = ko.observableArray([]);
            ko.utils.arrayForEach(self.enabled(), function(customFilter) { // loop over all enabled filters
                ko.utils.arrayForEach(customFilter.matchedItems(), function(item) {
                    if (allCustomFilteredItems.indexOf(item) === -1) {
                        // only push unique items
                        allCustomFilteredItems.push(item);
                    }
                });
            });

            // If matching the union, return everything
            if (!self.matchIntersection()) {
                return allCustomFilteredItems().slice();
            }
            else {
                // take the intersection of all the custom filtered items
                var intersection = ko.observableArray(allCustomFilteredItems().slice());
                ko.utils.arrayForEach(allCustomFilteredItems(), function(filteredItem) { // loop over all items
                    ko.utils.arrayForEach(self.enabled(), function(customFilter) { // loop over all filters
                        if (customFilter.matchedItems().indexOf(filteredItem) === -1) {
                            // remove the item if it is missing in any filter
                            intersection(intersection.remove(function(item) {
                                return item !== filteredItem;
                            }));
                        }
                    });
                });
                return intersection().slice();
            }
        });

        // rate-limit how often filtered items are populated
        self.allMatchedItems.extend({rateLimit: 500});

        self.addCustomFilter = function() {
            var filter = new CustomFilter(self, parent);
            self.all.push(filter);
        };

        self.clearAllFilters = function() {
            self.all.removeAll();
        };

        self.remoteCustomFilters = ko.observableArray([]);
        self.fetchAllFilters = function() {
            var dict = {loginName: parent.login.elements.username()};

            if (parent.login.elements.authenticated()) {
                self.remoteCustomFilters.removeAll();
                $.getJSON('/api/filters/', dict, function(data) {
                    $.each(data, function(index, filterDict) {
                        var filter = new CustomFilter(self, parent);
                        filter.filterName(filterDict.name);
                        filter.parameter(filterDict.parameter);
                        filter.searchTerm(filterDict.searchTerm);
                        filter.inversed(filterDict.inversed);
                        filter.enabled(false);

                        self.remoteCustomFilters.push(filter);
                    });
                }).fail(function(data) {
                    swal('Failed GET for all Filters.', JSON.stringify(data), 'error');
                });
            }
        };

        // unused ?
        self.getFiltersForUser = ko.computed(function() {
            if (parent.login.elements.authenticated()) {
                self.fetchAllFilters();
            }
            else {
                self.remoteCustomFilters.removeAll();
            }
        });

        // Setup default filters
        self.defaultFilters = ko.observableArray([]);

        var downFilter = new CustomFilter(self, parent);
        downFilter.filterName('Down');
        downFilter.parameter(downFilter.parameters.applicationStatus);
        downFilter.searchTerm(downFilter.searchTerms.stopped);
        self.defaultFilters.push(downFilter);

        var errorFilter = new CustomFilter(self, parent);
        errorFilter.filterName('Error');
        errorFilter.parameter(errorFilter.parameters.errorState);
        errorFilter.searchTerm(errorFilter.searchTerms.error);
        self.defaultFilters.push(errorFilter);

        self.time = ko.observable(Date.now());
        self.filterByTime = ko.observable(false);
        self.enableTimeFilter = function() {
            // Reset filter time on double click
            if (self.filterByTime()) {
                self.time(Date.now());
            }
            self.filterByTime(true);
            parent.sortByTime();
        };

        self.timeToolTip = ko.computed(function() {
            if (self.filterByTime()) {
                return 'Click to clear old updates';
            }
            return 'Click to enable update mode';
        });
    };
});
