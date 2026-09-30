# Research: Maps Title Contrast

## Theme Selection

**Decision**: Reuse the existing theme selector without changing `applyTheme`.

**Evidence**: `web_portal/static/js/portal.js` changes the `href` of `#theme-css`.
It also stores the theme name and updates Bootstrap's theme attribute.
It emits no theme-change event.

**Reason**: A listener on the existing stylesheet load event sees the new computed colors.
It also works with a saved theme and a cached stylesheet.

**Alternatives**: A click listener runs before the stylesheet becomes active.
A mutation observer on the link has the same timing defect.
A new global theme event would change unrelated pages.

## Plot Color

**Decision**: Read the computed text color of `#mapContainer`.
Use it as the layout font color.

**Evidence**: Every theme gives the map card its text color through theme CSS.
The current layout sets no font color, so Plotly chooses `#444`.
The plot paper and plotting area are transparent.

**Reason**: The inherited layout font controls the title without changing explicit device label colors.

**Alternatives**: Fixed light and dark values duplicate the theme definitions.
A direct SVG style change would become stale after Plotly redraws.

## Existing Map Update

**Decision**: Use `Plotly.relayout` for the font only.
Skip the update when the plot has no data.
Repeat the font synchronization after the original plot promise completes.

**Reason**: The map must keep its image, traces, viewing range, and selection.
A slow image load can complete after a theme change.
The existing view-number guard must still reject an older map.

**Alternatives**: `Plotly.newPlot` replaces the map and can reset its viewing range.
Polling introduces an unnecessary timer.

## Browser Evidence

**Decision**: Reuse the simulated cloud and map server from `test_map_viewer_image.py`.
Use the actual SVG title fill and actual card background.
Calculate the unrounded WCAG relative-luminance ratio.

**Reason**: A stylesheet assertion cannot prove what Plotly paints.
Rounding a ratio before the assertion can admit a value below 4.5:1.

**Alternatives**: Reusing the older rounded contrast helper would weaken the exact threshold.
Hardcoded expected colors would not measure the active theme.

## Local Environment

The initial validation found no `.venv`.
The system `python3` is Python 3.9 and cannot serve this project.
The Python 3.13 bootstrap then failed while it copied the interpreter.
UV created a working Python 3.13 environment and installed the pinned requirements.
The existing five map browser journeys passed before the repair.
