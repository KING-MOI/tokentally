from tokentally.cache import decode, encode

from conftest import make_record


def test_records_round_trip() -> None:
    rec = make_record(
        input_tokens=1,
        output_tokens=2,
        cache_creation_tokens=3,
        cache_read_tokens=4,
        cache_creation_1h_tokens=2,
    )
    assert decode(encode(rec)) == rec
