requirejs.config({
    baseUrl: 'front-end',
    paths: {
        'text':         './libs/text',
        'durandal':     './libs/durandal',
        'plugins' :     './libs/durandal/plugins',
        'transitions':  './libs/durandal/transitions',
        'knockout':     './libs/knockout-3.1.0',
        'bootstrap':    './libs/bootstrap.min',
        'jquery':       './libs/jquery-2.1.1.min',
        'd3':           './libs/d3',
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
    system.debug(true);

    app.title = 'Zoom';

    app.configurePlugins({
        router:true,
        dialog: true
    });

    app.start().then(function() {
        //Replace 'viewmodels' in the moduleId with 'views' to locate the view.
        //Look for partial views in a 'views' folder in the root.
        viewLocator.useConvention();

        //Show the app by setting the root view model for our application with a transition.
        app.setRoot('viewmodels/navbar', 'entrance');
    });
});
