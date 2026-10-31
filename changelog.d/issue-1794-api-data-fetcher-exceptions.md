### Audit API data fetch failures

- **Changed**: The Mist SDK can fail. The fetch method for the Mist API logs each error and checks for a rate limit. If a data export fails, it keeps the fetch error. Issue #1794.
