import os
import subprocess
import sys
from pathlib import Path

from tokentally import __version__


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tokentally", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_module_entry_point_runs() -> None:
    result = run("--version")
    assert result.returncode == 0
    assert result.stdout.strip() == f"tokentally {__version__}"


def test_usage_errors_exit_with_code_2() -> None:
    result = run("daily", "--sort", "vibes")
    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_closed_stdout_pipe_does_not_print_a_traceback(tmp_path: Path) -> None:
    project = tmp_path / ".claude" / "projects" / "p"
    project.mkdir(parents=True)
    line = (
        '{{"type":"assistant","timestamp":"2026-03-01T00:00:00Z","sessionId":"s",'
        '"message":{{"id":"m{0}","model":"claude-sonnet-4-5","usage":{{"output_tokens":1}}}}}}\n'
    )
    (project / "s.jsonl").write_text("".join(line.format(i) for i in range(5000)), "utf-8")
    env = {
        **os.environ,
        "HOME": str(tmp_path),
        "USERPROFILE": str(tmp_path),
        "TOKENTALLY_CONFIG": str(tmp_path / "none.toml"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
    }
    env.pop("CLAUDE_CONFIG_DIR", None)
    proc = subprocess.Popen(
        [sys.executable, "-m", "tokentally", "records", "--no-cache"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert proc.stdout is not None
    proc.stdout.read(10)
    proc.stdout.close()
    _, err = proc.communicate()
    assert b"Traceback" not in err
