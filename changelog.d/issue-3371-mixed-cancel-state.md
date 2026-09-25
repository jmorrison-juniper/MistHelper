### Fixed

- The upgrade capture portal no longer reports `completed` for a multi-site upgrade after a cancel that stopped part of the work. If one child job completed and the cancel stopped another child job, the upgrade now reads `cancelled`. The status card, the final note, and the history list show that word. An access point job that completed at one site and stopped at another site also reads `cancelled`. A failed child job still makes the upgrade read `failed` (issue #3371).
