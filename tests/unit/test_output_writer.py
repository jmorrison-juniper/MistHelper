from src.output.writer import ConsoleOutputWriter


def test_console_output_writer_methods(capsys):
    w = ConsoleOutputWriter()
    w.info("hello")
    w.warn("watch out")
    w.error("bad")
    captured = capsys.readouterr()
    assert "[INFO] hello" in captured.out
    assert "[WARN] watch out" in captured.out
    assert "[ERROR] bad" in captured.err
