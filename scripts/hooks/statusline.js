#!/usr/bin/env node
/**
 * statusline.js — SuperOPC StatusLine Hook
 *
 * Shows: model | current task | directory | context usage
 * Adapted from GSD gsd-statusline.js for SuperOPC ecosystem.
 *
 * Context window display shows USED percentage scaled to usable context.
 * Claude Code reserves ~16.5% for autocompact buffer, so usable context
 * is 83.5% of the total window. We normalize to show 100% at that point.
 *
 * Also writes context metrics to a bridge file for the context-monitor
 * PostToolUse hook, making the AGENT aware of context limits.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

let input = '';
// Timeout guard: exit silently if stdin doesn't close within 3s
const stdinTimeout = setTimeout(() => process.exit(0), 3000);

process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const model = data.model?.display_name || 'Claude';
    const dir = data.workspace?.current_dir || process.cwd();
    const session = data.session_id || '';
    const remaining = data.context_window?.remaining_percentage;

    // --- Context window display ---
    const AUTO_COMPACT_BUFFER_PCT = 16.5;
    let ctx = '';
    if (remaining != null) {
      const usableRemaining = Math.max(
        0,
        ((remaining - AUTO_COMPACT_BUFFER_PCT) / (100 - AUTO_COMPACT_BUFFER_PCT)) * 100
      );
      const used = Math.max(0, Math.min(100, Math.round(100 - usableRemaining)));

      // Write context metrics to bridge file for context-monitor hook
      const sessionSafe = session && !/[/\\]|\.\./.test(session);
      if (sessionSafe) {
        try {
          const bridgePath = path.join(os.tmpdir(), `opc-ctx-${session}.json`);
          const bridgeData = JSON.stringify({
            session_id: session,
            remaining_percentage: remaining,
            used_pct: used,
            timestamp: Math.floor(Date.now() / 1000)
          });
          fs.writeFileSync(bridgePath, bridgeData);
        } catch (_) {
          // Silent fail — bridge is best-effort
        }
      }

      // Build progress bar (10 segments)
      const filled = Math.floor(used / 10);
      const bar = '\u2588'.repeat(filled) + '\u2591'.repeat(10 - filled);

      if (used < 50) {
        ctx = ` \x1b[32m${bar} ${used}%\x1b[0m`;
      } else if (used < 65) {
        ctx = ` \x1b[33m${bar} ${used}%\x1b[0m`;
      } else if (used < 80) {
        ctx = ` \x1b[38;5;208m${bar} ${used}%\x1b[0m`;
      } else {
        ctx = ` \x1b[5;31m\u{1F480} ${bar} ${used}%\x1b[0m`;
      }
    }

    // --- Current task from .opc/STATE.md ---
    let task = '';
    const opcDir = path.join(dir, '.opc');
    const statePath = path.join(opcDir, 'STATE.md');
    if (fs.existsSync(statePath)) {
      try {
        const content = fs.readFileSync(statePath, 'utf8');
        // Extract current task from STATE.md: look for "## Current" or "当前任务"
        const taskMatch = content.match(
          /##\s*(?:Current|当前任务|当前)[^\n]*\n+(?:[-*]\s*)?(.+)/i
        );
        if (taskMatch) {
          task = taskMatch[1].trim().slice(0, 60);
        }
      } catch (_) {
        // Silent fail
      }
    }

    // Fallback: read from Claude Code todos
    if (!task && session) {
      const homeDir = os.homedir();
      const claudeDir = process.env.CLAUDE_CONFIG_DIR || path.join(homeDir, '.claude');
      const todosDir = path.join(claudeDir, 'todos');
      if (fs.existsSync(todosDir)) {
        try {
          const files = fs.readdirSync(todosDir)
            .filter(f => f.startsWith(session) && f.includes('-agent-') && f.endsWith('.json'))
            .map(f => ({ name: f, mtime: fs.statSync(path.join(todosDir, f)).mtime }))
            .sort((a, b) => b.mtime - a.mtime);
          if (files.length > 0) {
            const todos = JSON.parse(fs.readFileSync(path.join(todosDir, files[0].name), 'utf8'));
            const inProgress = todos.find(t => t.status === 'in_progress');
            if (inProgress) task = inProgress.activeForm || '';
          }
        } catch (_) {
          // Silent fail
        }
      }
    }

    // --- SuperOPC update check ---
    let opcUpdate = '';
    const homeDir = os.homedir();
    const cacheFile = path.join(homeDir, '.cache', 'superopc', 'update-check.json');
    if (fs.existsSync(cacheFile)) {
      try {
        const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
        if (cache.update_available) {
          opcUpdate = '\x1b[33m\u2B06 update available\x1b[0m \u2502 ';
        }
      } catch (_) {}
    }

    // --- Output ---
    const dirname = path.basename(dir);
    if (task) {
      process.stdout.write(
        `${opcUpdate}\x1b[2m${model}\x1b[0m \u2502 \x1b[1m${task}\x1b[0m \u2502 \x1b[2m${dirname}\x1b[0m${ctx}`
      );
    } else {
      process.stdout.write(
        `${opcUpdate}\x1b[2m${model}\x1b[0m \u2502 \x1b[2m${dirname}\x1b[0m${ctx}`
      );
    }
  } catch (_) {
    // Silent fail — don't break statusline on parse errors
  }
});
