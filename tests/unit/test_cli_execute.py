from cli.execute_from_config import parse_args


def test_parse_args_defaults():
    """Verify default argument values when required options are provided."""
    args = parse_args(["--config", "dummy.yml"])
    assert args.preview_only is False
