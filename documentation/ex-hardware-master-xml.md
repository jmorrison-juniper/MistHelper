# EX hardware master XML

The master XML is one XML file that holds the hardware inventory of every
connected EX switch in a run. A program that reads XML can use it with no
repair. This page describes the file and shows how to check it with common
tools. The format contract is
`specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts/report-xml.md`.

## Where the file comes from

| Front end | When it writes the file | Name |
|-----------|-------------------------|------|
| Menu 309 | Each run that has a result | `data/ExHardwareInventory_<UTC time>.xml`, next to the CSV report |
| WebSockets, Multi Site, output **One combined XML file (.xml)** | At the end of the run | `hardware/inventory.xml` in the run directory |
| WebSockets, Multi Site, output **Combined CSV and XML (.csv + .xml)** | At the end of the run, with the CSV report | `hardware/inventory.xml` and `hardware/inventory.csv` |

The portal download is `GET /api/websockets/batches/<session id>/download?format=xml`.
It returns the media type `application/xml` and a file name with the form
`ExHardwareInventory_<UTC time>.xml`. Both front ends use the same code, so a run
that collects the same switches gives the same file, apart from the time in the
`generated` attribute.

## Structure

```text
mh:hardware-inventory
  mh:organization *        id, name, status [, reason, detail]
    mh:site *              id, name
      mh:device *          id, name, status [, reason, detail]
        <reply root>       exactly one element, only when the status is collected
```

The prefix `mh` stands for the namespace address
`urn:misthelper:ex-hardware-inventory:1`. The wrapper elements belong to that
namespace. Their attributes belong to no namespace. Each reply keeps its own
namespaces and prefixes.

The root element carries these attributes:

| Attribute | Holds |
|-----------|-------|
| `generated` | The time of the report in UTC, `YYYY-MM-DDTHH:MM:SSZ` |
| `scope` | `organization` or `msp` |
| `command` | The fixed command, `show chassis hardware detail \| display xml \| no-more` |
| `organizations` | The number of organization elements |
| `unread` | The number of organizations that Mist could not read |
| `devices` | The number of device elements |
| `collected`, `failed`, `skipped`, `cancelled` | The number of devices with that status. The four numbers add up to `devices`. |

A device has one of four statuses. The statuses equal the statuses of the CSV
report for the same run.

| Status | Meaning | Child element |
|--------|---------|---------------|
| `collected` | The switch returned a valid reply | The reply, exactly one element |
| `failed` | The shell did not give a valid reply | None. `reason` and `detail` say why. |
| `skipped` | The switch was not run, for example because it was offline | None |
| `cancelled` | The operator stopped the run before the switch finished | None |

An organization that Mist could not read has the status `failed`, a reason, a
plain sentence in `detail`, and no site. Each organization, site, and device sorts
by name without case, then by identifier.

## What the file does to a reply

- The file keeps the elements, the attributes, the text, the namespace
  addresses, and the prefixes of the reply.
- The file drops the XML declaration, the comments, and the processing
  instructions of the reply.
- White space that only formats the child elements of an element is replaced by
  the indent of the file, two spaces for each level. All other white space is
  data and stays. This includes all white space below `xml:space="preserve"`.
- A reply with a DTD, an entity declaration, or more than 100 levels of nesting
  never enters the file. Its device has the status `failed` and the detail
  `The saved reply could not be read.`

The tool writes the names from Mist so that the file stays valid. It escapes
`&`, `<`, and `>` in text, and `&`, `<`, `>`, and `"` in an attribute value. It
replaces each character that XML 1.0 forbids with the replacement character
U+FFFD. In the values that it writes itself, it also replaces each character that
XML 1.0 discourages.

## Checks before the file is published

The tool checks the final bytes. A second pass that writes no XML does the work.
A file that fails a check is not published, and the tool says so in one
sentence.

1. The bytes are valid UTF-8 with no byte order mark and the exact first line,
   `<?xml version="1.0" encoding="UTF-8"?>`.
2. The text holds only characters that XML 1.0 allows.
3. A strict parser that knows namespaces reads the document. It refuses a DTD.
4. The names, the attributes, and the order of the wrapper elements follow the
   contract.
5. The counts on the root equal the counts in the document and the counts of the
   run.
6. Each collected device holds exactly one element. Each other device holds none.
7. The events of each embedded reply equal the events of its source. Formatting
   white space and the order of attributes do not count as a difference.
8. A standard canonicalizer reads the whole document.
9. The menu also reads the file back from the disk, and the disk must hold the
   checked bytes.

## Check the file with other tools

The commands below use the file `inventory.xml`. The schema file is
`documentation/schemas/ex-hardware-inventory.xsd`.

Read the file with libxml2 and validate it with the schema:

```bash
xmllint --noout inventory.xml
xmllint --noout --schema documentation/schemas/ex-hardware-inventory.xsd inventory.xml
```

Python with `lxml`:

```python
from lxml import etree

schema = etree.XMLSchema(etree.parse("documentation/schemas/ex-hardware-inventory.xsd"))
tree = etree.parse("inventory.xml", etree.XMLParser(resolve_entities=False, no_network=True))
schema.assertValid(tree)
```

PowerShell with the .NET reader:

```powershell
$settings = New-Object System.Xml.XmlReaderSettings
$settings.DtdProcessing = [System.Xml.DtdProcessing]::Prohibit
$settings.ValidationType = [System.Xml.ValidationType]::Schema
$null = $settings.Schemas.Add("urn:misthelper:ex-hardware-inventory:1", "documentation\schemas\ex-hardware-inventory.xsd")
$reader = [System.Xml.XmlReader]::Create("inventory.xml", $settings)
while ($reader.Read()) { }
$reader.Dispose()
```

The schema describes the wrapper elements. It accepts any reply under a
collected device, because no public schema covers each Junos release. A strict
validator can report one warning for each element of a reply. Those are warnings,
not errors.

Useful XPath expressions, with the prefix `mh` bound to the namespace address:

| Goal | XPath |
|------|-------|
| The reply of each collected switch | `//mh:device[@status='collected']/*` |
| The serial numbers | `//*[local-name()='serial-number']/text()` |
| The switches that did not collect | `//mh:device[@status!='collected']/@name` |
| The organizations that Mist could not read | `//mh:organization[@status='failed']/@name` |

## Limits and messages

- The file stays within the saved-output limit of 64 MiB. In the portal, the
  saved replies and the CSV report use part of that limit first.
- If the file would pass the limit, the menu says `The master XML would pass the
  size limit of 64 MiB. No XML file was written.` The portal marks the output as
  failed and keeps the saved replies and the archive. Run fewer sites to make a
  smaller file.
- If a check fails, the menu says `The master XML file failed its check and was
  removed. See the log for the cause.` The CSV report stays. The log holds the
  kind of the error and no data from the replies.
