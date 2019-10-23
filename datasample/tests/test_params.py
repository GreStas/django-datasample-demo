import unittest
from collections import OrderedDict
from datasample import check_params
from datasample.elements import Sample, SampleElementError

__all__ = (
    'SmokeParamsTestCase',
)

ETALON_SCHEMA_METADATA = OrderedDict([
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
        'ONDATE': OrderedDict([
            ('ctype', 'String'),
            ('label', 'На дату'),
        ]),
        'HIERARCHY': OrderedDict([
            ('ctype', 'Boolean'),
            ('label', 'С иерархией'),
        ]),
        'MIN_AMOUNT': OrderedDict([
            ('ctype', 'Decimal'),
            ('label', 'Минимальная полная сумма документа'),
        ]),
    }),
])

PARAM_YEAR_NEGATIVE = {'YEAR': '2018'}
PARAM_YEAR_POSITIVE = {'YEAR': 2018}

PARAM_ONDATE_POSITIVE = {'ONDATE': '20200101'}
PARAM_ONDATE_NEGATIVE = {'ONDATE': 20200101}

PARAM_HIERARCHY_POSITIVE = {'HIERARCHY': True}
PARAM_HIERARCHY_NEGATIVE = {'HIERARCHY': 'True'}

PARAM_MIN_AMOUNT_POSITIVE = {'MIN_AMOUNT': 100.50}
PARAM_MIN_AMOUNT_NEGATIVE = {'MIN_AMOUNT': '100.50'}


class SmokeParamsTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.etalon_sample = Sample(ETALON_SCHEMA_METADATA)

    def test_all_positive(self):
        self.assertTrue(check_params(
            {
                **PARAM_ONDATE_POSITIVE, 
                **PARAM_YEAR_POSITIVE,
                **PARAM_HIERARCHY_POSITIVE,
                **PARAM_MIN_AMOUNT_POSITIVE,
            }, 
            self.etalon_sample,
        ))
        
    def test_all_negative(self):
        with self.assertRaises(SampleElementError) as context:
            check_params(
                {
                    **PARAM_ONDATE_NEGATIVE,
                    **PARAM_YEAR_NEGATIVE,
                    **PARAM_HIERARCHY_NEGATIVE,
                    **PARAM_MIN_AMOUNT_NEGATIVE,
                },
                self.etalon_sample,
            )
        self.assertDictEqual(
            context.exception.errors,
            {
                'params[YEAR]':
                    "Incorect type: given <class 'str'> but waiting one of (<class 'int'>,)",
                'params[HIERARCHY]':
                    "Incorect type: given <class 'str'> but waiting one of (<class 'bool'>,)",
                'params[MIN_AMOUNT]':
                    "Incorect type: given <class 'str'> but waiting one of (<class 'float'>, <class 'decimal.Decimal'>)",
                'params[ONDATE]':
                    "Incorect type: given <class 'int'> but waiting one of (<class 'str'>,)",
            },
        )

    # @unittest.skip
    # def test_string_positive(self):
    #     pass
    #
    # @unittest.skip
    # def test_string_negative(self):
    #     pass
    #
    # @unittest.skip
    # def test_integer_param(self):
    #     pass
    #
    # @unittest.skip
    # def test_decimal_param(self):
    #     pass
    #
    # @unittest.skip
    # def test_boolean_param(self):
    #     pass
