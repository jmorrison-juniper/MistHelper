# Class of service

## Contents

1. [Source scope](#source-scope)
2. [Forwarding classes and queues](#forwarding-classes-and-queues)
3. [Classifiers and marking](#classifiers-and-marking)
4. [Schedulers and scheduler maps](#schedulers-and-scheduler-maps)
5. [Shapers, policers, and drop profiles](#shapers-policers-and-drop-profiles)
6. [Verification commands](#verification-commands)

## Source scope

Use this reference for Junos class-of-service work on routers, switches, and
security devices. Keep platform families separate when a source does so.

Primary sources:

- `cos`: Junos OS Class of Service User Guide for Routers, Junos 26.2.
- `cos-ex`: Junos OS for EX Series Ethernet Switches Class of Service User
  Guide, Junos 26.2.
- `cos-security-devices`: Junos OS Class of Service User Guide for Security
  Devices, Junos 26.2.
- `cos-hierarchical`: Junos OS Hierarchical Class of Service User Guide,
  Junos 26.2.

Warning: a class-of-service change can starve traffic when queues, rates, or
drop rules are wrong. Verify queue counters before and after the change.

## Forwarding classes and queues

A forwarding class maps traffic to an output queue. Configure the forwarding
class before you attach schedulers or rewrite rules to that traffic.

```text
set class-of-service forwarding-classes class video queue-num 4
```

Verify the result:

```text
show configuration class-of-service forwarding-classes
```

Source: Junos OS for EX Series Ethernet Switches Class of Service User Guide,
Junos 26.2, page 24.

## Classifiers and marking

### Configure a behavior aggregate classifier

A behavior aggregate classifier reads a code point that already exists in the
packet. The classifier then assigns a forwarding class and loss priority.

```text
edit class-of-service classifiers dscp ba-classifier
set forwarding-class be-class loss-priority high code-points 000001
```

Apply the classifier to an interface unit:

```text
set class-of-service interfaces ge-0/0/1 unit 0 classifiers dscp dscp_custom
```

Verify the result:

```text
show configuration class-of-service classifiers
show configuration class-of-service interfaces
```

Sources:

- Junos OS Class of Service User Guide for Routers, Junos 26.2, page 119.
- Junos OS Class of Service User Guide for Security Devices, Junos 26.2,
  page 201.

### Configure a multifield classifier

A multifield classifier uses a firewall filter. The filter can match several
packet fields, then assign a forwarding class or loss priority.

```text
set firewall family inet filter f1 term t1 then loss-priority high
set firewall family inet filter mf-classifier term BE-data then forwarding-class BE-data
```

Apply the classifier as an input filter:

```text
set interfaces ge-2/0/5 unit 0 family inet filter input mf-classifier
```

Verify the result:

```text
show firewall
show configuration interfaces
```

Sources:

- Junos OS for EX Series Ethernet Switches Class of Service User Guide,
  Junos 26.2, page 105.
- Junos OS Class of Service User Guide for Routers, Junos 26.2, page 252.

### Configure a rewrite rule

A rewrite rule marks packets as they leave the device.

```text
edit class-of-service rewrite-rules dscp rewrite-dscps
set forwarding-class be-class loss-priority low code-point 000000
set class-of-service interfaces ge-2/0/8 unit 0 rewrite-rules dscp IPv4-rewrite-table
```

Verify the result:

```text
show class-of-service
show configuration class-of-service interfaces
```

Sources:

- Junos OS Class of Service User Guide for Security Devices, Junos 26.2,
  page 123.
- Junos OS Class of Service User Guide for Routers, Junos 26.2, page 620.

## Schedulers and scheduler maps

### Configure scheduler priority and rates

A scheduler gives a queue its priority, transmit rate, and buffer size.

```text
set class-of-service schedulers video-sched priority low
set class-of-service schedulers video-sched transmit-rate percent 15
set class-of-service schedulers db-sched buffer-size percent 10
set class-of-service schedulers nc-sched priority strict-high
```

Verify the result:

```text
show class-of-service
```

Source: Junos OS for EX Series Ethernet Switches Class of Service User Guide,
Junos 26.2, page 26.

### Map forwarding classes to schedulers

A scheduler map binds each forwarding class to one scheduler.

```text
set class-of-service scheduler-maps ethernet-cos-map forwarding-class mail scheduler mail-sched
```

Verify the result:

```text
show class-of-service scheduler-map
```

Source: Junos OS for EX Series Ethernet Switches Class of Service User Guide,
Junos 26.2, page 26.

## Shapers, policers, and drop profiles

### Shape an interface

Warning: a shaper can cap traffic below demand. Verify the service rate before
you commit the change.

```text
set class-of-service interfaces ge-0/0/0 shaping-rate 100m
```

Verify the result:

```text
show configuration class-of-service interfaces
```

Source: Junos OS for EX Series Ethernet Switches Class of Service User Guide,
Junos 26.2, page 24.

### Configure a policer action

Warning: a policer can drop or remark traffic. Verify the threshold and traffic
class before you commit the change.

```text
set firewall policer policer_IFL then loss-priority high
set firewall policer policer_IFL then forwarding-class best-effort
```

Attach the policer to an interface unit:

```text
set interfaces ge-1/3/1 unit 0 family inet policer input policer_IFL
```

Verify the result:

```text
show firewall
show configuration interfaces
```

Source: Junos OS Class of Service User Guide for Security Devices, Junos 26.2,
page 68.

### Configure a drop profile and WRED

Weighted random early detection drops packets before a queue is full. Lower
fill levels and higher drop probabilities make drops more likely.

```text
set class-of-service drop-profiles dp-low interpolate fill-level 80 drop-probability 80
set class-of-service drop-profiles dp-low interpolate fill-level 100 drop-probability 100
set class-of-service drop-profiles dp-high interpolate fill-level 60 drop-probability 80
set class-of-service drop-profiles dp-high interpolate fill-level 80 drop-probability 100
```

Verify the result:

```text
show class-of-service
```

Source: Junos OS Class of Service User Guide for Security Devices, Junos 26.2,
page 302.

## Verification commands

Use these commands before and after a class-of-service change.

| Task | Command | Source |
| - | - | - |
| Check queue counters. | `show interfaces extensive ge-0/0/1 | find "queue counters"` | Class of Service for Routers, Junos 26.2, page 57. |
| Check forwarding classes. | `show configuration class-of-service forwarding-classes` | Class of Service for EX Series, Junos 26.2, page 24. |
| Check classifiers. | `show configuration class-of-service classifiers` | Class of Service for Routers, Junos 26.2, page 119. |
| Check schedulers. | `show class-of-service scheduler-map` | Class of Service for EX Series, Junos 26.2, page 45. |
| Check drop profiles. | `show class-of-service` | Class of Service for Security Devices, Junos 26.2, page 2. |
