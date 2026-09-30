# UI Contract: Maps Title Contrast

## Page and Controls

The target page is `/maps`.
The journey uses the existing site selector, map selector, theme selector, and map card.
Their existing `data-testid` attributes remain unchanged.
Plotly supplies the rendered SVG title selector `#plotArea .gtitle`.

## Initial Render

The title text remains the selected map name.
An empty name still selects `Floor Plan`.
The actual title fill equals the computed map card text color.
Its unrounded contrast against the computed map card background is at least 4.5:1.

## Theme Change

A loaded replacement theme updates the existing plot font.
The title uses the new card text color.
The map image, devices, selection, and viewing range remain unchanged.
The page makes no new map data request for the theme change.
Changing a theme before a map exists causes no script error.

## Guard Failure

The original dark gray fill on a dark card must fail the contrast check.
A missing title, missing card, invalid color, or transparent measurement must fail explicitly.
No missing capability may produce a successful browser measurement.
