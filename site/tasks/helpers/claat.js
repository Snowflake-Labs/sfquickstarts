'use strict';

const childprocess = require('child_process');
const spawn = childprocess.spawn;

// claat is a wrapper around the claat tool.
//
//   cwd - codelabs content dir
//   cmd - claat command, either 'update' or 'export'
//   fmt - output format, e.g. 'html'
//   ga - google analytics tracking code
//   args - an array of source doc IDs or codelab names (IDs)
//   callback - an async task callback function
//   prefix - prefix for codelab-elements
//
exports.run = (cwd, cmd, env, fmt, ga, o, prefix, args, callback) => {
  args.unshift(cmd, '-e', env, '-f', fmt, '-ga', ga, '-o', o, '-prefix', prefix);
  const proc = spawn('claat', args, { stdio: 'inherit', cwd: cwd, env: process.env, shell: true });

  proc.on('close', (e) => {
    if (e) {
      throw new Error(e);
    }
    callback();
  })
};
