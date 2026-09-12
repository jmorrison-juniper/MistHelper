# Contract: Theme Init Directive

**Feature**: 016-mermaid-documentation-suite  
**Date**: 2026-03-28

## Purpose

Defines the exact Mermaid `%%{init}%%` directive that MUST be applied to every diagram for consistent T-Mobile dark-mode theming.

## Standard Theme Directive

Every Mermaid code block MUST begin with this directive (before the diagram keyword):

```
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'fontFamily': 'ui-monospace, monospace'
}}}%%
```

## Safety Classification Styles (for flowcharts and mindmaps)

When diagrams color-code operations by safety level, add these classDef rules after the diagram keyword:

```
classDef safe fill:#00C853,stroke:#00C853,color:#1A1A2E
classDef interactiveSafe fill:#FFD600,stroke:#FFD600,color:#1A1A2E
classDef interactive fill:#FFD600,stroke:#FFD600,color:#1A1A2E
classDef websocket fill:#FF6F91,stroke:#FF6F91,color:#1A1A2E
classDef destructive fill:#FF1744,stroke:#FF1744,color:#E0E0E0
classDef wip fill:#448AFF,stroke:#448AFF,color:#E0E0E0
classDef resourceIntensive fill:#A0A0B0,stroke:#A0A0B0,color:#1A1A2E
classDef continuous fill:#A0A0B0,stroke:#A0A0B0,color:#1A1A2E
```

## Diagram-Type-Specific Overrides

### XY Chart
```
%%{init: {'theme': 'dark', 'themeVariables': {
  'xyChart': {
    'titleColor': '#E20074',
    'xAxisLabelColor': '#E0E0E0',
    'yAxisLabelColor': '#E0E0E0',
    'xAxisLineColor': '#FF4DA6',
    'yAxisLineColor': '#FF4DA6',
    'plotColorPalette': '#E20074,#FF6F91,#99004D,#00C853,#FFD600'
  }
}}}%%
```

### Pie Chart
```
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'pie1': '#E20074',
  'pie2': '#FF6F91',
  'pie3': '#99004D',
  'pie4': '#00C853',
  'pie5': '#FFD600',
  'pie6': '#FF1744',
  'pie7': '#448AFF',
  'pie8': '#A0A0B0',
  'pieTitleTextColor': '#E0E0E0',
  'pieSectionTextColor': '#E0E0E0'
}, 'pie': {'textPosition': 0.75}}}%%
```

### Gantt Chart
```
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'gridColor': '#16213E',
  'todayLineColor': '#FF1744'
}}}%%
```

## Compliance Rule

The CI lint script (FR-016) does NOT validate theme directives. Theme consistency is enforced by code review referencing this contract.
