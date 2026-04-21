---
name: autonomous-ops
description: Autonomous operations skill — defines boundaries, permission zones, and escalation rules for AI self-directed execution.
category: intelligence
trigger: When the system needs to decide whether to act autonomously or escalate to human.
id: autonomous-ops
type: meta
tags: [autonomous, zones, permission, cruise, escalation, green-yellow-red]
triggers:
  keywords: [自主, autonomous, 权限区, cruise, 自动执行, green, yellow, red, 升级]
version: 1.4.1
---

# Autonomous Operations

## Purpose

This skill governs **when and how** SuperOPC may act without explicit human instruction. It defines a three-zone permission model that balances speed with safety.

## Permission Zones

### GREEN Zone (Autonomous — No Approval Needed)

Actions the system can execute freely:

- **Health checks**: Run `/opc-health`, verify `.opc/` integrity
- **Test execution**: Run test suites, report results
- **Documentation generation**: Create or update docs from code
- **Intelligence gathering**: Fetch market data, builder feeds, competitive intel
- **Code formatting**: Apply linters, formatters, style fixes
- **Status reporting**: Generate progress, dashboard, session reports
- **Seed/backlog management**: Create seeds, update backlog metadata

### YELLOW Zone (Confirm-then-Execute)

Actions requiring confirmation before execution (in cruise mode, these execute with logging; in assist mode, they pause for approval):

- **Code changes**: Implement features, fix bugs, refactor
- **Dependency upgrades**: Update packages, resolve vulnerabilities
- **Phase advancement**: Move from planning → executing → reviewing
- **PR creation**: Create pull requests
- **Planning**: Generate new plans from requirements
- **Debug cycles**: Investigate and fix issues
- **Session operations**: Resume from handoff, advance to next step

### RED Zone (Human Approval Required — Always)

Actions that **never** execute without explicit human confirmation:

- **Production deployment**: Ship to production environments
- **Database migrations**: Schema changes on live databases
- **Security configuration**: Auth, encryption, access control changes
- **Payment/billing operations**: Anything touching money or subscriptions
- **Destructive operations**: Delete data, force-push, hard reset
- **External API key changes**: Modify third-party service credentials

## Escalation Protocol

When the decision engine encounters ambiguity:

1. **Check zone**: If GREEN, proceed. If RED, halt and notify.
2. **For YELLOW actions in cruise mode**: Execute but log prominently.
3. **For YELLOW actions in assist mode**: Pause, present the decision, wait for approval.
4. **If confidence < 0.5**: Always escalate regardless of zone.
5. **If 3+ consecutive failures**: Halt autonomous execution, switch to assist mode, notify human.
6. **If blocker detected**: Immediately pause, emit `autonomous.blocked` event.

## Anti-Build-Trap Guardrail

Before any autonomous execution of new feature code:

1. Check if `validate-idea` skill has been run for this feature
2. Check if `find-community` skill has evidence of paying demand
3. If neither exists, **refuse to build** and redirect to `/opc-discuss`

This guardrail is **non-negotiable** — it is the Minimalist Entrepreneur's core principle internalized as a system constraint.

## Integration Points

- **Decision Engine**: Consults this skill's zone map for every decision
- **Cruise Controller**: Uses escalation protocol for runtime behavior
- **DAG Engine**: Checks zone before dispatching tasks
- **Event Bus**: Emits `autonomous.proceed` or `autonomous.blocked` events
- **Notification System**: RED zone actions always trigger notifications

## Monitoring

During autonomous operation, the system maintains:

- Decision log in `.opc/decisions/`
- Execution log in `.opc/execution-log/`
- Event journal in `.opc/events/`
- Notification queue in `.opc/notifications/`

All logs are human-readable (JSON + Markdown) and git-trackable.
