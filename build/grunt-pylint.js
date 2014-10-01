module.exports = function(grunt) {
  'use strict';

  grunt.config.set('pylint', {
    app: {
      options: {
        rcfile: '.pylintrc',
        virtualenv: 'venv',
        messageTemplate: 'parseable',
        disable: ['missing-docstring']
      },
      src: ['server/**/*.py']
    }
  });

  grunt.loadNpmTasks('grunt-pylint');
};