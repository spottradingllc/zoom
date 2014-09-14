requirejs.config({
    baseUrl: 'front-end',
    paths: {
        'text':         './libs/text',
        'durandal':     './libs/durandal',
        'plugins' :     './libs/durandal/plugins',
        'transitions':  './libs/durandal/transitions',
        'knockout':     '//cdnjs.cloudflare.com/ajax/libs/knockout/3.1.0/knockout-min',
        'bootstrap':    '//maxcdn.bootstrapcdn.com/bootstrap/3.2.0/js/bootstrap.min',
        'jquery':       '//code.jquery.com/jquery-2.1.1',
        'd3':           '//cdnjs.cloudflare.com/ajax/libs/d3/3.4.11/d3.min',
        'vkbeautify':   './libs/vkbeautify.0.99.00.beta'
    },
    shim: {
        'bootstrap': {
            deps: ['jquery'],
            exports: 'jQuery'
       }
    }
});

define(['durandal/system', 'durandal/app', 'durandal/viewLocator'],  function (system, app, viewLocator) {
    //>>excludeStart("build", true);
    system.debug(false);
    //>>excludeEnd("build");

    app.title = 'Zoom';

    app.configurePlugins({
        router: true,
        dialog: true
    });

    app.start().then(function() {
        //Replace 'viewmodels' in the moduleId with 'views' to locate the view.
        //Look for partial views in a 'views' folder in the root.
        viewLocator.useConvention();

        //Show the app by setting the root view model for our application with a transition.
        app.setRoot('viewmodels/navbar');
    });
});
