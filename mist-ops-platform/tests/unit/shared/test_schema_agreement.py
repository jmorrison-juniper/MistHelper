"""Prove that the Alembic migration chain and the ORM models build one schema.

Issue #1883 records four disagreements between
`migrations/versions/0001_initial.py` and the models in `src/shared/models/`.
The disagreements break the login route and every configuration route.

This module runs the whole migration chain in the Alembic offline mode. The
offline mode renders the DDL as text and needs no PostgreSQL server. The tests
then read that DDL and compare it against the ORM metadata.
"""

from __future__ import annotations

import importlib.util
import io
import logging
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations

from src.shared.db import PARTITIONED_TABLES
from src.shared.models.base import Base

if TYPE_CHECKING:  # The module type is an annotation only, so keep it out of runtime.
    from types import ModuleType

logger = logging.getLogger(__name__)

# The migration files live beside the package root, so walk up to the project.
VERSIONS_DIR = Path(__file__).resolve().parents[3] / "migrations" / "versions"

# A hash partition child carries a `_pNN` suffix. A LIST partition child carries
# a `_org_<hex>` suffix. Neither child is an ORM table, so the tests skip both.
PARTITION_CHILD_PATTERN = re.compile(r"_p\d+$|_org_[0-9a-f]{32}$")

# A statement ends at a semicolon that closes the line in the Alembic output.
STATEMENT_SPLIT_PATTERN = re.compile(r";\s*\n")

# `CREATE TABLE name (` and `DROP TABLE name` both name the table in group 1.
CREATE_TABLE_PATTERN = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
DROP_TABLE_PATTERN = re.compile(
    r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)


def _load_migration_modules() -> list[ModuleType]:
    """Import every migration file and return the modules in upgrade order."""
    logger.info("Migration module load starts from %s.", VERSIONS_DIR)
    modules: dict[str, ModuleType] = {}  # Map a revision identifier to its module.
    for path in sorted(VERSIONS_DIR.glob("*.py")):  # Sort so the load order is stable.
        name = f"_mist_ops_migration_{path.stem}"  # Use a private name to avoid a clash.
        spec = importlib.util.spec_from_file_location(name, path)  # Build the import spec.
        if spec is None or spec.loader is None:  # A missing loader means the file is unreadable.
            pytest.fail(f"The migration file {path} is not importable.")
        module = importlib.util.module_from_spec(spec)  # Create the empty module object.
        sys.modules[name] = module  # Register the module, because `from __future__` needs it.
        spec.loader.exec_module(module)  # Run the file, which defines `upgrade` and the ids.
        modules[module.revision] = module  # Key the module by the revision it declares.
    ordered = _order_by_revision_chain(modules)  # Follow `down_revision` to get the real order.
    logger.debug("Migration module load done for %d modules.", len(ordered))
    return ordered


def _order_by_revision_chain(modules: dict[str, ModuleType]) -> list[ModuleType]:
    """Walk the `down_revision` chain and return the modules in upgrade order."""
    logger.info("Revision chain walk starts for %d modules.", len(modules))
    children = {m.down_revision: m for m in modules.values()}  # Map a parent to its child.
    ordered: list[ModuleType] = []  # Collect the modules from the root to the head.
    cursor: str | None = None  # The root migration declares `down_revision = None`.
    while cursor in children:  # Stop when no migration names the cursor as its parent.
        module = children[cursor]  # Take the child of the current revision.
        ordered.append(module)  # Append it, because it is the next upgrade step.
        cursor = module.revision  # Move the cursor to the revision that just ran.
    if len(ordered) != len(modules):  # A gap means a broken or a branched chain.
        pytest.fail("The migration chain is broken. Check every `down_revision` value.")
    logger.debug("Revision chain walk done for %d modules.", len(ordered))
    return ordered


def _render_migration_ddl() -> str:
    """Run every migration in the offline mode and return the rendered DDL."""
    logger.info("Offline migration render starts.")
    buffer = io.StringIO()  # The offline mode writes the DDL into this buffer.
    context = MigrationContext.configure(  # Build a context that renders instead of executes.
        dialect_name="postgresql",  # Render for PostgreSQL, because that is the target.
        opts={"as_sql": True, "output_buffer": buffer},  # `as_sql` selects the offline mode.
    )
    with Operations.context(context):  # Install the `alembic.op` proxy for the migrations.
        for module in _load_migration_modules():  # Run the chain from the root to the head.
            module.upgrade()  # Emit the DDL of this one migration into the buffer.
    rendered = buffer.getvalue()  # Read the whole rendered script.
    logger.debug("Offline migration render done with %d characters.", len(rendered))
    return rendered


def _statements(ddl: str) -> list[str]:
    """Split the rendered DDL into single statements."""
    logger.info("Statement split starts for %d characters.", len(ddl))
    parts = [part.strip() for part in STATEMENT_SPLIT_PATTERN.split(ddl)]  # Cut at each end.
    kept = [part for part in parts if part]  # Drop the empty tail that the final cut leaves.
    logger.debug("Statement split done with %d statements.", len(kept))
    return kept


