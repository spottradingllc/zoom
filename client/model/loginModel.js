define(['knockout', 'service' ], function (ko, service) {

    var login = new Object();
    //var for most recent login - used for password confirmation

    login.elements = {
        username: ko.observable(""),
        password: ko.observable(""),
        showError: ko.observable(false),
        error: ko.observable(""),
        readWrite: ko.observable(false),
        authenticated: ko.observable(false),
        passCheck: false
    };

    login.advertise = ko.computed(function(){
        if(login.elements.authenticated()){
            return login.elements.username()
        }
        else{
            return "Sign In";
        }
    });

    login.setUserFromCookie = function () {
        login.elements.username(service.getCookie("username"));
        if (service.getCookie("read_write")) {
            login.elements.readWrite(true)
        }

        if (login.elements.username() && login.elements.readWrite()) {
            login.elements.authenticated(true)
        }
    };

    login.onSuccess = function(data) {
        login.setUserFromCookie();
        login.elements.passCheck = true;
    };

    login.onFailure = function(data) {
        console.log("FAILED login attempt");
        console.log(JSON.stringify(data));
        //alert(JSON.stringify(data));
        login.elements.passCheck = false;
    };

    login.submit = function() {
        
        var params = {
            username: login.elements.username(),
            password: login.elements.password()
        };

        return service.post('login', params, login.onSuccess, login.onFailure);
           
    };


    login.reset = function () {
        login.elements.username("");
        login.elements.password("");
        login.elements.authenticated(false);
        login.submit();
    };

    login.setUserFromCookie()

    return login;
});
