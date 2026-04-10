#!/usr/bin/env node
/**
 * prompt-injection-scan.js — Scan for prompt injection patterns
 *
 * Advisory (exit 0). Detects known prompt injection patterns in files
 * being written. Warns but never blocks.
 *
 * Source: GSD prompt-guard pattern
 */

const fs = require('fs');

const INJECTION_PATTERNS = [
  /ignore\s+(all\s+)?previous\s+instructions/i,
  /you\s+are\s+now\s+a\s+different/i,
  /disregard\s+(all\s+)?(prior|previous)/i,
  /system\s*:\s*you\s+are/i,
  /\[INST\]/i,
  /<\|im_start\|>/i,
  /\u200B/,  // Zero-width space
  /\u200C/,  // Zero-width non-joiner
  /\u200D/,  // Zero-width joiner
  /\uFEFF/,  // BOM in unusual position
];

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);
  const content = (input.tool_input && (input.tool_input.content || input.tool_input.new_string)) || '';

  if (!content) process.exit(0);

  const findings = [];
  for (const pattern of INJECTION_PATTERNS) {
    if (pattern.test(content)) {
      findings.push(pattern.source);
    }
  }

  if (findings.length > 0) {
    console.log(
      'SuperOPC: Potential prompt injection pattern detected in file content.\n' +
      '  Patterns: ' + findings.slice(0, 3).join(', ') + '\n' +
      '  This is advisory — review the content to confirm it is intentional.'
    );
  }
} catch (e) {
  // Silent pass
}

process.exit(0);