def _surviving_tables(ddl: str) -> dict[str, str]:
    """Return the tables the migration chain leaves behind, keyed to their DDL."""
    logger.info("Surviving table scan starts.")
    tables: dict[str, str] = {}  # Hold the last `CREATE TABLE` text for each table name.
    for statement in _statements(ddl):  # Replay the script in order, so the last write wins.
        dropped = DROP_TABLE_PATTERN.match(statement)  # A drop removes the table again.
        if dropped is not None:  # Handle the drop first, because a drop never creates.
            tables.pop(dropped.group(1), None)  # Forget the table, and ignore an absent name.
            continue  # Move on, because a drop holds no column text.
        created = CREATE_TABLE_PATTERN.match(statement)  # A create adds or replaces the table.
        if created is not None:  # Record only a statement that starts with `CREATE TABLE`.
            tables[created.group(1)] = statement  # Store the text for the column assertions.
    logger.debug("Surviving table scan done with %d tables.", len(tables))
    return tables


def _parent_tables(ddl: str) -> dict[str, str]:
    """Return the surviving tables without the partition children."""
    logger.info("Partition child filter starts.")
    survivors = _surviving_tables(ddl)  # Start from every table the chain leaves behind.
    parents: dict[str, str] = {}  # Hold only the parent tables of the final schema.
    for name, statement in survivors.items():  # Read every table the chain leaves behind.
        if PARTITION_CHILD_PATTERN.search(name) is not None:  # Match a child name suffix.
            continue  # Skip the child, because no ORM model declares a partition child.
        parents[name] = statement  # Keep the parent, because the ORM must declare it.
    logger.debug("Partition child filter done with %d parents.", len(parents))
    return parents


@pytest.fixture(scope="module")
def migration_ddl() -> str:
    """Render the migration chain one time for every test in this module."""
    return _render_migration_ddl()


def test_migration_creates_every_orm_table(migration_ddl: str) -> None:
    """The migration must build every table that the ORM models declare."""
    parents = _parent_tables(migration_ddl)  # Read the tables the chain leaves behind.
    expected = set(Base.metadata.tables)  # The ORM metadata is the schema owner.
    missing = sorted(expected - set(parents))  # A missing table breaks every query on it.
    assert not missing, f"The migration builds no table for the ORM tables {missing}."


def test_migration_leaves_no_table_outside_the_orm(migration_ddl: str) -> None:
    """The migration must not leave a table that no ORM model declares."""
    parents = _parent_tables(migration_ddl)  # Read the tables the chain leaves behind.
    expected = set(Base.metadata.tables)  # The ORM metadata is the schema owner.
    extra = sorted(set(parents) - expected)  # An extra table is dead weight and a trap.
    assert not extra, f"The migration leaves the non-ORM tables {extra}."


def test_config_revisions_primary_key_matches_the_model(migration_ddl: str) -> None:
    """The `config_revisions` key must be `revision_id` plus `org_id`."""
    parents = _parent_tables(migration_ddl)  # Read the tables the chain leaves behind.
    assert "config_revisions" in parents, "The migration builds no `config_revisions` table."
    statement = parents["config_revisions"]  # Take the final definition of that one table.
    assert "revision_id" in statement, "The `config_revisions` table holds no `revision_id`."
    assert (
        "PRIMARY KEY (revision_id, org_id)" in statement
    ), "The `config_revisions` primary key does not match the `ConfigRevision` model."


def test_config_revisions_columns_match_the_model(migration_ddl: str) -> None:
    """Every `ConfigRevision` column must exist in the migrated table."""
    parents = _parent_tables(migration_ddl)  # Read the tables the chain leaves behind.
    statement = parents.get("config_revisions", "")  # Take the final definition, or an empty text.
    model_columns = [c.name for c in Base.metadata.tables["config_revisions"].columns]  # Read ORM.
    missing = [name for name in model_columns if name not in statement]  # Compare name by name.
    assert not missing, f"The migrated `config_revisions` table holds no columns {missing}."


@pytest.mark.parametrize("table_name", PARTITIONED_TABLES)
def test_partitioned_tables_use_list_partitioning(migration_ddl: str, table_name: str) -> None:
    """Each partitioned table must use LIST, because `ensure_org_partitions` sends a LIST bound."""
    parents = _parent_tables(migration_ddl)  # Read the tables the chain leaves behind.
    statement = parents.get(table_name, "")  # Take the final definition of this one table.
    assert statement, f"The migration builds no `{table_name}` table."
    assert (
        "PARTITION BY LIST (org_id)" in statement
    ), f"The `{table_name}` table does not use LIST partitioning by `org_id`."
    assert "PARTITION BY HASH" not in statement, (
        f"The `{table_name}` table still uses HASH partitioning. "
        "A LIST bound fails against a hash-partitioned parent."
    )


def test_model_declares_list_partitioning_for_every_partitioned_table() -> None:
    """The ORM models must declare the same partition strategy as `PARTITIONED_TABLES`."""
    for table_name in PARTITIONED_TABLES:  # Check each table the login path partitions.
        table = Base.metadata.tables[table_name]  # Read the ORM table object by its name.
        strategy = table.dialect_options["postgresql"].get("partition_by")  # Read the option.
        message = f"The `{table_name}` model declares the partition strategy {strategy!r}."
        assert strategy == "LIST (org_id)", message  # A HASH parent rejects a LIST bound.
