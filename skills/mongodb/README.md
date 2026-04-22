# MongoDB Skill

Single-skill MongoDB support for the `sourcing_system` database.

Keeps one install surface while separating each collection into its own module.

## Install

```bash
pip install -r skills/mongodb/requirements.txt
```

## Configure

Preferred shared config:

```json
{
  "uri": "mongodb://user:pass@host:port/db?authSource=admin"
}
```

Save that JSON to `skills/mongodb/mongodb.json`.

Env var override still works:

```bash
export MONGODB_URI="mongodb://user:pass@host:port/db?authSource=admin"
```

## Collections

- `signals`
- `companies`

## Adding a New Collection

3 steps, minimal blast radius:

1. `profiles/<name>.json` — schema, allowed ops, unique keys
2. `scripts/<name>_ops.py` — collection-specific functions
3. `scripts/mongo_skill.py` — add import block + `__all__` entries

See `SKILL.md` for full templates.

## Structure

```
profiles/         ← per-collection JSON schemas
scripts/
  client.py       ← connection & serialization utils
  base_ops.py     ← profile-driven generic CRUD
  signals_ops.py  ← signals-specific functions
  companies_ops.py← companies-specific functions
  mongo_skill.py  ← unified re-export entry point
```

## Quick Check

```bash
python skills/mongodb/scripts/mongo_skill.py
```
