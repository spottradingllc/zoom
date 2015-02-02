define(['jquery',
        'model/constants'],

    function($, constants) {
        var kibana = {};

        kibana.ProdErrorsURL = function() {
            console.log("Checkpoint 1");
            var form = document.createElement("form");
            form.method = "GET";
            form.action = constants.kibana.prodErrors;
            form.target = "_blank";
            form.submit();
        };

        kibana.ProdStatsURL = function() {
            console.log("Checkpoint 1");
            var form = document.createElement("form");
            form.method = "GET";
            form.action = constants.kibana.prodStats;
            form.target = "_blank";
            form.submit();
        };

        kibana.StagingStatsURL = function() {
            console.log("Checkpoint 1");
            var form = document.createElement("form");
            form.method = "GET";
            form.action = constants.kibana.stagingStats;
            form.target = "_blank";
            form.submit();
        };

        return kibana;
    });



