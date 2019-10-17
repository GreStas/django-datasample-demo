from typing import Sequence, Set, FrozenSet, Union
from decimal import Decimal
from collections import OrderedDict, namedtuple
from sqlalchemy.sql import text

from .utils import add_message

__all__ = (
    'CTYPES',
    'Field', 'Param', 'Sample',
    'check_op_args',
    'SampleElementError',
)


CTYPES = {
    "Boolean": (bool,),
    "String": (str,),
    "Integer": (int,),
    "Decimal": (float, Decimal),
}
OPERATIONS = {
    "Boolean": ('is null', 'is not null',),
    "String": ('is null', 'is not null', '=', '!=', 'in', 'not in', 'like', 'not like',),
    "Integer": ('is null', 'is not null', '=', '!=', 'in', 'not in', '<', '<=', '>', '>=', 'between', 'not between',),
    "Decimal": ('is null', 'is not null', '=', '!=', 'in', 'not in', '<', '<=', '>', '>=', 'between', 'not between',),
    "Date": ('is null', 'is not null', '=', '!=', 'in', 'not in', '<', '<=', '>', '>=', 'between', 'not between',),
}
OPERATIONS_ARGS = {
    'is null': tuple(),
    'is not null': tuple(),
    '=': ('<ctype>',),
    '!=': ('<ctype>',),
    'in': ('<collection>',),
    'not in': ('<collection>',),
    '<': ('<ctype>',),
    '<=': ('<ctype>',),
    '>': ('<ctype>',),
    '>=': ('<ctype>',),
    'between': ('<ctype>', '<ctype>'),
    'not between': ('<ctype>', '<ctype>'),
}
AGGREGATES = ('sum', 'avg', 'min', 'max',)

ERR_MSG_NOTCTYPE = f"'ctype' must be in {OPERATIONS.keys()}"
ERR_MSG_NOTIDENTIFIER = 'Value must be Python and SQL identifier compatible.'
ERR_MSG_NOTOPERATION = f"All values must be in ({OPERATIONS})."
ERR_MSG_NOTAGGREGATED = f"All values must be in ({AGGREGATES})."
ERR_MSG_KEY_CALC = "Only one of 'key' and 'calc' must by set on."

FieldType = namedtuple('FieldType', ('datatype', 'default', 'validator', 'errmsg',))


def check_val_ctype(val, ctype: str):
    return isinstance(val, tuple(CTYPES[ctype]))


def check_op_args(op: str, args: tuple, field_state: dict = None):
    """
        Проверка операции и её операндов на соответсвие описанию поля

    :param op: операция
    :param args: параметры операнды
    :param field_state: описание поля
    :return: None
    """
    # Операция в списке допустимых для поля
    try:
        arg_descriptor = OPERATIONS_ARGS[op]
    except KeyError:
        raise ValueError(f"Недопустимая операция {repr(op)}")
    # Отсутсвие операндов
    if not arg_descriptor and args:
        raise ValueError(f"Операция {repr(op)} не предусматривает наличия аргументов.")
    if len(arg_descriptor) == 1 and arg_descriptor[0] == '<collection>':
        if not isinstance(args, (list, tuple, set)):
            raise ValueError(f"Операция {repr(op)} предусматривает коллекцию аргументов.")
    # Количество аргументов
    elif len(arg_descriptor) != len(args):
        raise ValueError(
            f"Операция {repr(op)} предусматривает {len(arg_descriptor)} аргументов, а передано {len(args)}."
        )
    # TODO проверить <ctype> | <collection>


class SampleElementError(Exception):
    def __init__(self, errors: dict, **kwargs):
        super().__init__(**kwargs)
        self.errors = errors

    def __str__(self):
        return '\n'.join([
            "{key}: {msgs}".format(key=key, msgs=';\t\n'.join(msgs))
            for key, msgs in self.errors.items()
        ])


def check_mandatory_hidden(val: str, state: dict = None):
    return not (bool(val) and bool(state['hidden']))


def check_hidden_mandatory(val: str, state: dict = None):
    return not (bool(val) and bool(state['mandatory']))


def check_ctype(val: str, state: dict = None):
    return val in OPERATIONS.keys()


def check_operation(val, state: dict):
    return val is None or val in OPERATIONS[state['ctype']]


def check_identifier(val, state: dict = None):
    return val is None or val.isidentifier()


