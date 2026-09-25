# Research: An empty site never replaces the choices of the operator

**Issue**: #3389 | **Spec**: [spec.md](spec.md)

## D1: Refuse an empty record. Do not skip the site.

An empty record has two causes. The site holds no device, or the inventory
read failed. The route cannot tell the two causes apart. If the route skips
the site, a failed read removes real devices from the plan, and the operator
does not know. A refusal that names the site is the safe answer. The operator
saves again after a temporary failure, or clears the site if it is empty.

The single-site save keeps the answer that the page already showed. That rule
cannot apply to a multi-site save, because the target builder needs the
inventory to fill the fields of each target.

## D2: Refuse a site with no planned device only when another site holds one

A site can answer a record with no target. The site then holds devices, but no
device has a checked type with a target version. The old route added no child
job for that site, and the confirm page showed no sign of it.

If no site holds a target, the old refusal names the "Device types to upgrade"
control. That refusal is correct, and a contract test keeps it. The new refusal
therefore applies only when another site holds a target.

## D3: Read the site names on the refusal path only

`build_site_rows` makes three reads. The accepted save already calls it once
through `selected_rows`. The refusal path calls it one time to get the names.
If the read raises a transport fault, the refusal shows the site identifiers.
The fault must not hide the refusal.

## D4: Show ten names at most

A failed token can empty the record of every selected site. A selection of two
hundred sites would then give a very long message. The message shows ten names,
and then it states the count of the other sites.

## D5: Put the rule in a small class outside the route module

`OrgSiteRecords` collects the targets and the options of each site. It lives in
`src/upgrade_portal/upgrade/org_site_records.py`, and it imports no route
module. `OrgSiteRefusal` is a `ValueError`, so `save_options` already answers it
with status 400 and the message text.

## D6: Give the browser journey its own operator

The stored site set lasts across browser journeys. Other journeys clear only
the first two sites. If this journey fails with the empty site selected, other
journeys would meet the new refusal. A separate operator holds its own site set,
as the recovery journey of issue #3247 does.

## D7: A retry skips the refusal of a site with no planned device

A code review found this case. A retry of issue #3247 chooses the sites of its
failed devices. If the operator clears a device type, or a retry device leaves
its site, a site can hold no retry device. The D2 refusal then told the
operator to clear that site on the Sites page. That page ends the retry, and
the next plan adds the healthy devices again.

The constructor flag `every_site_planned` turns off the D2 refusal for a
retry. The D1 refusal stays, because a failed read must never drop a retry
device with no message. The route reads the retry plan from the request cache,
so the flag adds no store read.

Issue #3396 covers the site that stays in the saved operation, in the
pre-check gate, and in the lock scope.

## D8: A device view with no device counts as an empty record

A second code review found this case. The save reads the inventory of each
site two times. The first read gives the device view, and the second read
gives the record. If the first read fails, the view holds no device. The
record read can still answer, and the site then holds no target. D7 skips such
a site in a retry, so the save dropped the retry devices of that site with no
message.

The route now returns the empty record when the view holds no device. The D1
refusal then names the site, in a retry too. For this case, a plain save gave
the D2 message, which tells the operator to check the device types. The real
cause is a failed read, so the D1 message is correct. The route also makes no
second read of that site.
