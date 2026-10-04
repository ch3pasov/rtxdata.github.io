"""Offline importer regression using invented transactions and stdlib only.

Extract importer functions so the notebook module's import-time private file
reads and optional visualization packages are never executed.
"""
import ast
import io
import json
import sqlite3
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace


SOURCE = Path(__file__).resolve().parents[1] / 'utils.py'


def import_synthetic(debit, credit):
    tree = ast.parse(SOURCE.read_text())
    names = {'format_date_string', 'parse_ref', 'init_database'}
    functions = ast.Module(body=[node for node in tree.body
                                if isinstance(node, ast.FunctionDef)
                                and node.name in names], type_ignores=[])
    tx = [''] * 15
    tx[2], tx[3], tx[5] = 'RSD', '01.02.2023 12:34:56', 'synthetic-card'
    tx[6], tx[7], tx[8], tx[9] = 'Invented reference', 'synthetic-id', debit, credit
    tx[11], tx[13], tx[14] = 'synthetic-ref2', 'synthetic-type', tx[6]
    payload = json.dumps({'transactions': {'synthetic-account': [[None, [tx]]]}})
    db = sqlite3.connect(':memory:')

    def open_synthetic(filename, mode):
        assert filename == 'Raiff_synthetic.json' and mode == 'r'
        return io.StringIO(payload)

    namespace = {'datetime': datetime, 'json': json, 'db': db,
                 'os': SimpleNamespace(listdir=lambda directory: ['Raiff_synthetic.json']),
                 'open': open_synthetic, 'patterns': {}, 'rates_rsd': {'RSD': 1}}
    exec(compile(functions, str(SOURCE), 'exec'), namespace)
    try:
        namespace['init_database']('')
        return db.execute('SELECT sum, rsum FROM TX').fetchone()
    finally:
        db.close()


class TransactionAmountsTest(unittest.TestCase):
    def test_credit_with_literal_zero_debit(self):
        self.assertEqual(import_synthetic('0', '125.50'), (125.50, 125.50))

    def test_credit_with_decimal_zero_debit(self):
        self.assertEqual(import_synthetic('0.00', '125.50'), (125.50, 125.50))

    def test_credit_with_integer_zero_debit(self):
        self.assertEqual(import_synthetic(0, 125.50), (125.50, 125.50))

    def test_credit_with_float_zero_debit(self):
        self.assertEqual(import_synthetic(0.0, 125.50), (125.50, 125.50))

    def test_nonzero_debit_keeps_negative_sign(self):
        self.assertEqual(import_synthetic('12.34', '0'), (-12.34, -12.34))

    def test_numeric_nonzero_debit_keeps_precedence(self):
        self.assertEqual(import_synthetic(12.34, 99), (-12.34, -12.34))

    def test_negative_credit_is_preserved(self):
        self.assertEqual(import_synthetic('0.00', '-25.50'), (-25.50, -25.50))


if __name__ == '__main__':
    unittest.main()
