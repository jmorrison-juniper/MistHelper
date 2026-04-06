from src.marvis.interactive import launch_interactive


def test_launch_interactive_returns_result():
    res = launch_interactive(None, None)
    assert isinstance(res, dict)
    assert "csv_paths" in res
