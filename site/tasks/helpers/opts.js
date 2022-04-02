'use strict';

const autoprefixer = require('autoprefixer');
const closureCompilerPackage = require('google-closure-compiler');
const cssdeclarationsorter = require('css-declaration-sorter');
const cssnano = require('cssnano');
const fs = require('fs')

exports.babel = () => {
  return {
    presets: ['es2015'],
  };
};

exports.closureCompiler = () => {
  return {
    compilation_level: 'ADVANCED',
    warning_level: 'VERBOSE',
    language_out: 'ECMASCRIPT5_STRICT',
    generate_exports: true,
    export_local_property_definitions: true,
    output_wrapper: '(function(window, document){\n%output%\n})(window, document);',
    js_output_file: 'cardsorter.js',
  };
};

exports.crisper = () => {
  return {
    scriptInHead: false,
  };
};

exports.htmlmin = () => {
  return {
    collapseWhitespace: true,
    conservativeCollapse: true,
    preserveLineBreaks: true,
    removeComments: true,
    useShortDoctype: true,
  };
};

exports.postcss = () => {
  return [
    autoprefixer({
    }),
    cssdeclarationsorter({ order: 'alphabetically' }),
    cssnano(),
  ];
};

exports.sass = () => {
  return {
    outputStyle: 'expanded',
    precision: 5,
  };
};

exports.uglify = () => {
  return {
    compress: {
      drop_console: true,
      keep_infinity: true,
      passes: 5,
    },
    output: {
      beautify: false,
    },
    toplevel: false,
  };
};

exports.vulcanize = () => {
  return {
    excludes: ['prettify.js'], // prettify produces errors when inlined
    inlineCss: true,
    inlineScripts: true,
    stripComments: true,
    stripExcludes: ['iron-shadow-flex-layout.html'],
  };
};

exports.webserver = () => {
  const webserverOpts = {
    livereload: false,
  }
  // If docker,
  try {
    if (fs.existsSync('/.dockerenv')) {
      // then export server to host
      webserverOpts.host = '0.0.0.0';
    }
  } catch(err) {}
  return webserverOpts;
};
