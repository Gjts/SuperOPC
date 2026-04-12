---
name: opc-profile
description: View or refresh the developer profile — 8 dimensions of work style that personalize SuperOPC behavior.
---

# /opc-profile

## Usage

```
/opc-profile [--refresh] [--json]
```

## Behavior

### View Profile
Without flags, displays the current 8-dimension developer profile:
1. **Communication style**: terse / balanced / verbose
2. **Decision pattern**: intuitive / analytical / consensus-seeking
3. **Debugging preference**: systematic / intuitive / log-driven
4. **UX aesthetic**: minimalist / feature-rich / data-dense
5. **Tech stack affinity**: Detected from project history
6. **Friction triggers**: Patterns that cause frustration
7. **Learning style**: hands-on / conceptual / example-driven
8. **Explanation depth**: brief / moderate / deep

### Refresh Profile
With `--refresh`, re-analyzes session history and interaction patterns to update inferred dimensions.

## Storage

Profile is stored globally at `~/.opc/USER-PROFILE.json` and shared across all projects.

## Related

- `/opc-dashboard` — Project dashboard (includes profile-influenced recommendations)
- `/opc-start` — Profile is consulted during project initialization
