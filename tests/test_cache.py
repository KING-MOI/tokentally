from pathlib import Path

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


def test_cache_hit_until_the_file_changes(tmp_path: Path) -> None:
    from tokentally.cache import FileCache

    log = tmp_path / "a.jsonl"
    log.write_text("x\n", encoding="utf-8")
    store = tmp_path / "cache" / "records.json"
    cache = FileCache(store)
    assert cache.get(log) is None
    cache.put(log, [make_record()])
    cache.save()
    reloaded = FileCache(store)
    assert reloaded.get(log) == [make_record()]
    with log.open("a", encoding="utf-8") as fh:
        fh.write("more\n")
    assert reloaded.get(log) is None


def test_corrupt_or_old_cache_is_ignored(tmp_path: Path) -> None:
    from tokentally.cache import FileCache

    store = tmp_path / "records.json"
    store.write_text("{nope", encoding="utf-8")
    assert FileCache(store).entries == {}
    store.write_text('{"version": 0, "files": {"x": {}}}', encoding="utf-8")
    assert FileCache(store).entries == {}
