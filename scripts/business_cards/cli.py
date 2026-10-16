import argparse
import json
from pathlib import Path

from .contacts import (domain_candidates, export_library, import_batch,
                       import_edits, load_catalog)
from .video import extract_video, prepare_video

BASE = Path.cwd()


def main():
    parser = argparse.ArgumentParser(description='Video business-card batches and cumulative contact workbook')
    parser.add_argument('--library', type=Path, default=BASE / 'card_library')
    parser.add_argument('--xlsx', type=Path, default=BASE / 'business_cards.xlsx')
    parser.add_argument('--companies', type=Path, default=Path(__file__).parent / 'company_domains.json')
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare', help='Sample a new video and propose card borders')
    prepare.add_argument('video', type=Path)
    prepare.add_argument('--interval', type=float, default=1.0)
    extract = commands.add_parser('extract', help='Cut full-resolution cards using reviewed annotations')
    extract.add_argument('job', type=Path)
    extract.add_argument('--interval', type=float, default=.4)
    extract.add_argument('--scene', type=int)
    append = commands.add_parser('append', help='Import a recognized batch and regenerate the cumulative workbook')
    append.add_argument('batch', type=Path)
    append.add_argument('--edited-xlsx', type=Path)
    edits = commands.add_parser('import-edits', help='Preserve manual changes from a downloaded v2 workbook')
    edits.add_argument('xlsx_file', type=Path)
    domains = commands.add_parser('domains', help='Show corporate domains for missing companies')
    domains.add_argument('batch', type=Path)
    commands.add_parser('export', help='Regenerate XLSX with linked four-column photo gallery')
    commands.add_parser('status')
    args = parser.parse_args()
    args.library = args.library.resolve()
    args.xlsx = args.xlsx.resolve()
    if args.command == 'prepare':
        job = prepare_video(args.video, args.library, args.interval)
        result = {'job': str(job), 'next_step': 'Review overview/proposals and save annotations.json for this video'}
    elif args.command == 'extract':
        result = extract_video(args.job, args.interval, only_scene=args.scene)
    elif args.command == 'domains':
        known = json.loads(args.companies.read_text())
        result = []
        for path in sorted((args.batch / 'recognition').glob('card_*.json')):
            card = json.loads(path.read_text())
            if not card.get('company'):
                result.append({'card': card['id'], 'domains': domain_candidates(card),
                               'unresolved': [d for d in domain_candidates(card) if d not in known]})
    elif args.command == 'status':
        catalog = load_catalog(args.library)
        result = {'library': str(args.library), 'cards': len(catalog['cards']),
                  'videos': len(catalog['sources']), 'xlsx': str(args.xlsx)}
    else:
        result = {}
        if args.command == 'import-edits':
            result.update(import_edits(args.library, args.xlsx_file))
        if args.command == 'append':
            if args.edited_xlsx:
                result.update(import_edits(args.library, args.edited_xlsx))
            result.update(import_batch(args.library, args.batch, json.loads(args.companies.read_text())))
        result.update(export_library(args.library, args.xlsx))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
