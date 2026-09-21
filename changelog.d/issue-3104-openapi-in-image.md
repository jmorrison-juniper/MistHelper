### Fixed

- Menu 243 now works inside the container. The operation generates the SNMP MIB
  from the Mist OpenAPI document, and the image carried no such file, so the
  operation failed on every container run. The registry calls menu 243 safe, so
  the portal listed it and an operator could start it. The image now carries the
  one file that has a runtime reader, which costs 5.3 MB of the 130 MB
  documentation directory. Issue #3104.
- An absent OpenAPI file now names an action. The operator used to read
  `[Errno 2] No such file or directory`, which gives no action to take. The
  message now names the path and the step that restores the file. Issue #3104.
