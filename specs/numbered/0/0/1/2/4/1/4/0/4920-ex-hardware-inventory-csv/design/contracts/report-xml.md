# Contract: Report XML (master XML)

The master XML is one XML file for one run. It holds the reply of each collected switch and one element for each other target. Both front ends write the same structure and apply the same checks. Issue #4933.

## File

- Encoding: UTF-8 with no byte order mark.
- First line: exactly `<?xml version="1.0" encoding="UTF-8"?>`, then a line feed.
- Line end inside the wrapper elements: a line feed.
- CLI name: `ExHardwareInventory_<YYYYMMDDTHHMMSSZ>.xml` in `data/`. It has the stamp and the suffix of the CSV report of the same run.
- Portal name: `hardware/inventory.xml` in the run folder. The download name is `ExHardwareInventory_<UTC time>.xml`.
- Media type: `application/xml`.

## Namespace

The namespace address is `urn:misthelper:ex-hardware-inventory:1`. The files of the tool bind it to the prefix `mh`. The wrapper elements belong to this namespace. Their attributes belong to no namespace. The file declares no default namespace, so a reply that has no namespace keeps it. Each reply keeps its own namespaces and prefixes.

## Structure

```text
mh:hardware-inventory
  mh:organization *        id, name, status [, reason, detail]
    mh:site *              id, name
      mh:device *          id, name, status [, reason, detail]
        <reply root>       exactly one element, only when the status is collected
```

An organization that Mist could not read has the status `failed`, a reason, a detail, and no site. A device that did not collect has no child element.

### Attributes of `mh:hardware-inventory`

| Attribute | Holds |
|-----------|-------|
| `generated` | The time of the report in UTC, `YYYY-MM-DDTHH:MM:SSZ`. |
| `scope` | `organization` or `msp`. |
| `command` | The fixed command: `show chassis hardware detail \| display xml \| no-more`. |
| `organizations` | The number of `mh:organization` elements. |
| `unread` | The number of `mh:organization` elements with the status `failed`. |
| `devices` | The number of `mh:device` elements. |
| `collected`, `failed`, `skipped`, `cancelled` | The number of devices with that status. The four numbers add up to `devices`. |

### Attributes of the other elements

| Element | Attribute | Holds |
|---------|-----------|-------|
| `mh:organization` | `id`, `name` | The identifier and the name of the organization. |
| `mh:organization` | `status` | `read`, or `failed` when Mist could not read it. |
| `mh:organization` | `reason`, `detail` | Present only for `failed`: the reason code and a plain sentence. |
| `mh:site` | `id`, `name` | The identifier and the name of the site. |
| `mh:device` | `id`, `name` | The logical device identifier and the host name. |
| `mh:device` | `status` | `collected`, `failed`, `skipped`, or `cancelled`. The statuses equal the statuses of the CSV report. |
| `mh:device` | `reason`, `detail` | Present when the status is not `collected`: the reason code (it can be empty) and a plain sentence. |

## Order

Organizations sort by name without case, then by identifier. Sites and devices sort the same way inside their parent. Devices with equal keys keep the order of the run. The order has no other meaning.

## The replies

- A reply keeps its elements, attributes, text, namespace addresses, and prefixes. A reader that compares the events of a parser finds no difference between the reply in the file and its source.
- The tool drops the XML declaration, the comments, and the processing instructions of a reply.
- White space that only formats an element is replaced by the indent of the file. That is the white space between the child elements of an element that holds no other text. All other white space is data and stays as it is. This includes all white space below `xml:space="preserve"`.
- The tool indents each level with two spaces. It writes attributes in the order of the source, with double quotes, and it writes an empty element in the short form, `<name/>`.
- A reply with a DTD, an entity declaration, or more than 100 levels of nesting never enters the file. Its device has the status `failed` and the detail `The saved reply could not be read.`

## Characters

- The tool escapes `&`, `<`, and `>` in text, and `&`, `<`, `>`, and `"` in attribute values. It writes a tab, a line feed, and a carriage return in an attribute value as a character reference.
- A character that XML 1.0 forbids becomes U+FFFD. These are the control characters other than tab, line feed, and carriage return, the surrogate code points, U+FFFE, and U+FFFF.
- In the values that the tool writes itself (identifiers, names, reasons), a character that XML 1.0 discourages also becomes U+FFFD. These are U+007F through U+0084, U+0086 through U+009F, U+FDD0 through U+FDEF, and the last two code points of each plane.

## Checks before the file is published

