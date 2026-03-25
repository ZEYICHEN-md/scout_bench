# OpenClaw Configuration

My personal OpenClaw configuration and custom skills.

## Structure

```
├── AGENTS.md          # Agent behavior and memory rules
├── SOUL.md            # Persona and tone definition
├── USER.md            # User profile
├── IDENTITY.md        # Agent identity
├── TOOLS.md           # Local tool notes
├── MEMORY.md          # Long-term memory
├── HEARTBEAT.md       # Periodic task definitions
├── skills/            # Custom skills
│   └── domain-digger/ # Domain name discovery tool
├── config/
│   └── openclaw.json.example  # Configuration template (sensitive values removed)
└── .gitignore
```

## Custom Skills

### domain-digger

Generate concise .com domain name ideas based on intent and check availability.

Usage: The skill triggers on phrases like "find me a domain", "domain name ideas", "帮我找域名".

## Setup

1. Copy `config/openclaw.json.example` to `~/.openclaw/openclaw.json`
2. Fill in your own sensitive values:
   - `channels.telegram.botToken` - Your Telegram bot token
   - `gateway.auth.token` - Your gateway auth token
3. Symlink or copy `skills/` to `~/.openclaw/skills/`

## Security

- Never commit `openclaw.json` with real tokens
- `.gitignore` excludes `.openclaw/` directory with sensitive data
