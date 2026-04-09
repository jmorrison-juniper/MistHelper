# Address Normalization & Similarity

If `usaddress-scourgify` and `rapidfuzz` are installed, address comparison for inventory reconciliation (menu 61) uses:

- **Normalization pipeline**: Parse & canonicalize address fields
- **Token sort ratio**: Fuzzy scoring with rapidfuzz (difflib fallback if rapidfuzz absent)
- **Configurable threshold**: Via future `.env` variable (documented in Agents Guide)

## Dependencies

These are optional -- MistHelper will fall back gracefully if not installed:

```bash
pip install usaddress-scourgify rapidfuzz
```

## Usage

Run inventory diff with address comparison:

```bash
python MistHelper.py -M 61
```

The address similarity scoring helps identify duplicate or near-duplicate site entries across different naming conventions.
