import csv
import sqlite3
from pathlib import Path
import logging


class Exporter:
    """Export Phase 1 results to CSV and SQLite."""

    def write(self, rows, outdir: str = "data/ssid-consolidation", basename: str = "matrix"):
        path = Path(outdir)
        path.mkdir(parents=True, exist_ok=True)
        csv_path = path / f"{basename}.csv"

        if rows:
            keys = list(rows[0].keys())
        else:
            keys = []

        try:
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for r in rows:
                    writer.writerow({k: (r.get(k) if r.get(k) is not None else "") for k in keys})
        except Exception:
            logging.exception("Failed to write CSV export")

        # SQLite export
        db_path = path / f"{basename}.db"
        try:
            con = sqlite3.connect(str(db_path))
            cur = con.cursor()
            if keys:
                cols = ", ".join([f'"{k}" TEXT' for k in keys])
                cur.execute(f"CREATE TABLE IF NOT EXISTS phase1_matrix ({cols})")
                cur.execute("DELETE FROM phase1_matrix")
                for r in rows:
                    vals = [str(r.get(k, "")) for k in keys]
                    placeholders = ",".join(["?" for _ in vals])
                    cur.execute(
                        f"INSERT INTO phase1_matrix ({','.join([k for k in keys])}) VALUES ({placeholders})",
                        vals,
                    )
                con.commit()
            con.close()
        except Exception:
            logging.exception("Failed to write SQLite export")

        return {"csv": str(csv_path), "db": str(db_path)}
