"""Replace ZoneConfigurationAnalyzer class in MistHelper.py with a delegation stub.

Usage:
    python scripts/replace_zone.py
"""

from pathlib import Path

MISTHELPER = Path("MistHelper.py")

START_MARKER = "class ZoneConfigurationAnalyzer:"
END_MARKER = "class SiteAnalyticsConfigurator:"

STUB = '''\
class ZoneConfigurationAnalyzer:
    """Zone, engagement, and occupancy configuration analysis (Menu 119).

    Implementation extracted to src/analytics/zone_analyzer.py.
    """

    @staticmethod
    def analyze() -> None:
        """Delegate to extracted module."""
        from src.analytics.zone_analyzer import ZoneConfigurationAnalyzer as _ZCA

        _ZCA.analyze(
            apisession=apisession,
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
            check_stop_fn=ConfigUtils.check_stop_signal,
            all_sites_fn=APICoreFetchUtils.all_sites_with_limit,
            save_data_fn=DataExporter.save_data_to_output,
        )


'''


def main() -> None:
    text = MISTHELPER.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if start_idx is None and line.strip() == START_MARKER:
            start_idx = i
        elif start_idx is not None and end_idx is None and line.strip() == END_MARKER:
            end_idx = i
            break

    if start_idx is None:
        raise SystemExit(f"Could not find: {START_MARKER}")
    if end_idx is None:
        raise SystemExit(f"Could not find: {END_MARKER}")

    old_count = end_idx - start_idx
    print(f"Found class at lines {start_idx + 1}-{end_idx} ({old_count} lines)")
    print(f"Replacing with stub ({len(STUB.splitlines())} lines)")

    new_lines = lines[:start_idx] + [STUB] + lines[end_idx:]
    MISTHELPER.write_text("".join(new_lines), encoding="utf-8")
    print("Done.")


if __name__ == "__main__":
    main()
