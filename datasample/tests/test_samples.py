# import json
import pickle
from copy import deepcopy
import unittest
from collections import OrderedDict

from datasample.elements import Sample, SampleElementError
from .fixtures import ETALON_FULL_SCHEMA_METADATA

__all__ = (
    'SmokeSampleTestCase',
    'CheckFieldsOfSampleTestCase',
)


class CheckFieldsOfSampleTestCase(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.sample = Sample()
        self.sample_metadata = deepcopy(ETALON_FULL_SCHEMA_METADATA)

    def test_key_calc_negative(self):
        """ Поле может быть или ключевое или вычисляемое """
        self.sample_metadata['fields']['year']['calc'] = ('sum',)
        with self.assertRaises(SampleElementError) as context:
            self.sample.state = self.sample_metadata
        self.assertDictEqual(
            context.exception.errors,
            {
                'fields[year]':
                    ["'key': Only one of 'key' and 'calc' must by set on."],
            },
        )


class SmokeSampleTestCase(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.sample = Sample()

    def test_simple_sample(self):
        """ Схема минимальной сложности """
        etalon_metadata = OrderedDict([
            ('tables', {
                'main': """select  document_id, amount_total from datamart_dmallocationplan where year = :YEAR""",
                'resources': """select  document_id, amount_total from datamart_dmallocationplan where year = :YEAR""",
            }),
            ('fields', {
                'document_id': OrderedDict([
                    ('mandatory', False),
                    ('ctype', 'Integer'),
                    ('label', 'ID документа'),
                    ('key', True),
                    ('calc', None),
                    ('filtered', ('=', 'in')),
                    ('ordered', True),
                    ('having', None),
                    ('hidden', True),
                    ('table', 'main'),
                    ('expression', 'document_id'),
                    ('alias', 'document'),
                ]),
                'amount': OrderedDict([
                    ('mandatory', False),
                    ('ctype', 'Decimal'),
                    ('label', 'Полная сумма документа'),
                    ('key', False),
                    ('calc', ('sum', 'min', 'max')),
                    ('filtered', ('=', '!=', '<', '<=', '>', '>=')),
                    ('ordered', True),
                    ('having', ('=', '!=', '<', '<=', '>', '>=')),
                    ('hidden', False),
                    ('table', 'resources'),
                    ('expression', 'amount_total'),
                    ('alias', 'amount'),
                ]),
            }),
            ('params', {
                'YEAR': OrderedDict([
                    ('ctype', 'Integer'),
                    ('label', 'Отчётный год'),
                ]),
            }),
        ])
        metadata = dict(etalon_metadata)
        sample = Sample(metadata)
        self.assertDictEqual(sample.__getstate__(), etalon_metadata)
        # print(pickle.dumps(sample))

    def test_full_sample(self):
        """ Схема с максимальными кросс-проверками """
        try:
            sample = Sample(ETALON_FULL_SCHEMA_METADATA)
            self.assertDictEqual(sample.__getstate__(), ETALON_FULL_SCHEMA_METADATA)
        except SampleElementError as e:
            print(e)
