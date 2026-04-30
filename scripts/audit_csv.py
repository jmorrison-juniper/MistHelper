"""Audit mist_ideas.csv for data quality issues."""
import csv
import re


def audit():
    with open("data/mist_ideas.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    print(f"Total rows: {total}")

    # Field emptiness stats
    empty_title = sum(1 for r in rows if not r.get("title", "").strip())
    empty_desc = sum(1 for r in rows if not r.get("description_full", "").strip())
    zero_votes = sum(1 for r in rows if r.get("votes", "0") == "0")
    has_comments = sum(1 for r in rows if int(r.get("comments_count", "0")) > 0)
    empty_status = sum(1 for r in rows if not r.get("status", "").strip())
    empty_submitter = sum(1 for r in rows if not r.get("submitter", "").strip())
    empty_category = sum(1 for r in rows if not r.get("category", "").strip())

    print(f"Empty title:      {empty_title} ({100*empty_title/total:.1f}%)")
    print(f"Empty description: {empty_desc} ({100*empty_desc/total:.1f}%)")
    print(f"Zero votes:       {zero_votes} ({100*zero_votes/total:.1f}%)")
    print(f"Has comments:     {has_comments} ({100*has_comments/total:.1f}%)")
    print(f"Empty status:     {empty_status} ({100*empty_status/total:.1f}%)")
    print(f"Empty submitter:  {empty_submitter} ({100*empty_submitter/total:.1f}%)")
    print(f"Empty category:   {empty_category} ({100*empty_category/total:.1f}%)")
    print()

    # Check title vs URL slug consistency
    slug_match_count = 0
    slug_mismatch_count = 0
    mismatch_examples = []

    for row in rows:
        url = row.get("url", "")
        title = row.get("title", "").lower().strip()
        match = re.search(r"/suggestions/\d+-(.+?)$", url)
        if match and title:
            slug = match.group(1).replace("-", " ").lower()
            slug_first = slug.split()[0] if slug.split() else ""
            title_first = title.split()[0] if title.split() else ""
            if slug_first and title_first:
                if slug_first == title_first:
                    slug_match_count += 1
                else:
                    slug_mismatch_count += 1
                    if len(mismatch_examples) < 8:
                        mismatch_examples.append({
                            "idea_id": row.get("idea_id", ""),
                            "url_slug": slug[:70],
                            "title": title[:70],
                            "desc_len": len(row.get("description_full", "").strip()),
                        })

    print(f"Title matches URL slug: {slug_match_count}")
    print(f"Title MISMATCHES slug:  {slug_mismatch_count}")
    print(f"Mismatch rate: {100*slug_mismatch_count/(slug_match_count+slug_mismatch_count):.1f}%")
    print()

    if mismatch_examples:
        print("=== TITLE/SLUG MISMATCH EXAMPLES ===")
        for ex in mismatch_examples:
            print(f"  idea_id: {ex['idea_id']}")
            print(f"  slug:    {ex['url_slug']}")
            print(f"  title:   {ex['title']}")
            print(f"  desc_len: {ex['desc_len']}")
            print()

    # Status field analysis (what's in there when not empty)
    non_empty_status = [r.get("status", "").strip() for r in rows if r.get("status", "").strip()]
    if non_empty_status:
        print("=== STATUS VALUES (first 5 non-empty, truncated) ===")
        for s in non_empty_status[:5]:
            print(f"  [{s[:80]}]")
        print()


if __name__ == "__main__":
    audit()
