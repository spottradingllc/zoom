define(['knockout','./loginModel'], 
function (ko, login) {

    var admin = new Object();

    admin._login = login
    admin._enabled = ko.observable(false);
    admin.disable = function(){
        admin._enabled(false);
    }
    admin.enable = function(){
        if(login.elements.authenticated()){
            admin._enabled(true);
        }
        else{
            alert("You must be logged in to use admin");
        }
    }
    admin.enabled = ko.computed(function(){
        if(login.elements.authenticated()){
            return admin._enabled();
        }
        return false;
    });

    return admin;
});
