---
name: opc-cruise
description: Start autonomous cruise mode — SuperOPC operates continuously with zone-based permissions.
---

# /opc-cruise

## Usage

```
/opc-cruise [--mode watch|assist|cruise] [--hours N]
```

## Modes

| Mode | GREEN | YELLOW | RED |
|------|-------|--------|-----|
| **watch** | Monitor only | Monitor only | Alert |
| **assist** | Auto-execute | Pause + ask | Alert |
| **cruise** | Auto-execute | Auto-execute (logged) | Pause + alert |

## Behavior

1. Load current `.opc/STATE.md` and `HANDOFF.json`
2. Start heartbeat loop (default: 60s intervals)
3. Each heartbeat:
   - Run health check
   - Ask decision engine for recommended next action
   - Check action's permission zone against current mode
   - Execute or escalate accordingly
   - Update state and write to cruise log

## Safety

- **Emergency stop**: 3+ consecutive failures → automatic shutdown + critical alert
- **RED zone**: Always requires human approval, regardless of mode
- **Duration limit**: Use `--hours N` to auto-stop after N hours
- **All decisions logged**: `.opc/cruise-log/` contains full decision history

## Examples

```
/opc-cruise --mode watch           # Monitor only, alert on issues
/opc-cruise --mode assist          # Handle routine tasks, pause for code changes
/opc-cruise --mode cruise --hours 4 # Full autonomy for 4 hours
```

## Related

- `/opc-heartbeat` — View current cruise status
- `/opc-autonomous` — Single-session bounded autonomy
- `/opc-health` — Manual health check
