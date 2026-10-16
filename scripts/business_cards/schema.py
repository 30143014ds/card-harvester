"""English workbook labels and readers for previously delivered Russian workbooks."""

HEADERS = ['Company', 'Full name', 'Position', 'Email', 'Phone', 'Card photo', 'Original link', '_id']
LEGACY_HEADERS = ['Компания', 'ФИО', 'Должность', 'Email', 'Телефон', 'Фотография визитки', '_id']
RUSSIAN_HEADERS = LEGACY_HEADERS[:-1] + ['Ссылка на оригинал', '_id']
SUPPORTED_HEADERS = (HEADERS, HEADERS[:6] + ['_id'], LEGACY_HEADERS, RUSSIAN_HEADERS)
SHEET_NAMES = {'contacts': ('Contacts', 'Визитки'), 'originals': ('Originals', 'Оригиналы'),
               'review': ('Review', 'Проверить'), 'sources': ('Sources', 'Источники')}
COLUMN_NAMES = {'company': ('Company', 'Компания'), 'full_name': ('Full name', 'ФИО'),
                'position': ('Position', 'Должность'), 'emails': ('Email',), 'phones': ('Phone', 'Телефон')}
FIELD_ALIASES = {label: field for field, labels in COLUMN_NAMES.items() for label in labels}


def get_sheet(book, kind, required=True):
    matches = [name for name in SHEET_NAMES[kind] if name in book.sheetnames]
    if len(matches) > 1:
        raise ValueError(f'Ambiguous {kind} sheets: {matches}')
    if matches:
        return book[matches[0]]
    if required:
        raise ValueError(f'Missing {kind} worksheet')
    return None


def column_index(headers, field, required=True):
    matches = [i for i, label in enumerate(headers) if label in COLUMN_NAMES[field]]
    if len(matches) > 1 or (required and not matches):
        raise ValueError(f'Expected one {field} column')
    return matches[0] if matches else None