def check_operations(val, state: dict):
    return val is None or all([check_operation(v, state) for v in val])


def check_having(val, state: dict):
    return val is None \
           or \
           bool(state['calc']) and check_operations(val, state)


def check_aggregates(val, state: dict = None):
    return val is None or all([v in AGGREGATES for v in val])


def check_calc(val, state: dict):
    return val is None \
           or \
           not bool(state['key']) and check_aggregates(val, state)


def check_key(val, state):
    return not val or val ^ bool(state['calc'])


class SampleElement:
    _TEMPLATE = OrderedDict([('label', FieldType(str, "{{name}}", None, None))])

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.state = kwargs

    @property
    def template(self) -> dict:
        return self._TEMPLATE

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if isinstance(value, str) and value.isidentifier():
            self._name = value
        else:
            raise TypeError("'name' must be string and Python identifier compatible.")

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: dict):
        new_state = self.defaults
        if value is None:
            self._state = new_state
            return
        if not isinstance(value, (dict, OrderedDict)):
            raise TypeError("Incompatibe type: expected dict or OrderedDict")
        for attr in self.attributes:
            if attr in value and isinstance(value[attr], self.template[attr].datatype):
                new_state[attr] = value[attr]
        messages = dict()
        for attr in self.attributes:
            if self.template[attr].validator and not self.template[attr].validator(new_state[attr], new_state):
                messages[attr] = self.template[attr].errmsg
        if messages:
            raise SampleElementError(messages)
        self._state = new_state

    def __getstate__(self):
        return self.name, self.state

    def __setstate__(self, value: tuple):
        if len(value) != 2:
            raise ValueError("'value' must be tuple of the pair '<field_name>', {<dictionary_of_state>}")
        self.name, self.state = value

    @property
    def attributes(self):
        return self.template.keys()

    @property
    def defaults(self) -> OrderedDict:
        return OrderedDict(**{attr: self.get_default(attr) for attr in self.attributes})

    def get_default(self, attr: str):
        return self.name if self.template[attr].default == "{{name}}" else self.template[attr].default

    def __repr__(self):
        return repr(self.__getstate__())


class Field(SampleElement):
    _TEMPLATE = OrderedDict([
        ('mandatory', FieldType(bool, False,
                                check_mandatory_hidden,
                                'mandatory can not be equal hidden')),
        ('ctype', FieldType(str, "String",
                            check_ctype,
                            ERR_MSG_NOTCTYPE)),
        ('label', FieldType(str, "{{name}}",
                            None, None)),
        ('key', FieldType(bool, False,
                          check_key,
                          ERR_MSG_KEY_CALC)),
        ('calc', FieldType((tuple, list), None,
                           check_aggregates,
                           ERR_MSG_KEY_CALC + ERR_MSG_NOTAGGREGATED)),
        ('filtered', FieldType((tuple, list), None,
                               check_operations,
                               ERR_MSG_NOTOPERATION)),
        ('ordered', FieldType(bool, False,
                              None, None)),
        ('having', FieldType((tuple, list), None,
                             check_having,
                             'having-field can by set on only for calc-field.')),
        ('hidden', FieldType(bool, False,
                             check_hidden_mandatory,
                             'hidden can not be equal mandatory')),
        ('table', FieldType(str, 'main',
                            check_identifier,
                            ERR_MSG_NOTIDENTIFIER)),
        ('expression', FieldType(str, "{{name}}",
                                 check_identifier,
                                 ERR_MSG_NOTIDENTIFIER)),
        ('alias', FieldType(str, "{{name}}",
                            check_identifier,
                            ERR_MSG_NOTIDENTIFIER)),
    ])

    @property
    def sql_identifier(self):
        return f''' "{self._state['table']}"."{self._state['expression']}" '''

    @property
    def sql_alias(self):
        return f''' "{self._state['alias']}" '''

    @property
    def sql_column(self):
        return f'''{self.sql_identifier} AS {self.sql_alias} '''


class Param(SampleElement):
    _TEMPLATE = OrderedDict([
        ('ctype', FieldType(str, "String",
                            check_ctype,
                            ERR_MSG_NOTCTYPE)),
        ('label', FieldType(str, "{{name}}",
                            None, None)),
    ])


def check_from(val: dict, state: dict = None):
    return isinstance(val, dict) \
           and 'main' in val \
           and all(val.values()) \
           and all(check_identifier(alias) for alias in val)


