#!/usr/bin/env node
/**
 * console-log-warn.js — Warn about console.log in edited files
 *
 * Advisory (exit 0). Reminds to remove debug statements.
 */

const fs = require('fs');

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);
  const content = (input.tool_input && (input.tool_input.new_string || input.tool_input.content)) || '';

  if (!content) process.exit(0);

  const debugPatterns = [
    /console\.log\(/,
    /console\.debug\(/,
    /debugger;/,
    /print\(\s*f?["']/,  // Python print
  ];

  const found = debugPatterns.filter(p => p.test(content));
  if (found.length > 0) {
    console.log(
      'SuperOPC: Debug statement detected in edited content. ' +
      'Remember to remove console.log/debugger/print before committing.'
    );
  }
} catch (e) {
  // Silent pass
}

process.exit(0);
