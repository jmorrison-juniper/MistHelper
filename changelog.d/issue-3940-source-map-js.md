### Security

- Raise the transitive `source-map-js` pin of the operations portal above the
  advisory range. Every pull request failed the `ops-portal` npm audit gate with
  advisory GHSA-68fv-2mgg-jv7q, which allows an event-loop denial of service
  through indexed source-map section offsets. Issue #3940.
