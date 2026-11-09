# Menu contract

Selection cancellation sends no request.
A successful empty page preserves the existing no-data message.
A complete export writes every row once with the existing filename and endpoint metadata.
An HTTP failure, absent status, missing promised page, or malformed payload produces failure feedback without writing.
Failure messages include only fixed text and validated integer status values.
No exporter message includes an exception, response body, or next-page URL.
Local transformation and writer exceptions continue to reach the caller.
