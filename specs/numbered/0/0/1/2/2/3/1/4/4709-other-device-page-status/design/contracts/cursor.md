# Cursor safety

The coordinator requested repeated-cursor protection after the first local #4709 repair commit.
Preserve `4ee8f9d5bae65dfe16d784fa391a97dee82d088f` and add a separate local commit.

`PickerPageReader.read` and `PolicyResponse.collect` keep a set of requested cursor strings.
Their domain-specific exceptions cannot serve this exporter without importing unrelated feature contracts.
Use the same progress invariant locally with fixed error messages.

A `None` or exact empty-string cursor marks completion.
Every other cursor must be a nonblank string not previously requested during this export.
The documented string has no `minLength`, and installed `mistapi.get_all` treats `""` as terminal.
This corrects the earlier instruction to reject every blank cursor.
Validate the cursor before sending its next request.
Never log the cursor value.
Require dictionary rows in both direct lists and `results` lists.
Malformed rows cannot prove a complete export.

This additional contract stays under `contracts/` to preserve the five-child directory limit.
