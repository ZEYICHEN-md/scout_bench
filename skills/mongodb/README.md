# MongoDB Skill

Single-skill MongoDB support for the `sourcing_system` database.

This skill stays simple on the outside:

- one skill to install
- one `requirements.txt`
- one main script entry

Internally, it uses collection profiles so `signals` and `companies` stay easier
to maintain without splitting into separate installable skills.

## Install

```bash
pip install -r skills/mongodb/requirements.txt
```

## Configure

Set the connection string explicitly:

```bash
export MONGODB_URI="mongodb://user:pass@host:port/db?authSource=admin"
```

## Collections

- `signals`
- `companies`
- `sector_rankings`
- `ic_sessions`
- `ic_votes`
- `weekly_rankings`
- `manual_inputs`

## Notes and Structure

- The hard-coded MongoDB URI has been removed.
- Shared CRUD helpers now live in `skills/mongodb/scripts/`.
- Collection-specific settings live in `skills/mongodb/profiles/`.
- Main runtime entry remains `skills/mongodb/scripts/mongo_skill.py`.

## Quick Check

```bash
python skills/mongodb/scripts/mongo_skill.py
```
