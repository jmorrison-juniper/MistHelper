from src.marvis.client import MarvisClient


def test_marvis_client_call_exists():
    mc = MarvisClient()
    assert callable(mc.call)
    res = mc.call("GET", "/test")
    assert isinstance(res, dict)
    assert "status_code" in res
