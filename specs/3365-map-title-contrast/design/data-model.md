# Data Model: Maps Title Contrast

This repair adds no database entity, schema, API field, or persistent application state.

## Existing Map View

The existing plot retains its traces, layout images, axis ranges, and selected map.
The repair changes the layout font color only.
The existing map view number still rejects late answers.

## Existing Theme

The theme name remains under the browser key `misthelper-theme`.
The stylesheet link remains `#theme-css`.
The computed text color of the map card supplies the plot font color.

## Test Measurement

The browser returns the title fill, card background, and card text color.
The test rejects a missing element or an unsupported color instead of using a default.
The test computes the contrast from those measurements without rounding.
Screenshots and traces remain in test-controlled directories.
