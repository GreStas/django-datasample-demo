import unittest

from datasample import Sample, SampleElementError, check_options
from .fixtures import ETALON_FULL_SCHEMA_METADATA, ETALON_FULL_OPTIONS

__all__ = (
    'SmokeOptionsTestCase',
)


class SmokeOptionsTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.etalon_full_sample = Sample(ETALON_FULL_SCHEMA_METADATA)

    def test_all_positive(self):
        self.assertTrue(check_options(ETALON_FULL_OPTIONS, self.etalon_full_sample,))

    @unittest.skip
    def test_all_negative(self):
        with self.assertRaises(SampleElementError) as context:
            check_options(
                {
                    'fields': tuple([field
                                     for field, state in ETALON_FULL_SCHEMA_METADATA['fields'].items()
                                     if state['hidden']]),
                },
                self.etalon_full_sample,
            )
        self.assertDictEqual(
            context.exception.errors,
            {
                'options[YEAR]':
                    "Incorect type: given <class 'str'> but waiting one of (<class 'int'>,)",
            },
        )
