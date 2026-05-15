"""Quick integration test for audit analysis pipeline using real data."""

import json
import os
import sys

sys.path.insert(0, ".")

from src.audit.analyzer import AuditLogAnalyzer
from src.audit.filter import AuditLogFilter
from src.audit.renderer import AuditReportRenderer

with open("data/orgaudit-filtered.json") as f:
    data = json.load(f)

entries = data["results"]
print(f"Raw entries: {len(entries)}")

filt = AuditLogFilter()
filtered, stats = filt.filter_with_stats(entries)
print(f"After filter: {stats}")

analyzer = AuditLogAnalyzer()
result = analyzer.analyze(filtered, time_range_description="Test run from orgaudit-filtered.json")
print(f"Admins: {len(result.admin_timelines)}")
print(f"Objects modified: {len(result.object_changelogs)}")
print(f"Rollback diffs: {len(result.rollback_diffs)}")

for timeline in result.admin_timelines:
    print(f"  - {timeline.admin_name}: {timeline.action_count} actions")

renderer = AuditReportRenderer()
renderer.render_mermaid(result, "data/OrgAuditAnalysis.md")
renderer.render_html(result, "data/OrgAuditAnalysis.html")

md_size = os.path.getsize("data/OrgAuditAnalysis.md")
html_size = os.path.getsize("data/OrgAuditAnalysis.html")
print(f"MD size: {md_size} bytes")
print(f"HTML size: {html_size} bytes")
print("SUCCESS - both reports generated")
