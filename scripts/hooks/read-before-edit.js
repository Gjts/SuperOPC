#!/usr/bin/env node
/**
 * read-before-edit.js — Warn when editing unread files
 *
 * Advisory hook (exit 0). Reminds the AI to read a file before
 * editing it, preventing infinite retry loops in non-Claude runtimes.
 *
 * Source: GSD read-guard pattern
 */

const fs = require('fs');

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);
  const filePath = (input.tool_input && (input.tool_input.file_path || input.tool_input.path)) || '';

  if (filePath) {
    console.log(
      'SuperOPC: Ensure you have read "' + filePath + '" before editing. ' +
      'Reading first prevents edit failures from outdated content assumptions.'
    );
  }
} catch (e) {
  // Silent pass
}

process.exit(0);
