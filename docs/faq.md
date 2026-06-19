# FAQ

**The cost is far above what I pay for my subscription.**
The numbers are what the same traffic would cost at pay-as-you-go API prices.
A subscription bills differently. The estimate is still useful to compare days,
models and projects with each other.

**A model shows up as unpriced.**
Add it under `[prices]` in the config file, or open an issue with the model id
and a source for its price.

**Totals change between two runs a few seconds apart.**
A running session is still appending to its log. Only completed responses are
counted.

**Why is the first run slow?**
Every log is parsed once and cached. Later runs only re-read files that grew.

**Why does `--since 7d` include eight days?**
`7d` means "seven days ago", and the range is inclusive. Use `6d` for a
seven-day window ending today.

**Can I see usage per git branch?**
Not yet; Claude Code records the branch, the other agents do not.
