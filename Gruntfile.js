module.exports = function(grunt) {
  'use strict';

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json')
  });

  // load tasks and configuration.
  grunt.loadTasks('build');

  grunt.registerTask('lint',
    'Statically analyze the project JavaScript for errors and code style',
    ['jscs', 'jshint', 'pylint']);

  grunt.registerTask('default', ['lint']);
};
