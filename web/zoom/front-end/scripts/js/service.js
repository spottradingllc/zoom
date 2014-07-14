define(['jquery', 'knockout'],
function($, ko) {
    var getUrl;
    getUrl = function(path) {
        return "" + location.origin + "/" + path;
    };

    return {
        get: function(path, callback, errorCallback) {
            return $.ajax(getUrl(path), {
                dataType: 'json',
                type: "GET",
                success: function(data) {
                    return callback(data);
                },
                error: function(jqxhr) {
                    return errorCallback(jqxhr.responseJSON);
                }
            });
        },

        post: function(path, params, callback, errorCallback) {
            return $.ajax(getUrl(path), {
                data: JSON.stringify(params),
                dataType: "json",
                type: "POST",
                success: function(data) {
                    return callback(data);
                },
                error: function(jqxhr) {
                    return errorCallback(jqxhr.responseJSON);
                }
            });
        }
    };
});


//  ...modern way of doing things....using promises/futures
//
//  var jqxhr = $.post("/login", JSON.stringify(data), function (response) {
//        console.log("POST (response):" + JSON.stringify(response));
//    });
//
//    jqxhr.fail(function (response) {
//        console.log("POST (response):" + JSON.stringify(response));
//        self.showErrorText(true);
//    });