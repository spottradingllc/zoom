define([], function () {
    return {
        colors: {
            actionBlue: '#057D9F',
            confirmgreen: '#328332',
            errorRed: '#CC574F',
            successTrans: '',
            unknownGray: '#F7EEDA',
            warnOrange: '#FFAE2F',
            configErrPink: '#FF64DB',
            disabledGray: '#71707F',
            allDepsUpYellow: '#FFE977',
            timeComponentPurple: '#B45CE8'
        },

        glyphs: {
            runningCheck: 'glyphicon glyphicon-ok-circle',
            stoppedX: 'glyphicon glyphicon-remove-circle',
            unknownQMark: 'glyphicon glyphicon-question-sign',
            thumpsUp: 'glyphicon glyphicon-thumbs-up',
            startingRetweet: 'glyphicon glyphicon-retweet',
            stoppingDown: 'glyphicon glyphicon-arrow-down',
            errorWarning: 'glyphicon glyphicon-warning-sign',
            notifyExclamation: 'glyphicon glyphicon-exclamation-sign',
            filledStar: 'glyphicon glyphicon-star',
            emptyStar: 'glyphicon glyphicon-star-empty',
            modeAuto: 'glyphicon glyphicon-sort-by-attributes',
            modeManual: 'glyphicon glyphicon-pause',
            configErr: 'glyphicon glyphicon-resize-small',
            grayed: 'glyphicon glyphicon-user',
            pdWrench: 'glyphicon glyphicon-wrench',
            readOnly: 'glyphicon glyphicon-eye-open',
            staggeredClock: 'glyphicon glyphicon-time',
            invalidTrash: 'glyphicon glyphicon-trash'
        },

        applicationStatuses: {
            running: 'running',
            stopped: 'stopped',
            unknown: 'unknown'
        },

        errorStates: {
            ok: 'ok',
            staggered: 'staggered',
            starting: 'starting',
            started: 'started',
            stopping: 'stopping',
            stopped: 'stopped',
            error: 'error',
            notify: 'notify',
            configErr: 'config_error',
            unknown: 'unknown',
            invalid: 'invalid'
        },

        descriptions: {
            'ok': 'Everything is working as expected.',
            'started': 'Everything is working as expected.',
            'staggered': 'The application is attempting to start, but it is being staggered. This is a means of limiting applications from starting up all at once.',
            'starting': 'The application is starting.',
            'running': 'The application is running.',
            'stopped': 'NOT running.',
            'stopping': 'The application is being stopped.',
            'error': 'The last stop/restart command returned a non-zero exit code.',
            'notify': 'The application has crashed or was brought down outside of Zoom.',
            'config_error': 'Two sentinel agents have configs with the same ID. The configs will need to be updated and the agents will need to be restarted to resolve.',
            'unknown': 'The sentinel agent has lost connection to Zookeeper.',
            'invalid': 'The application was once mapped to this host, but is no longer in that host\'s config. The row/app should likely be deleted.',
            'manual': 'The application is currently ignoring updates from its dependencies.',
            'auto': 'The application will react to updates from its dependencies.',
            'readOnly': 'The application is Read-Only. This means it is brought up/down outside of the normal Zookeeper startup. Zoom only reports whether it is up or down.',
            'grayed': 'Someone has indicated that this application can be ignored. It could be up or down.',
            'pdDisabled': 'PagerDuty alerts originating from Zoom will be ignored.'
        },

        predicateTypes: {
            ZooKeeperHasChildren: 'zookeeperhaschildren',
            ZooKeeperHasGrandChildren: 'zookeeperhasgrandchildren',
            ZooKeeperNodeExists: 'zookeepernodeexists',
            ZookeeperGoodUntilTime: 'zookeepergooduntiltime',
            ZookeeperGlob: 'zookeeperglob',
            Weekend: 'weekend',
            Holiday: 'holiday',
            TimeWindow: 'timewindow',
            Process: 'process',
            Health: 'health',
            API: 'api'
        },

        zkPaths: {
            statePath: '/spot/software/state/',
            appStatePath: '/spot/software/state/application/'
        },

        platform: {
            linux: 0,
            windows: 1
        }
    };
});