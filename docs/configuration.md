# Configuration

tokentally reads an optional TOML file. `tokentally config path` prints where it
looks and `tokentally config init` writes a commented starter file.

Lookup order:

1. `$TOKENTALLY_CONFIG`
2. `$XDG_CONFIG_HOME/tokentally/config.toml`
3. `~/.config/tokentally/config.toml`

## `[defaults]`

Default values for command line options, using the option name with dashes
replaced by underscores. Command line flags always win.

```toml
[defaults]
tz = "Europe/Berlin"
source = ["claude", "codex"]
sort = "cost"
svg_theme = "dark"
```

Unknown keys and invalid values are reported as config errors rather than being
ignored.

## `[paths]`

Extra or replacement log directories per source. A string or a list.

```toml
[paths]
claude = ["~/.claude/projects", "/mnt/backup/claude/projects"]
```

## `[prices]`

Add a model or override a built-in price. Values are USD per million tokens.
Lookups match the longest configured name that prefixes the model id.

```toml
[prices."claude-sonnet-4-5"]
input = 3.0
output = 15.0
cache_write = 3.75
cache_read = 0.30
```

## `[budget]`

Spending limits in USD. `tokentally summary` shows today's and this month's
estimated spend against them, in yellow from 80% and red once exceeded.

```toml
[budget]
daily = 20
monthly = 400
```
