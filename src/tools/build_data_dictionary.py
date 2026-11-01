"""Generate the embedded Power Query dictionary from native TMDL metadata."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import textwrap

MODEL = Path(__file__).resolve().parents[2] / 'power_bi/gps/activity_tracking.SemanticModel/definition'
HELPERS = {'measures_', 'select_measures', 'select_dimensions', 'data_dictionary'}
FIELDS = ['Object Type', 'Table Name', 'Object Name', 'Description', 'Display Folder',
          'Data Type', 'Format String', 'DAX Expression', 'Is Hidden']
OBJECT = re.compile(r"^\t(measure|column) ('(?:[^']|'')*'|[^\s=]+)(?:\s*=([^\n]*))?$", re.M)


def metadata_rows(model: Path = MODEL) -> list[list]:
    """Read the repository's native descriptions and object-level properties.

    This handles the checked-in TMDL convention, not arbitrary TMDL syntax.
    Unsupported expression fences fail explicitly rather than emit broken docs.
    """
    rows = []
    for path in sorted((model / 'tables').glob('*.tmdl')):
        if path.stem == 'data_dictionary':
            continue
        content = path.read_text(encoding='utf-8')
        matches = list(OBJECT.finditer(content))
        for match in matches:
            kind, name, first_expression = match.groups()
            if kind == 'column' and path.stem in HELPERS:
                continue
            if name.startswith("'"):
                name = name[1:-1].replace("''", "'")
            # A native description is the contiguous /// block above the object.
            before = content[:match.start()].splitlines()
            description = []
            for line in reversed(before):
                if not line.startswith('\t///'):
                    break
                description.append(line[4:].lstrip())
            description = '\n'.join(reversed(description))
            if not description:
                raise ValueError(f'Missing native description: {path.stem}.{name}')
            # Read only this object's body, never properties on the next object.
            tail = content[match.end():]
            end = re.search(r'^\t[^\t\n]', tail, re.M)
            body = tail[:end.start()] if end else tail

            def prop(key):
                found = re.search(r'^\t\t' + key + r': (.*)$', body, re.M)
                return found[1] if found else None

            expression = (first_expression or '').strip()
            continuation = []
            for line in body.splitlines():
                if line.startswith('\t\t') and not re.match(r'\t\t(?:\w+:|isHidden\b|annotation\b)', line):
                    continuation.append(line[2:])
                elif line.strip():
                    break
            if continuation:
                expression = '\n'.join(filter(None, [expression, textwrap.dedent('\n'.join(continuation))]))
            if '```' in expression:
                raise ValueError(f'Unsupported fenced expression: {path.stem}.{name}')
            # Measures infer their output type in the engine; do not guess it.
            data_type = prop('dataType') if kind == 'column' else 'Inferred by DAX'
            rows.append([
                'Measure' if kind == 'measure' else 'Column', path.stem, name,
                description, prop('displayFolder'), data_type, prop('formatString'),
                expression or None, bool(re.search(r'^\t\tisHidden\s*$', body, re.M)),
            ])
    return rows


def m_literal(value) -> str:
    """Encode text as an M literal, preserving quotes and control characters."""
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return str(value).lower()
    value = value.replace('#(', '#(#)(').replace('"', '""')
    value = value.replace('\r', '#(cr)').replace('\n', '#(lf)').replace('\t', '#(tab)')
    return '"' + value + '"'


def render(model: Path = MODEL) -> str:
    path = model / 'tables/data_dictionary.tmdl'
    current = path.read_text(encoding='utf-8')
    # Preserve the existing table/column identities and source bindings.
    header = current.split('\n\tpartition data_dictionary = ', 1)[0].rstrip()
    header = re.sub(r'^///.*\n', '/// Embedded dictionary generated from native TMDL definitions; run python -m src.tools.build_data_dictionary after metadata edits.\n', header, count=1)
    header = re.sub(r'sourceColumn: \[([^\]]+)\]', r'sourceColumn: \1', header)
    schema = ', '.join(f'#"{field}" = ' + ('logical' if field == 'Is Hidden' else 'nullable text') for field in FIELDS)
    lines = [header, '', '\tpartition data_dictionary = m', '\t\tmode: import',
             '\t\tsource =', '\t\t\t\t#table (', '\t\t\t\t    type table [' + schema + '],', '\t\t\t\t    {']
    rows = metadata_rows(model)
    for index, row in enumerate(rows):
        lines.append('\t\t\t\t        {' + ', '.join(m_literal(value) for value in row) + '}' + (',' if index < len(rows)-1 else ''))
    lines += ['\t\t\t\t    }', '\t\t\t\t)', '', '\tannotation PBI_ResultType = Table', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if the embedded dictionary needs regeneration')
    args = parser.parse_args()
    path = MODEL / 'tables/data_dictionary.tmdl'
    result = render()
    if args.check:
        if path.read_text(encoding='utf-8') != result:
            raise SystemExit('Dictionary is stale; run python -m src.tools.build_data_dictionary')
        print('Dictionary matches native TMDL metadata.')
    else:
        path.write_text(result, encoding='utf-8')
        print(f'Generated {len(metadata_rows())} dictionary rows.')


if __name__ == '__main__':
    main()
