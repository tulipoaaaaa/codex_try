from cli.execute_from_config import parse_args


def test_parse_args_defaults():
    args = parse_args([])
    assert args.dry_run is False
