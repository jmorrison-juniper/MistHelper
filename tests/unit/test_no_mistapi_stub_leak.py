"""Guard against a test module that leaves a mistapi stub in sys.modules.

Some test modules put a MagicMock at ``sys.modules["mistapi"]``. This lets them import
their subject without the real SDK.

pytest imports every test module during collection. But pytest runs ``teardown_module``
only for a module with a selected test. A stub from import time therefore stays for the
whole session when pytest deselects the owner module, such as under ``-k``.

The leak is silent. The real ``mistapi`` package finds its subpackages through
``__getattr__``. That lookup reads ``sys.modules["mistapi"]`` to get the parent package.
A stub has no ``__path__``, so the import fails. The error then names ``mistapi`` as
"not a package" in an unrelated test. See issue #1739.

Each stub module must restore sys.modules directly after its import.
"""

from __future__ import annotations

import sys


def test_mistapi_in_sys_modules_is_the_real_package() -> None:
    """Fail if collection left a stub in place of the real mistapi package."""
    module = sys.modules.get("mistapi")  # Whatever collection left behind.
    assert module is not None, "mistapi is absent from sys.modules. A test module removed it."

    # A MagicMock stub has no __path__, so lazy subpackage imports fail.
    assert hasattr(module, "__path__"), (
        "sys.modules['mistapi'] holds a stub, not the real package. A test module "
        "installed a mock at import time and did not restore it. Restore sys.modules "
        "directly after the guarded import. teardown_module does not run for a "
        "deselected module. See issue #1739."
    )