Each check runs on the final bytes. A second pass reads the bytes again with code that does not write XML. A failed check stops the publication, and no file stays.

1. The bytes are valid UTF-8, with no byte order mark and the exact first line.
2. The text holds only characters that the XML 1.0 character rules allow.
3. A strict parser reads the document. The parser knows namespaces. It refuses a DTD and reports any error of well-formedness or of namespaces.
4. The root and its descendants have the names, the attributes, and the order of this contract.
5. The counts on the root equal the counts in the document, and they equal the counts of the run.
6. Each collected device holds exactly one element. Each other device holds none.
7. The events of each embedded reply equal the events of its source. The events are the elements, the attributes, the namespace declarations, the prefixes, and the text. Formatting white space and the order of attributes do not count as a difference.
8. A standard canonicalizer reads the whole document without error.
9. In the CLI, the tool reads the file back from the disk, and the disk must hold exactly the checked bytes. The portal downloads the published file, so the bytes that the operator receives are the bytes that were checked.

## Front ends

| Front end | When the file is written | Name |
|-----------|--------------------------|------|
| CLI menu 309 | Each run that has a result writes the CSV report and the master XML. The two are independent: a refusal of one does not stop the other. | `data/ExHardwareInventory_<stamp>.xml`, next to the CSV report. |
| Portal, output `One combined XML file` (`master-xml`) | At the end of the run. | `hardware/inventory.xml` in the run folder. |
| Portal, output `Combined CSV and XML` (`csv-master-xml`) | At the end of the run, together with the CSV report. Both files appear, or neither does. | `hardware/inventory.csv` and `hardware/inventory.xml`. |

Both front ends call the same builder. For the same run they write the same file, apart from the time in `generated`.

## Limits

- The file stays within the saved-output limit of the run, 64 MiB. In the portal, the replies and the CSV report use part of that limit first.
- A reply stays within the existing limit of 1 MiB, and within 100 levels of nesting.
- A file that passes the limit is not written. The CLI says so in one sentence, and the portal marks the output as failed and keeps the saved replies.

## Schema

`documentation/schemas/ex-hardware-inventory.xsd` is an XML Schema 1.0 document for the wrapper elements. It accepts any reply under a collected device, because no public schema covers each Junos release. The schema accepts each file that the tool writes. A strict validator can report one warning for each element of a reply, because the reply is under a wildcard that is processed in the lax mode. Those are warnings, not errors.

## Independent validation

The unit tests read the document with four standard library readers and a safe parser, and they pin the schema to the constants of the code. The live checks of issue #4933 also read the files of one real run with these readers, which the tool does not use:

- libxml2 through `lxml`, with recovery off and with the schema.
- `xmlschema` with the schema.
- The .NET `XmlReader` with character checks, no DTD, and the schema, then `XmlDocument` and LINQ to XML.
- The canonical form of libxml2 equals the canonical form of the standard library for the same file.

## Example

The values below are invented.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mh:hardware-inventory xmlns:mh="urn:misthelper:ex-hardware-inventory:1" generated="2026-11-25T18:46:06Z" scope="organization" command="show chassis hardware detail | display xml | no-more" organizations="1" unread="0" devices="2" collected="1" failed="1" skipped="0" cancelled="0">
  <mh:organization id="ORG-1" name="Example Org" status="read">
    <mh:site id="SITE-1" name="Example Site">
      <mh:device id="DEV-1" name="ex-switch-01" status="collected">
        <rpc-reply xmlns:junos="http://xml.juniper.net/junos/25.2R0/junos">
          <chassis-inventory xmlns="http://xml.juniper.net/junos/25.2R0/junos-chassis">
            <chassis junos:style="inventory">
              <name>Chassis</name>
              <serial-number>SERIAL-0001</serial-number>
              <description>EX-EXAMPLE-48</description>
            </chassis>
          </chassis-inventory>
          <cli>
            <banner>{master:0}</banner>
          </cli>
        </rpc-reply>
      </mh:device>
      <mh:device id="DEV-2" name="ex-switch-02" status="failed" reason="completion_unproven" detail="The shell did not show a stable prompt."/>
    </mh:site>
  </mh:organization>
</mh:hardware-inventory>
```

## Reading the file

- XPath with the prefix `mh` bound to the namespace address: `//mh:device[@status='collected']/*` selects the reply of each collected switch.
- Serial numbers: `//*[local-name()='serial-number']/text()`.
- Failed devices: `//mh:device[@status!='collected']/@name`.
