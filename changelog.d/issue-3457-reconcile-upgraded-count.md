### Count each proven device in the counts of a multi-site operation

- **Fixed**: After the multi-site check proves a child job, the progress page
  counts each device of that child job as upgraded. The child row, the
  operation block, and the status poll now show the same counts as the device
  table. A device that the cloud lists as failed stays failed. A child job with
  no proof keeps its counts. Issue #3457.
