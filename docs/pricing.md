# Pricing

Prices live in `src/tokentally/pricing.py`, in USD per million tokens, split by
provider. `tokentally pricing` prints the table in use, including any overrides
from the config file.

## How a model is matched

1. The model id is lowercased, and any provider prefix is removed
   (`us.anthropic.`, `models/`, a Vertex `publishers/.../` path).
2. An exact entry wins.
3. Otherwise the longest entry that prefixes the id and ends at `-`, `@` or `:`
   is used, so `claude-sonnet-4-5-20250929` uses `claude-sonnet-4-5`, and
   `gpt-50` does not match `gpt-5`.

## Buckets

| Bucket | Anthropic | OpenAI | Google |
|---|---|---|---|
| input | uncached prompt tokens | prompt minus cached | prompt minus cached |
| output | output incl. thinking | output incl. reasoning | output plus thoughts |
| cache write | 5 minute writes at the listed rate, 1 hour writes at 2x input | not billed | not billed |
| cache read | cache hits | cached prompt tokens | cached content tokens |

## Extras

- Responses that report `"speed": "fast"` are priced at twice the standard
  token rates, which is what fast mode costs on the models that offer it.
- Claude web searches add $10 per 1,000 searches on top of the tokens.

## Known gaps

- Long context tiers are applied per request when the prompt (input plus
  cache tokens) exceeds 200k tokens, for Claude Sonnet 4 and 4.5 and Gemini
  Pro. Codex logs report per-turn totals, which match per-request prompts.
- Batch and priority tier pricing are not modeled; logs do not say which was
  used.
- OpenAI and Google prices are best-effort. Override them in the config file
  if your contract differs.
