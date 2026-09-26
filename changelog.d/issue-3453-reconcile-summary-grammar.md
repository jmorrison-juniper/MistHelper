### State the correct device noun in the multi-site check result

- **Fixed**: The portal now states the correct device noun in the check
  result of a multi-site child job. For one device, the result reads "The
  target version runs on 0 of 1 device". For two or more devices, the result
  keeps the plural noun. The progress page and the stored record show the
  same text. A record of an earlier check keeps its old text. Issue #3453.
