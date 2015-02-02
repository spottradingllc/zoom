define(['jquery',
        'model/constants'],

    function($, constants) {
        var kibana = {};

        var url = {
            prodErrors: 'http://kibanaproduction:9292/index.html#/dashboard/elasticsearch/Errors',
            prodStats: 'http://kibanaproduction:9292/index.html#/dashboard/elasticsearch/Zoom_Production_stats',
            stagingStats: 'http://kibanastaging:9292/index.html#/dashboard/elasticsearch/Zoom_Staging_stats'
         }

        kibana.ProdErrorsURL = function() {
            var form = document.createElement("form");
            form.method = "GET";
            form.action = url.prodErrors;
            form.target = "_blank";
            form.submit();
        };

        kibana.ProdStatsURL = function() {
            var form = document.createElement("form");
            form.method = "GET";
            form.action = url.prodStats;
            form.target = "_blank";
            form.submit();
        };

        kibana.StagingStatsURL = function() {
            var form = document.createElement("form");
            form.method = "GET";
            form.action = url.stagingStats;
            form.target = "_blank";
            form.submit();
        };

        return kibana;
    });



