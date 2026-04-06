from src.ui.pager import InteractivePager


def test_truncation_rules():
    pager = InteractivePager(None, 'site-1')
    long_str = 'x' * 200
    row = {'device_id': 'd1', 'hostname': long_str}
    formatted = pager._format_page([row])
    assert len(formatted[0]['hostname']) < 200
