# Address Normalization and Similarity

MistHelper installs `usaddress-scourgify` and `rapidfuzz`. Address comparison for menu 195 uses:

- **Normalization pipeline**: Parse and canonicalize address fields
- **Token sort ratio**: Use `rapidfuzz`, with a `difflib` fallback if `rapidfuzz` is absent
- **Configurable threshold**: Read `ADDRESS_MATCH_THRESHOLD` from `.env`

## Dependencies

These packages are already in `requirements.txt`:

```bash
pip install usaddress-scourgify rapidfuzz
```

## Usage

Run the site address audit:

```bash
python MistHelper.py -M 195
```

The address score helps identify duplicate or near-duplicate site entries across different naming conventions.
