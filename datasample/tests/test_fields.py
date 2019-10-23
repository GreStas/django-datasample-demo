import json
import unittest
from collections import OrderedDict
from datasample.elements import Field, SampleElementError

__all__ = (
    'SmokeFieldTestCase',
    'CheckFieldTestCase',
)


class CheckFieldTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.field = Field('field')

    def test_key_calc_negative(self):
        """ Поле может быть или ключевое или вычисляемое """
        with self.assertRaises(SampleElementError) as context:
            field = Field(
                'test_full_field',
                expression='calc_field',
                ctype="Decimal",
                having=('<=', '<', '>=', '>', '=', '!=', 'between'),
                hidden=False,
                label="Максимально заполненное поле",
                ordered=True,
                alias='full_calc_field',
                mandatory=True,
                key=True,
                calc=('sum', 'min', 'max'),
                table='resources',
                filtered=('>', '>=', 'between', 'in', 'not in', '<', '<=', 'not between', 'is null', 'is not null', '=', '!='),
            )
        self.assertDictEqual(
            context.exception.errors,
            {
                'key':
                    "Only one of 'key' and 'calc' must by set on.",
            },
        )


class SmokeFieldTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.field = Field('field')

    def test_full_field(self):
        """ Максимально заполненное поле

            для проверки, что умолчания не влияют
        """
        field = Field(
            'test_full_field',
            expression='calc_field',
            ctype="Decimal",
            having=('<=', '<', '>=', '>', '=', '!=', 'between'),
            hidden=False,
            label="Максимально заполненное поле",
            ordered=True,
            alias='full_calc_field',
            mandatory=True,
            key=False,
            calc=('sum', 'min', 'max'),
            table='resources',
            filtered=('>', '>=', 'between', 'in', 'not in', '<', '<=', 'not between', 'is null', 'is not null', '=', '!='),
        )
        etalon_state = OrderedDict([
            ('mandatory', True),
            ('ctype', "Decimal"),
            ('label', "Максимально заполненное поле"),
            ('key', False),
            ('calc', ("sum", "min", "max")),
            ('filtered', ('>', '>=', 'between', 'in', 'not in', '<', '<=', 'not between', 'is null', 'is not null', '=', '!=')),
            ('ordered', True),
            ('having', ('<=', '<', '>=', '>', '=', '!=', 'between')),
            ('hidden', False),
            ('table', 'resources'),
            ('expression', 'calc_field'),
            ('alias', 'full_calc_field'),
        ])
        self.assertEqual(field.name, 'test_full_field', "Наименование поля не идентично заданному")
        self.assertDictEqual(field.state, etalon_state, "Описание поля не идентично заданному")

    def test_short_field(self):
        """ Минимально заполненное поле

            для проверки умолчаний
        """
        etalon_state = [
            ('mandatory', False),
            ('ctype', "String"),
            ('label', self.field.name),
            ('key', False),
            ('calc', None),
            ('filtered', None),
            ('ordered', False),
            ('having', None),
            ('hidden', False),
            ('table', 'main'),
            ('expression', self.field.name),
            ('alias', self.field.name),
        ]
        self.assertListEqual([(k, w) for k, w in self.field.state.items()], etalon_state,
                             "Не соответсвуют порядок и/или подстановки значений по-умолчанию")

    @unittest.skip
    def test_getstate(self):
        pass

    @unittest.skip
    def test_setstate(self):
        pass

    @unittest.skip
    def test_json_dumps(self):
        pass

    @unittest.skip
    def test_json_loads(self):
        pass

    @unittest.skip
    def test_json_reload(self):
        pass

    @unittest.skip
    def test_key_field(self):
        """ Простое ключевое поле """
        pass

    @unittest.skip
    def test_calc_field(self):
        """ Простое вычислимое поле """
        pass

    @unittest.skip
    def test_having_field(self):
        """ Вычислимое поле с having """
        pass

    @unittest.skip
    def test_ordered_field(self):
        """ Простое поле с order by """
        pass
