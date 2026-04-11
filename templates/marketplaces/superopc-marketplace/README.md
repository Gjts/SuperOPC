# SuperOPC Marketplace Template

This directory is a **template for a separate Claude Code marketplace repository**, not a plugin repository.

## Intended repository split

- `gjts/superopc` — plugin source repository
- `gjts/superopc-marketplace` — marketplace repository

The marketplace repository should have a root layout like:

```text
superopc-marketplace/
├── .claude-plugin/
│   └── marketplace.json
└── README.md
```

## Expected end-user installation flow

After the marketplace repository is live and verified in Claude Code, users should install with:

```text
/plugin marketplace add gjts/superopc-marketplace
/plugin install superopc@superopc-marketplace
```

## Notes

- Keep plugin implementation files (`commands/`, `agents/`, `skills/`, `hooks/`) in the `gjts/superopc` plugin repository.
- Keep marketplace indexing metadata in the separate `gjts/superopc-marketplace` repository.
- If Claude Code requires pinned revisions or a different marketplace `source` shape, update `.claude-plugin/marketplace.json` in the marketplace repository before publication.
