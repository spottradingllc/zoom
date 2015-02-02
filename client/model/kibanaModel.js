define(['jquery',
        'model/constants'],

    function($, constants) {
        var kibana = {};

        kibana.ProdErrorsURL = function() {
            var form = document.createElement("form");
            form.method = "GET";
            form.action = constants.kibana.prodErrors;
            form.target = "_blank";
            form.submit();
        };

        kibana.ProdStatsURL = function() {
            var form = document.createElement("form");
            form.method = "GET";
            form.action = constants.kibana.prodStats;
            form.target = "_blank";
            form.submit();
        };

        kibana.StagingStatsURL = function() {
            var form = document.createElement("form");
            form.method = "GET";
            form.action = constants.kibana.stagingStats;
            form.target = "_blank";
            form.submit();
        };

        return kibana;
    });



