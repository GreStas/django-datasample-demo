import unittest
from django.test import TestCase

# from etl.tests import commondata
from datasample import execute
from datasample.tests.fixtures import (
    ETALON_FULL_SCHEMA_METADATA,
    ETALON_FULL_OPTIONS,
    PARAM_YEAR_POSITIVE,  # PARAM_YEAR_NEGATIVE,
    PARAM_DATEFROM_POSITIVE,  # PARAM_DATEFROM_NEGATIVE,
    PARAM_DATETO_POSITIVE,  # PARAM_DATETO_NEGATIVE,
    PARAM_HIERARCHY_POSITIVE,  # PARAM_HIERARCHY_NEGATIVE,
    PARAM_MIN_AMOUNT_POSITIVE,  # PARAM_MIN_AMOUNT_NEGATIVE,
)

__all__ = (
    'SmokeExecuteTestCase',
)


PARAMS_POSITIVE = {
    **PARAM_YEAR_POSITIVE,
    **PARAM_DATEFROM_POSITIVE,
    **PARAM_DATETO_POSITIVE,
    **PARAM_HIERARCHY_POSITIVE,
    **PARAM_MIN_AMOUNT_POSITIVE,
}


@unittest.skip("TODO Создать фикстуры для DMAllocationPlan")
class SmokeExecuteTestCase(TestCase):
    # fixtures = [*commondata.initial, *commondata.allocationplan]

    def setUp(self):
        self.maxDiff = None
        self.db_settings = {
            'NAME': 'postgres',
            'USER': 'postgres',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }

    def test_full(self):
        options = dict(ETALON_FULL_OPTIONS)
        options['filters'] = (('year', '!=', (2017,)),)
        options['order'] = (('year', 'asc'),)
        del options['having']
        data = execute(
            ETALON_FULL_SCHEMA_METADATA,
            PARAMS_POSITIVE,
            options,
            self.db_settings,
        )
        self.assertNotEqual(len(data), 0, "Выборка должна быть не пустая.")
