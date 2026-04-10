#!/usr/bin/env node
/**
 * command-audit-log.js — Audit log bash commands
 *
 * Logs all bash commands with timestamps for session review.
 * Writes to .opc/audit.log (or falls back to console).
 */

const fs = require('fs');
const path = require('path');

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);
  const command = (input.tool_input && input.tool_input.command) || '';

  if (!command) process.exit(0);

  const timestamp = new Date().toISOString();
  const logLine = `[${timestamp}] ${command}\n`;

  // Try to write to .opc/audit.log
  const logDir = path.join(process.cwd(), '.opc');
  const logFile = path.join(logDir, 'audit.log');

  try {
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    fs.appendFileSync(logFile, logLine);
  } catch (writeErr) {
    // Can't write log file — not critical, skip silently
  }
} catch (e) {
  // Silent pass
}

process.exit(0);
