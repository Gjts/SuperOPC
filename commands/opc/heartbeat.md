---
name: opc-heartbeat
description: View current cruise mode status, recent decisions, and autonomous operation health.
---

# /opc-heartbeat

## Usage

```
/opc-heartbeat [--json]
```

## Output

Displays:
- Current cruise mode (watch / assist / cruise / stopped)
- Heartbeat count and last heartbeat timestamp
- Actions executed / skipped / escalated
- Last decision and its zone
- Recent notifications
- Error count and consecutive failure status

## Related

- `/opc-cruise` — Start or stop cruise mode
- `/opc-progress` — Project progress snapshot
- `/opc-dashboard` — Full project dashboard
