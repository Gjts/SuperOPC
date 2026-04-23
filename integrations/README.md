# Integrations Output

`integrations/` is a generated-output directory.

Source of truth lives in:

- `agents/`
- `commands/`
- `skills/`
- `scripts/convert.py`

Do not manually edit runtime files under `integrations/<tool>/`.

Regenerate them with:

```bash
python scripts/convert.py --tool all
```

Use this directory only to inspect or smoke-test exported runtime packages.
