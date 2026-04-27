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
    scan_parser.add_argument("--run-id", required=False)

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
    claim_parser.add_argument("--quotes-file", required=False)
    claim_parser.add_argument("--run-id", required=False)

    # purge
    purge_parser = subparsers.add_parser("purge", help="purge cache")
    purge_parser.add_argument("--all", action="store_true")
    purge_parser.add_argument("--keep-assets", action="store_true")
    purge_parser.add_argument("--force", action="store_true")

    # axis
    axis_parser = subparsers.add_parser("axis", help="per-axis analysis")
    axis_sub = axis_parser.add_subparsers(dest="subcommand", parser_class=_Parser)
    axis_run = axis_sub.add_parser("run")
    axis_run.add_argument("name")
    axis_run.add_argument("--locale", required=True)
    axis_run.add_argument("--scan", required=True)
    axis_run.add_argument("--emit-hitl-block", action="store_true")
    axis_val = axis_sub.add_parser("validate")
    axis_val.add_argument("--text", required=True)
    axis_val.add_argument("--locale", required=True)
    axis_val.add_argument("--skip-if-overlaps", required=False)
    axis_sub.add_parser("list")

    # render persona/report
    render_parser = subparsers.add_parser("render", help="render persona/report")
    render_sub = render_parser.add_subparsers(dest="subcommand", parser_class=_Parser)
    persona_p = render_sub.add_parser("persona")
    persona_p.add_argument("--claims", required=True)
    persona_p.add_argument("--scope", required=True, choices=["repo", "global"])
    persona_p.add_argument("--locale", required=True, choices=["ko", "en", "jp"])
    persona_p.add_argument("--run-id", required=True)
    persona_p.add_argument("--now", required=True)
    persona_p.add_argument("--out", required=True)
    persona_p.add_argument("--narrative", required=False)
    report_p = render_sub.add_parser("report")
    report_p.add_argument("--persona", required=True)
    report_p.add_argument("--locale", required=True, choices=["ko", "en", "jp"])
    report_p.add_argument("--out", required=True)

    personas_p = render_sub.add_parser("personas")
    personas_p.add_argument("--synthesis", required=True)
    personas_p.add_argument("--persona", required=True)
    personas_p.add_argument("--locale", required=True, choices=["ko", "en", "jp"])
    personas_p.add_argument("--out-dir", required=True)

    # persona check
    persona_parser = subparsers.add_parser("persona", help="persona utilities")
    persona_sub = persona_parser.add_subparsers(dest="subcommand", parser_class=_Parser)
    persona_check = persona_sub.add_parser("check")
    persona_check.add_argument("--persona", required=True)

    # doctor
    subparsers.add_parser("doctor", help="environment health check")

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
            base_dir=args.base_dir,
            run_id=args.run_id,
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
            run_id=args.run_id,
            quotes_file=args.quotes_file,
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

    elif args.command == "axis" and args.subcommand == "run":
        from .axis import run, AXES
        from pathlib import Path
        if args.name not in AXES:
            return 2
        return run(args.name, args.locale, Path(args.scan), args.emit_hitl_block)

    elif args.command == "axis" and args.subcommand == "validate":
        from .axis import validate
        return validate(args.text, args.locale, skip_if_overlaps=args.skip_if_overlaps)

    elif args.command == "axis" and args.subcommand == "list":
        from .axis import AXES
        print("\n".join(AXES))
        return 0

    elif args.command == "render" and args.subcommand == "persona":
        from .render import render_persona
        return render_persona(
            claims_path=args.claims,
            scope=args.scope,
            locale=args.locale,
            run_id=args.run_id,
            now=args.now,
            out_path=args.out,
            narrative_path=args.narrative,
        )

    elif args.command == "render" and args.subcommand == "report":
        from .render import render_report
        return render_report(
            persona_path=args.persona,
            locale=args.locale,
            out_path=args.out,
        )

    elif args.command == "render" and args.subcommand == "personas":
        from .persona_prompt import render_personas
        return render_personas(
            synthesis_path=args.synthesis,
            persona_path=args.persona,
            locale=args.locale,
            out_dir=args.out_dir,
        )

    elif args.command == "persona" and args.subcommand == "check":
        from pathlib import Path
        return 0 if Path(args.persona).exists() else 66

    elif args.command == "doctor":
        from .doctor import main as doctor_main
        return doctor_main()

    print(f"error: unrecognized command or missing subcommand: {' '.join(argv or [])}", file=sys.stderr)
    return 1
