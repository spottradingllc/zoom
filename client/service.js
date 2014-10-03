define(['jquery'], function($) {

    var getUrl = function(path) {
        return '' + location.origin + '/' + path;
    };

    var getCookie = function(c_name) {
        var c_value = document.cookie;
        // c_value looks like: user='foo.bar@spottrading.com'
        var c_start = c_value.indexOf(' ' + c_name + '=');
        if (c_start == -1) {
            c_start = c_value.indexOf(c_name + '=');
        }
        if (c_start == -1) {
            c_value = null;
        }
        else {
            c_start = c_value.indexOf('=', c_start) + 1;
            var c_end = c_value.indexOf(';', c_start);
            if (c_end === -1) {
                c_end = c_value.length;
            }
            c_value = c_value.substring(c_start, c_end);
        }
        return c_value;
    };

    return {
        getCookie: getCookie,

        get: function(path, callback, errorCallback) {
            return $.ajax(getUrl(path), {
                dataType: 'json',
                type: 'GET',
                success: function(data) {
                    return callback(data);
                },
                error: function(jqxhr) {
                    return errorCallback(jqxhr.responseJSON);
                }
            });
        },

        synchronousGet: function(path, callback, errorCallback) {
            return $.ajax(getUrl(path), {
                async: false,
                dataType: 'json',
                type: 'GET',
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
                dataType: 'json',
                type: 'POST',
                success: function(data) {
                    return callback(data);
                },
                error: function(jqxhr) {
                    return errorCallback(jqxhr.responseJSON);
                }
            });
        },

        put: function(path, params, callback, errorCallback) {
            return $.ajax(getUrl(path), {
                data: JSON.stringify(params),
                dataType: 'json',
                type: 'PUT',
                success: function(data) {
                    return callback(data);
                },
                error: function(jqxhr) {
                    return errorCallback(jqxhr.responseJSON);
                }
            });
        },

        del: function(path, params, callback, errorCallback) {
            return $.ajax(getUrl(path), {
                type: 'DELETE',
                success: function(data) {
                    if (callback) {
                        return callback(data);
                    }
                },
                error: function(jqxhr) {
                    if (errorCallback) {
                        return errorCallback(jqxhr.responseJSON);
                    }
                }
            });
        }
    };
});


//  ...modern way of doing things....using promises/futures
//
//  var jqxhr = $.post('/login', JSON.stringify(data), function(response) {
//        console.log('POST (response):' + JSON.stringify(response));
//    });
//
//    jqxhr.fail(function(response) {
//        console.log('POST (response):' + JSON.stringify(response));
//        self.showErrorText(true);
//    });
