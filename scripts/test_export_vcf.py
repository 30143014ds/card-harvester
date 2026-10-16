import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from export_vcf import export_vcf, prepare_names

try:
    import vobject
except ImportError:
    vobject = None


class VcfExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.xlsx = self.root / 'cards.xlsx'
        self.names = self.root / 'names.json'
        self.vcf = self.root / 'cards.vcf'
        self.report = self.root / 'report.json'

    def fixture(self, phones, company='Example Company', emails=None, legacy=False):
        book = Workbook()
        sheet = book.active
        sheet.title = 'Визитки' if legacy else 'Contacts'
        sheet.append(['Компания', 'ФИО', 'Телефон', '_id', 'Email'] if legacy else
                     ['Company', 'Full name', 'Phone', '_id', 'Email'])
        names = {}
        for index, value in enumerate(phones):
            key = f'test_{index}'
            sheet.append([company, f'Карточка Тест {index}', value, key,
                          emails[index] if emails else None])
            names[key] = {'source_name': f'Карточка Тест {index}',
                          'first_name': 'Тест', 'last_name': f'Карточка-{index}'}
        review = book.create_sheet('Проверить' if legacy else 'Review')
        review.append(['ID', 'Row', 'Field', 'Visible fragment', 'Reason'])
        review.append(['test_0', 2, 'Телефон', 'неясные цифры', 'тестовая пометка'])
        book.save(self.xlsx)
        book.close()
        self.names.write_text(json.dumps(names, ensure_ascii=False), encoding='utf-8')

    def run_export(self, **kwargs):
        return export_vcf(self.xlsx, self.names, self.vcf, self.report, **kwargs)

    def test_keeps_all_phone_types_and_countries_and_empty_contacts(self):
        self.fixture([
            '+7 495 000-00-00\n8 (916) 000-00-01\n9030000002\n+7 916 000-00-01',
            '+7 495 000-00-00, доб. 12-34\n+49 30 000000\n021 000 00 00',
            None,
            '+1 202 555 0100',
        ])
        before = hashlib.sha256(self.xlsx.read_bytes()).digest()
        summary = self.run_export()
        self.assertEqual((summary['contacts'], summary['with_phone'],
                          summary['without_phone']), (4, 3, 1))
        records = json.loads(self.report.read_text())['records']
        self.assertEqual([p['value'] for p in records[0]['selected_phones']],
                         ['+74950000000', '89160000001', '9030000002', '+79160000001'])
        self.assertEqual([p['value'] for p in records[1]['selected_phones']],
                         ['+74950000000,,1234', '+4930000000', '0210000000'])
        self.assertEqual(records[2]['selected_phones'], [])
        self.assertEqual(records[3]['selected_phones'][0]['value'], '+12025550100')
        self.assertEqual(hashlib.sha256(self.xlsx.read_bytes()).digest(), before)
        self.assertEqual(self.vcf.read_bytes().count(b'BEGIN:VCARD\r\n'), 4)
        self.assertIn(b'+74950000000\\,\\,1234', self.vcf.read_bytes())

    def test_landlines_are_kept_and_invalid_numbers_are_reported(self):
        self.fixture(['+7 495 000-00-00\n+7 916 000-00-01\n+7 916 ???'])
        summary = self.run_export()
        self.assertEqual(summary['telephone_fields'], 2)
        self.assertEqual(summary['skipped_phone_count'], 1)
        report = json.loads(self.report.read_text())
        self.assertEqual(report['skipped_phones'][0]['source'], '+7 916 ???')
        self.assertEqual(report['source_review'][0]['reason'], 'тестовая пометка')

    def test_explicit_country_codes_and_national_prefixes_are_preserved(self):
        self.fixture(['+81 3-0000-0000\n+81 70-0000-0001', '8 916 000-00-01'])
        self.run_export()
        records = json.loads(self.report.read_text())['records']
        self.assertEqual([p['value'] for p in records[0]['selected_phones']],
                         ['+81300000000', '+817000000001'])
        self.assertEqual(records[1]['selected_phones'][0]['value'], '89160000001')

    def test_extensions_deduplicate_by_number_and_extension_without_guessing_country(self):
        self.fixture(['020 7946 0123 ext. 45\n02079460123 x45\n02079460123 #46\n+44 (0)20 7946 0123 extension 45',
                      '9160000001\n1234 ext. 56\n123456'])
        self.run_export()
        records = json.loads(self.report.read_text())['records']
        self.assertEqual([p['value'] for p in records[0]['selected_phones']],
                         ['02079460123,,45', '02079460123,,46', '+442079460123,,45'])
        self.assertEqual([p['value'] for p in records[1]['selected_phones']],
                         ['9160000001', '1234,,56', '123456'])

    def test_legacy_russian_workbooks_remain_readable(self):
        self.fixture(['8 916 000 00 01'], legacy=True)
        summary = self.run_export()
        self.assertEqual(summary['telephone_fields'], 1)
        self.assertIn(b'TEL;TYPE=VOICE:89160000001', self.vcf.read_bytes())

    def test_multiple_emails_and_blank_cells(self):
        self.fixture([None, None], emails=['first@example.test\nsecond@example.test;first@example.test', None])
        summary = self.run_export()
        self.assertEqual(summary['email_fields'], 2)
        records = json.loads(self.report.read_text())['records']
        self.assertEqual(records[0]['emails'], ['first@example.test', 'second@example.test'])
        self.assertEqual(records[1]['emails'], [])

    def test_name_review_rejects_missing_stale_or_unfinished_decisions_before_writing(self):
        self.fixture(['+7 916 000-00-01'])
        self.vcf.write_bytes(b'previous export')
        original = json.loads(self.names.read_text())
        for invalid in ({}, {'test_0': {**original['test_0'], 'source_name': 'different'}},
                        {'test_0': {**original['test_0'], 'first_name': None}}):
            self.names.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                self.run_export()
            self.assertEqual(self.vcf.read_bytes(), b'previous export')
            self.assertFalse(self.report.exists())

    def test_preparation_preserves_existing_decisions_and_paths_cannot_replace_input(self):
        self.fixture([None])
        before = self.names.read_bytes()
        with self.assertRaises(FileExistsError):
            prepare_names(self.xlsx, self.names)
        self.assertEqual(self.names.read_bytes(), before)
        with self.assertRaises(ValueError):
            export_vcf(self.xlsx, self.names, self.xlsx)
        prepared = self.root / 'new_names.json'
        prepare_names(self.xlsx, prepared)
        self.assertIsNone(json.loads(prepared.read_text())['test_0']['first_name'])

    @unittest.skipUnless(vobject, 'Optional independent parser vobject is not installed')
    def test_independent_parser_preserves_unicode_structured_names_company_and_extensions(self):
        company = ('Тест; компания, \\ демонстрация\n' + 'Жёлтый ä тест ' * 20).strip()
        self.fixture(['+7 495 000-00-00, доб. 12-34'], company,
                     emails=['first@example.test\nsecond@example.test'])
        self.run_export()
        data = self.vcf.read_bytes()
        self.assertTrue(all(len(line) <= 75 for line in data.split(b'\r\n')))
        card, = vobject.readComponents(data.decode('utf-8'))
        self.assertTrue(card.validate())
        self.assertEqual(card.n.value.given, 'Тест')
        self.assertEqual(card.n.value.family, 'Карточка-0')
        self.assertFalse(card.n.value.additional)
        self.assertEqual(card.org.value, [company])
        self.assertEqual(card.tel.value, '+74950000000,,1234')
        self.assertEqual([email.value for email in card.email_list],
                         ['first@example.test', 'second@example.test'])
        self.assertEqual(set(card.contents), {'version', 'fn', 'n', 'org', 'tel', 'email'})


if __name__ == '__main__':
    unittest.main()
