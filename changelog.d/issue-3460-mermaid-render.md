### Fixed

- The Mermaid diagrams on the menu API endpoint wiki pages now fit the wiki column and render. GitHub cut off the bottom of 223 of 289 diagrams, because long request paths and names made each diagram wider than the column. The generator now breaks each label into short lines. Each category page now has one overview diagram that links the category to its most used SDK families, instead of up to seven diagrams of crossing edges.
- GitHub did not render the last diagrams of a page with more than about 60 diagrams. A menu option with fewer than three endpoints now has no diagram, because its table shows the same endpoints. The largest page now has 27 diagrams. (#3460)
