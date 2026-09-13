# The live checklist of the upgrade rehearsal

## Scope

This checklist holds the facts that the rehearsal cannot prove. The rehearsal
drives the shipped run driver against a stand-in cloud and a driven clock. It
proves every portal rule. It cannot prove that the real cloud accepts the call,
and it cannot prove that the hardware reboots.

This feature does not close issue #1992. A person must decide the live run. No
test of this feature runs scenario C or scenario D against real hardware.

## Warning: the live run reboots the hardware

The live run writes firmware and the device reboots. Issue #2007 records the
result at the test site. One switch carries power over Ethernet for six access
points. The reboot of that switch stops those six access points for about six
minutes. Plan the run for a window in which that outage is acceptable, and tell
the site owner before you start.

## The five items

Each item below needs real hardware. Read each item before the run, and record
the answer after the run.

1. The cloud accepts the upgrade call. The portal sends the call, and the cloud
   answers with an upgrade identifier. Record that identifier.
2. The device reboots. The cloud reports a smaller uptime and the new firmware
   version. Record both readings.
3. The settle gate closes on the real cadence. The device settles inside the
   phase deadline of 1800 seconds. Record the settle moment of each phase.
4. The cancel call reaches the cloud. Press stop during a phase, and read the
   answer. Record which devices the cloud reported in the write state.
5. The post-check capture answers. The portal starts the capture after the
   client phase, and the capture returns a report. Record the report key.
