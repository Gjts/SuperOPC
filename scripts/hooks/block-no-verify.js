#!/usr/bin/env node
/**
 * block-no-verify.js — Block git --no-verify flag
 *
 * Prevents bypassing pre-commit, commit-msg, and pre-push hooks.
 * Exit code 2 = block the tool call.
 */

const fs = require('fs');

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);
  const command = (input.tool_input && input.tool_input.command) || '';

  if (/--no-verify/.test(command)) {
    console.log(
      'SuperOPC: --no-verify flag detected. ' +
      'Pre-commit hooks exist for a reason — they protect code quality. ' +
      'Remove --no-verify and fix the underlying issue instead.'
    );
    process.exit(2);
  }
} catch (e) {
  // Silent pass on parse errors — don't block normal operations
}

process.exit(0);
