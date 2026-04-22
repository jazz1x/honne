import argparse
import sys
from typing import Optional, List
from . import __version__


class _Parser(argparse.ArgumentParser):
    """ArgumentParser that exits with code 1 (not 2) on bad args."""
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"error: {message}\n")


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point. Python<3.9 guard: exit 4 if unsupported."""
    if sys.version_info < (3, 9):
        sys.stderr.write("python3>=3.9 required\n")
        return 4

    parser = _Parser(
        prog="honne_py",
        description="honne — session transcript analysis"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="subcommands", parser_class=_Parser)

    # scan
    scan_parser = subparsers.add_parser("scan", help="scan transcripts")
    scan_parser.add_argument("--scope", choices=["global", "repo"], default="repo")
    scan_parser.add_argument("--since", default="2020-01-01")
    scan_parser.add_argument("--cache", required=False, default=".honne/cache/scan.json")
    scan_parser.add_argument("--index-ref", required=False)
    scan_parser.add_argument("--redact", action="store_true", default=True)
    scan_parser.add_argument("--base-dir", required=False)

    # extract lexicon
    extract_parser = subparsers.add_parser("extract", help="extract patterns")
    extract_subparsers = extract_parser.add_subparsers(dest="axis")
    lexicon_parser = extract_subparsers.add_parser("lexicon")
    lexicon_parser.add_argument("--input", required=True)
    lexicon_parser.add_argument("--out", required=True)
    lexicon_parser.add_argument("--top", type=int, default=50)
    lexicon_parser.add_argument("--min-sessions", type=int, default=3)

    # detect-recurrence
    detect_parser = subparsers.add_parser("detect-recurrence", help="detect recurrence")
    detect_parser.add_argument("--input", required=True)
    detect_parser.add_argument("--out", required=True)
    detect_parser.add_argument("--min-sessions", type=int, default=3)

    # evidence gather
    evidence_parser = subparsers.add_parser("evidence", help="gather evidence")
    evidence_subparsers = evidence_parser.add_subparsers(dest="subcommand")
    gather_parser = evidence_subparsers.add_parser("gather")
    gather_parser.add_argument("--input", required=True)
    gather_parser.add_argument("--claim", required=True)
    gather_parser.add_argument("--out", required=True)
    gather_parser.add_argument("--max", type=int, default=10)

    # index session
    index_parser = subparsers.add_parser("index", help="index session")
    index_subparsers = index_parser.add_subparsers(dest="subcommand")
    session_parser = index_subparsers.add_parser("session")
    session_parser.add_argument("--jsonl", required=True)
    session_parser.add_argument("--out", required=True)

    # query assets
    query_parser = subparsers.add_parser("query", help="query assets")
    query_parser.add_argument("--base-dir", required=False)
    query_parser.add_argument("--scope", choices=["global", "repo"], required=False)
    query_parser.add_argument("--since", required=False)
    query_parser.add_argument("--until", required=False)
    query_parser.add_argument("--tag", required=False)
    query_parser.add_argument("--tags", required=False)
    query_parser.add_argument("--type", required=False)
    query_parser.add_argument("--types", required=False)
    query_parser.add_argument("--out", required=False)

    # record claim
    record_parser = subparsers.add_parser("record", help="record claim")
    record_subparsers = record_parser.add_subparsers(dest="subcommand")
    claim_parser = record_subparsers.add_parser("claim")
    claim_parser.add_argument("--type", required=True)
    claim_parser.add_argument("--axis", required=True)
    claim_parser.add_argument("--scope", required=True)
    claim_parser.add_argument("--claim", required=True)
    claim_parser.add_argument("--out", required=True)
    claim_parser.add_argument("--support-count", type=int, required=False)
    claim_parser.add_argument("--prior-id", required=False)
    claim_parser.add_argument("--quotes-json", required=False)

    # purge
    purge_parser = subparsers.add_parser("purge", help="purge cache")
    purge_parser.add_argument("--all", action="store_true")
    purge_parser.add_argument("--keep-assets", action="store_true")
    purge_parser.add_argument("--force", action="store_true")

    # precommit
    precommit_parser = subparsers.add_parser("precommit", help="pre-commit hook")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    # Dispatch to subcommand handlers
    if args.command == "scan":
        from .scan import run_scan
        return run_scan(
            scope=args.scope,
            since=args.since,
            cache=args.cache,
            index_ref=args.index_ref,
            redact_secrets=args.redact,
        )

    elif args.command == "extract" and args.axis == "lexicon":
        from .extract import extract_lexicon
        return extract_lexicon(
            input_path=args.input,
            out_path=args.out,
            top=args.top,
            min_sessions=args.min_sessions,
        )

    elif args.command == "detect-recurrence":
        from .detect_recurrence import detect
        return detect(
            input_path=args.input,
            out_path=args.out,
            min_sessions=args.min_sessions,
        )

    elif args.command == "evidence" and args.subcommand == "gather":
        from .evidence import gather
        return gather(
            input_path=args.input,
            claim=args.claim,
            out_path=args.out,
            max_=args.max,
        )

    elif args.command == "index" and args.subcommand == "session":
        from .index import index_session
        return index_session(
            jsonl_path=args.jsonl,
            out_path=args.out,
        )

    elif args.command == "query":
        from .query import query
        return query(
            base_dir=args.base_dir,
            scope=args.scope,
            since=args.since,
            until=args.until,
            tag=args.tag,
            tags=args.tags,
            type_=args.type,
            types=args.types,
            out_path=args.out,
        )

    elif args.command == "record" and args.subcommand == "claim":
        from .record import record_claim
        return record_claim(
            type_=args.type,
            axis=args.axis,
            scope=args.scope,
            claim=args.claim,
            out_path=args.out,
            support_count=args.support_count,
            prior_id=args.prior_id,
            quotes_json=args.quotes_json,
        )

    elif args.command == "purge":
        from .purge import purge
        return purge(
            all_=args.all,
            keep_assets=args.keep_assets,
            force=args.force,
        )

    elif args.command == "precommit":
        from .precommit import precommit
        return precommit()

    return 0
