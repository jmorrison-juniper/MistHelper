# CSV Output Contract

The CSV reader returns literal `\r` for each input carriage return. String fields retain the existing
line-feed escaping. List fields retain their existing line-feed behavior after conversion.
The order of both characters remains unchanged. Non-CSV output receives no new carriage-return escaping.
CSV output does not mutate its input records.
