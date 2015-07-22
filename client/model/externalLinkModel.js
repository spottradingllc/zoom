define([],
    function() {
        var externalLink = {};

        var urls = {
            prodErrors: 'http://kibanaproduction/index.html#/dashboard/elasticsearch/Errors',
            prodStats: 'http://kibanaproduction/index.html#/dashboard/elasticsearch/Zoom_Production_stats',
            stagingStats: 'http://kibanastaging:9292/index.html#/dashboard/elasticsearch/Zoom_Staging_stats',
            apiDoc: "http://" + document.location.host + "/doc"
         };

        var createLink = function(url) {
            var form = document.createElement("form");
            form.method = "GET";
            form.action = url;
            form.target = "_blank";
            form.submit();
        };

        externalLink.ProdErrorsURL = function() {
            createLink(urls.prodErrors)
        };

        externalLink.ProdStatsURL = function() {
            createLink(urls.prodStats)
        };

        externalLink.StagingStatsURL = function() {
            createLink(urls.stagingStats)
        };
        externalLink.apiDoc = function() {
            createLink(urls.apiDoc)
        };

        return externalLink;
    });