def check_fields(val, state):
    messages = dict()
    for field_name, field_state in val.items():
        try:
            field = Field(field_name, **field_state)
            if field.state['table'] not in state['from']:
                messages[field.name] = "\n".join([
                    messages.get(field.name, ''),
                    f"{field.name}.table='{field.state['table']}' must be one of aliases ({state['from'].keys()})."])
        except SampleElementError as e:
            messages.update(e.errors)
    if messages:
        raise SampleElementError(messages)
    return True


def check_params(val, state):
    messages = dict()
    for val_name, val_state in val.items():
        try:
            Field(val_name, **val_state)
        except SampleElementError as e:
            messages.update(e.errors)
    if messages:
        raise SampleElementError(messages)
    return True


class Sample:
    """ Описание схемы выборки данных.

    Цель: гаранитровать логическую целостность структуры.

        Вход и выход - словарь описания схемы выборки данных.
        Внутрение структуры построены на использовании SampleElement.
        Если данные не полны, но есть значения по-умолчанию - они устанавливаются.
    """
    def __init__(self, metadata: dict = None):
        if metadata:
            self.__setstate__(metadata)
        else:
            self.tables = dict()
            self.fields = dict()
            self.params = dict()

    def __getstate__(self):
        return OrderedDict([
            ('tables', self.tables),
            ('fields', self.fields),
            ('params', self.params),
        ])

    def __setstate__(self, state: dict):
        self.tables = dict()
        self.fields = dict()
        self.params = dict()
        sample_messages = dict()

        tables_messages = dict()
        if 'tables' in state:
            for alias, sql_stmt in state['tables'].items():
                if not check_identifier(alias):
                    add_message(tables_messages,
                                f"tables[{alias}]",
                                ERR_MSG_NOTIDENTIFIER)
                    # tables_messages[f"tables[{alias}]"] =
                    # tables_messages.get(tables_messages[f"tables[{alias}]"], []).append(ERR_MSG_NOTIDENTIFIER)
                if not sql_stmt:
                    add_message(tables_messages,
                                f"tables[{alias}]",
                                'SQL statement is empty.')
                self.tables[alias] = sql_stmt
        else:
            add_message(sample_messages,
                        'sample',
                        "'tables' is not defined in sample.")

        fields_messages = dict()
        if 'fields' in state:
            for field_name, fields_state in state['fields'].items():
                attribute = f"fields[{field_name}]"
                try:
                    field = Field(field_name, **fields_state)
                    if field.state['table'] not in self.tables:
                        raise SampleElementError({
                            attribute:
                                [f"alias '{field.state['table']}' not in 'tables' ({','.join(self.tables)})"]
                        })
                    self.fields[field.name] = field.state
                except SampleElementError as e:
                    fields_messages[attribute] = fields_messages.get(f"fields[{field_name}]", [])
                    fields_messages[attribute].extend(
                        [f"'{field_param}': {err_msg}" for field_param, err_msg in e.errors.items()]
                    )
        else:
            add_message(sample_messages,
                        'sample',
                        "'fields' is not defined in sample.")

        params_messages = dict()
        if 'params' in state:
            for param_name, param_state in state['params'].items():
                try:
                    param = Param(param_name, **param_state)
                    self.params[param.name] = param.state
                except SampleElementError as e:
                    params_messages[f"params[{param_name}]"] = \
                        params_messages.get(f"params[{param_name}]", []).append(e.errors)
        else:
            add_message(sample_messages,
                        'sample',
                        "'params' is not defined in sample.")
        messages = {**sample_messages, **tables_messages, **fields_messages, **params_messages}
        if messages:
            raise SampleElementError(messages)

    @property
    def state(self):
        return self.__getstate__()

    @state.setter
    def state(self, state: dict):
        self.__setstate__(state)

    def sql_tables(self, fields: Union[Sequence[str], Set[str], FrozenSet[str]]) -> str:
        """
            Генерация списка колонок для фразы SELECT

        :param fields: коллекция имён полей
        :return: список колонок для фразы SELECT
        """
        using_tables = {
            state['table']
            for name, state in self.fields.items()
            if name in fields
        }
        return text(', '.join([
            f'({stmt}) AS "{alias}"'
            for alias, stmt in self.tables.items()
            if alias in using_tables
        ]))

    def __repr__(self):
        return repr(self.__getstate__())
