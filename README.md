# tokentally

[![ci](https://github.com/OWNER/tokentally/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/tokentally/actions/workflows/ci.yml)
[![pypi](https://img.shields.io/pypi/v/tokentally.svg)](https://pypi.org/project/tokentally/)
[![python](https://img.shields.io/pypi/pyversions/tokentally.svg)](https://pypi.org/project/tokentally/)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Count the tokens your AI coding agents burn.

`tokentally` reads the session logs that Claude Code, Codex CLI and Gemini CLI
already write to your home directory, adds up the tokens per day, model,
session or project, and estimates what that usage would cost at API prices.
Nothing leaves your machine.

## Install

```sh
pip install tokentally
```

## Usage

```sh
tokentally              # daily report (same as `tokentally daily`)
tokentally models       # one row per model
tokentally monthly --since 2026-01-01
tokentally sessions --sort cost --limit 10
tokentally projects --source claude --format json
```
