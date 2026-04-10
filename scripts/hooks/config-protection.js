#!/usr/bin/env node
/**
 * config-protection.js — Warn when modifying linter/formatter configs
 *
 * Advisory (exit 0). Steers toward fixing code instead of weakening configs.
 * Source: ECC config-protection pattern
 */

const fs = require('fs');
const path = require('path');

const CONFIG_FILES = [
  '.eslintrc', '.eslintrc.js', '.eslintrc.json', '.eslintrc.yml',
  'eslint.config.js', 'eslint.config.mjs',
  '.prettierrc', '.prettierrc.js', '.prettierrc.json',
  'prettier.config.js', 'prettier.config.mjs',
  'tsconfig.json', 'tsconfig.build.json',
  '.stylelintrc', '.stylelintrc.json',
  'biome.json', 'biome.jsonc',
  '.editorconfig'
];

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);
  const filePath = (input.tool_input && (input.tool_input.file_path || input.tool_input.path)) || '';

  if (!filePath) process.exit(0);

  const basename = path.basename(filePath);
  if (CONFIG_FILES.includes(basename)) {
    console.log(
      'SuperOPC: Modifying linter/formatter config "' + basename + '". ' +
      'Consider fixing the code to comply with existing rules instead of weakening the config.'
    );
  }
} catch (e) {
  // Silent pass
}

process.exit(0);
