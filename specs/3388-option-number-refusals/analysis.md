# Analysis

The shared numeric reader rejects non-ASCII digits and finite values that exceed
their supported maximum. The option mapper keeps unbounded `max_failures` and
stored epoch replay separate, so it does not invent a business maximum.

The local unit and route tests cover superscript digits, 5000-digit values,
finite boundaries, and no-clock epoch replay. The browser test uses the seeded
multi-site options journey to confirm that the refusal hides Python policy text.
