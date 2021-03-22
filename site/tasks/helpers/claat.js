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
//
exports.run = (cwd, cmd, env, fmt, ga, o, args, callback) => {
  args.unshift(cmd, '-e', env, '-f', fmt, '-ga', ga, '-o', o);
  const proc = spawn('claat', ["export -ga=UA-41491190-9 -o ../dist/ */*.md"], { stdio: 'inherit', cwd: cwd, env: process.env, shell: true });

  proc.on('close', (e) => {
    if (e) {
      throw new Error(e);
    }
    callback();
  })
};
