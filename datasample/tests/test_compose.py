import unittest

from datasample import compose
from .fixtures import (
    ETALON_FULL_SCHEMA_METADATA,
    ETALON_FULL_OPTIONS,
    PARAM_YEAR_POSITIVE, PARAM_YEAR_NEGATIVE,
    PARAM_DATEFROM_POSITIVE, PARAM_DATEFROM_NEGATIVE,
    PARAM_DATETO_POSITIVE, PARAM_DATETO_NEGATIVE,
    PARAM_HIERARCHY_POSITIVE, PARAM_HIERARCHY_NEGATIVE,
    PARAM_MIN_AMOUNT_POSITIVE, PARAM_MIN_AMOUNT_NEGATIVE,
)

__all__ = (
    'SmokeComposeTestCase',
)

PARAMS_POSITIVE = {
    **PARAM_YEAR_POSITIVE,
    **PARAM_DATEFROM_POSITIVE,
    **PARAM_DATETO_POSITIVE,
    **PARAM_HIERARCHY_POSITIVE,
    **PARAM_MIN_AMOUNT_POSITIVE,
}


class SmokeComposeTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_full(self):
        query, kwargs = compose(ETALON_FULL_SCHEMA_METADATA,
                                PARAMS_POSITIVE,
                                ETALON_FULL_OPTIONS,)
        self.assertIsNotNone(query)
        self.assertIsNotNone(kwargs)
