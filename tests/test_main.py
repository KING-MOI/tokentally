import subprocess
import sys

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


def test_closed_stdout_pipe_does_not_print_a_traceback() -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "tokentally", "pricing"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None
    proc.stdout.read(10)
    proc.stdout.close()
    _, err = proc.communicate()
    assert b"Traceback" not in err
