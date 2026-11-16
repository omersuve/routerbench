import argparse
import json
import sys
from pathlib import Path
from .adapters import Rules, Replay, Local
from .runner import predict
from .scoring import score
from .io import write_new

def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m routerbench', description='Observe-only routing benchmark; paid inference has no transport.')
    sub = parser.add_subparsers(dest='command', required=True)
    run = sub.add_parser('predict', help='Tasks-only inference; this command cannot accept labels.')
    run.add_argument('--inputs', required=True)
    run.add_argument('--output', required=True, help='New directory; never overwrites a run.')
    run.add_argument('--adapter', choices=('rules', 'local', 'replay', 'jev'), default='rules')
    run.add_argument('--responses', help='Explicit hash-bound JSONL recording; required for replay/Jev.')
    run.add_argument('--model', help='Installed Ollama model; never inferred from global config.')
    run.add_argument('--allow-local', action='store_true')
    run.add_argument('--threshold', type=float, help='Optional conservative minimum certainty; missing confidence abstains.')
    evaluate = sub.add_parser('score', help='Offline label scoring after prediction is sealed.')
    evaluate.add_argument('--run', required=True)
    evaluate.add_argument('--labels', required=True)
    evaluate.add_argument('--output', required=True)
    work = sub.add_parser('execute', help='Bounded data-file repair, no generated code execution.')
    work.add_argument('--model', required=True)
    work.add_argument('--allow-local', action='store_true')
    work.add_argument('--output', required=True)
    audit = sub.add_parser('audit', help='Audit the explicit public release allowlist.')
    audit.add_argument('--root', default='.')
    export = sub.add_parser('export', help='Build audited deterministic zip; no publishing.')
    export.add_argument('--root', default='.')
    export.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'predict':
            if args.adapter == 'rules':
                adapter = Rules()
            elif args.adapter == 'local':
                adapter = Local(args.model, args.allow_local)
            else:
                if not args.responses:
                    raise ValueError('Jev/replay requires an explicit response file; live paid calls are disabled')
                adapter = Replay(args.responses, args.adapter)
            result = predict(args.inputs, args.output, adapter, args.threshold)
        elif args.command == 'score':
            result = score(args.run, args.labels)
            write_new(args.output, result)
        elif args.command == 'execute':
            from .execution import execute
            if Path(args.output).exists() or not Path(args.output).parent.is_dir():
                raise ValueError('new output with existing parent required')
            result = execute(Local(args.model, args.allow_local))
            write_new(args.output, result)
        else:
            from .release import audit_release, export_release
            result = audit_release(Path(args.root)) if args.command == 'audit' else export_release(Path(args.root), Path(args.output))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        # Errors expose controlled diagnostics only, not HTTP bodies or credentials.
        print('Benchmark refused: ' + type(error).__name__ + '. Check inputs, flags and output paths.', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
