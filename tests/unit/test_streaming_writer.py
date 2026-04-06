import io
from src.export.streaming_exporter import StreamingCSVWriter


def test_streaming_writer_writes():
    stream = io.StringIO()
    cols = ['a', 'b']
    writer = StreamingCSVWriter(stream, cols, buffer_size=10)
    writer.write_header()
    writer.write_row({'a': 1, 'b': 2})
    writer._flush_buffer()
    out = stream.getvalue()
    assert 'a' in out and 'b' in out
