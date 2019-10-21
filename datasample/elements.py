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


# допустимые типы полей в СВД и трансляция их на типы Python
CTYPES = {
    "Boolean": (bool,),
    "String": (str,),
    "Integer": (int,),
    "Decimal": (float, Decimal),
}
# Допустимые операции над типами полей
OPERATIONS = {
    "Boolean": ('is null', 'is not null',),
    "String": ('is null', 'is not null', '=', '!=', 'in', 'not in', 'like', 'not like',),
    "Integer": ('is null', 'is not null', '=', '!=', 'in', 'not in', '<', '<=', '>', '>=', 'between', 'not between',),
    "Decimal": ('is null', 'is not null', '=', '!=', 'in', 'not in', '<', '<=', '>', '>=', 'between', 'not between',),
    "Date": ('is null', 'is not null', '=', '!=', 'in', 'not in', '<', '<=', '>', '>=', 'between', 'not between',),
}
# допустиые типы операндов для операций
# '<ctype>' - задумано как один из допустимых типов полей
# '<collection>' - задумано как последовательность из допустимых типов полей
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
# Допустимые функции агрегации данных
AGGREGATES = ('sum', 'avg', 'min', 'max',)

# Перечень шаблонов известных ошибок валидации
ERR_MSG_NOTCTYPE = f"'ctype' must be in {OPERATIONS.keys()}"
ERR_MSG_NOTIDENTIFIER = 'Value must be Python and SQL identifier compatible.'
ERR_MSG_NOTOPERATION = f"All values must be in ({OPERATIONS})."
ERR_MSG_NOTAGGREGATED = f"All values must be in ({AGGREGATES})."
ERR_MSG_KEY_CALC = "Only one of 'key' and 'calc' must by set on."

# Для описания параметров полей СВД используем структуру FieldType
# namedtuple позволяет работать с данными как с классом, при этом данные упорядочены как в кортеже
FieldType = namedtuple('FieldType', ('datatype', 'default', 'validator', 'errmsg',))


def check_val_ctype(val, ctype: str):
    """ Проверка значениен на допустимые типы полей """
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
    """
        Исключение для обрабатываемых пакетом ошибок

    self.errors - это словарь в котором
        Ключи - идентифицирут элемент, коолрый валидировался
        Значения - список развёрнутых сообщений об ошибках
    """
    def __init__(self, errors: dict, **kwargs):
        super().__init__(**kwargs)
        self.errors = errors

    def __str__(self):
        return '\n'.join([
            "{key}: {msgs}".format(key=key, msgs=';\t\n'.join(msgs))
            for key, msgs in self.errors.items()
        ])

#
# Все функции check_* предназначены для конкретных валидаций
# первый параметр - само проверяемое значение
# второй параметр - полное состояние валидируемой структуры,
#                   так как некотрые проверки являются кросс-проверками
#                   или взаимо-дополняюцие
#
# Имя функции содержит перечень параметров поля, которые проверяются.
# Напрмер, check_mandatory_hidden проверяет mandatory в сваязке с hidden.
#
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
    """
        Базовая функциональность любого элемента СВД

    Атрибуты
    ========
    _TEMPLATE - словарь с описанием атрибутов полей в структуре FieldType
                В наследниках необходимо определить _TEMPLATE своей структурой описания элемента
    """

    _TEMPLATE = OrderedDict([('label', FieldType(str, "{{name}}", None, None))])

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.state = kwargs

    @property
    def template(self) -> dict:
        """ Защищаем от изменения удобную нам mutable стурктуру данных OrderedDict """
        return self._TEMPLATE

    @property
    def name(self):
        """ Установка имени элемента должна валидироваться. Поэтому защищаем свойством. """
        return self._name

    @name.setter
    def name(self, value: str):
        """ Установка имени элемента должна валидироваться. Поэтому защищаем свойством. """
        if isinstance(value, str) and value.isidentifier():
            self._name = value
        else:
            raise TypeError("'name' must be string and Python identifier compatible.")

    @property
    def state(self):
        """ Установка внутреннего состояния элемента должна валидироваться. Поэтому защищаем свойством. """
        return self._state

    @state.setter
    def state(self, value: dict):
        """ Установка внутреннего состояния элемента должна валидироваться. Поэтому защищаем свойством. """
        new_state = self.defaults  # Используем своё свойство, которое гарантирует тип и результат.
        if value is None:
            self._state = new_state  # по-умолчанию возвращаем структуру со сзначениями по-умолчанию
            return
        # Контролируем типы на входе, чтобы потом в неожиданном месте не наскочить на исключение.
        if not isinstance(value, (dict, OrderedDict)):
            raise TypeError("Incompatibe type: expected dict or OrderedDict")
        # Если для ключей из шаблона структуры элемента валидируем тип и перекрываем в итоговой структуре
        for attr in self.attributes:
            if attr in value and isinstance(value[attr], self.template[attr].datatype):
                new_state[attr] = value[attr]
        # Валидация всей структуры на основе данных шаблона
        messages = dict()
        for attr in self.attributes:
            if self.template[attr].validator and not self.template[attr].validator(new_state[attr], new_state):
                messages[attr] = self.template[attr].errmsg  # ошибки валидации накапливаем
        if messages:
            raise SampleElementError(messages)
        self._state = new_state

    def __getstate__(self):
        return self.name, self.state

    def __setstate__(self, value: tuple):
        if len(value) != 2:
            raise ValueError("'value' must be tuple of the pair '<field_name>', {<dictionary_of_state>}")
        self.name, self.state = value  # валиадци будет выпонена в сеттерах свойств

    @property
    def attributes(self):
        return self.template.keys()

    @property
    def defaults(self) -> OrderedDict:
        """ Создаём новый экземпляр структуры элемента из шаблона """
        return OrderedDict(**{attr: self.get_default(attr) for attr in self.attributes})

    def get_default(self, attr: str):
        """
            Получить значение атрибута по-умолчанию

        имя атрибута {{name}} - зарезервировано для ситуаций, когда значение опирается на имя элемента
        """
        return self.name if self.template[attr].default == "{{name}}" else self.template[attr].default

    def __repr__(self):
        return repr(self.__getstate__())


class Field(SampleElement):
    """ Описание Поля в СВД """

    _TEMPLATE = OrderedDict([
        # обязательный для включения в выборку
        ('mandatory', FieldType(bool, False,
                                check_mandatory_hidden,
                                'mandatory can not be equal hidden')),
        # Тип поля
        ('ctype', FieldType(str, "String",
                            check_ctype,
                            ERR_MSG_NOTCTYPE)),
        # Метка для форм и отчётов
        ('label', FieldType(str, "{{name}}",
                            None, None)),
        # Признак, что поле может быть включено в группировку
        ('key', FieldType(bool, False,
                          check_key,
                          ERR_MSG_KEY_CALC)),
        # Признак, что полле может быть включено в аггрегацию
        ('calc', FieldType((tuple, list), None,
                           check_aggregates,
                           ERR_MSG_KEY_CALC + ERR_MSG_NOTAGGREGATED)),
        # Признак, что поле можт участвовать в where
        ('filtered', FieldType((tuple, list), None,
                               check_operations,
                               ERR_MSG_NOTOPERATION)),
        # Признак, что поле может быть включено в сортировку
        ('ordered', FieldType(bool, False,
                              None, None)),
        # Признак, что поле может быть включено в отбор
        ('having', FieldType((tuple, list), None,
                             check_having,
                             'having-field can by set on only for calc-field.')),
        # Признак, что это поле не преназначено для пользовательского вывода,
        # но, например, необходимо для фильтров или сортировок или т.п.
        ('hidden', FieldType(bool, False,
                             check_hidden_mandatory,
                             'hidden can not be equal mandatory')),
        # Из какой таблицы это поле
        ('table', FieldType(str, 'main',
                            check_identifier,
                            ERR_MSG_NOTIDENTIFIER)),
        # SQL-выражене для вычисления поля
        ('expression', FieldType(str, "{{name}}",
                                 check_identifier,
                                 ERR_MSG_NOTIDENTIFIER)),
        # SQL-алиас этого поля
        ('alias', FieldType(str, "{{name}}",
                            check_identifier,
                            ERR_MSG_NOTIDENTIFIER)),
    ])

    @property
    def sql_identifier(self):
        """ Получить полный идентификатор поля для SQL """
        return f''' "{self._state['table']}"."{self._state['expression']}" '''

    @property
    def sql_alias(self):
        """ Получить SQL-алиас поля"""
        return f''' "{self._state['alias']}" '''

    @property
    def sql_column(self):
        """ Получить полный идентификатор поля для SQL c аласом поля для SQL-фразы select"""
        return f'''{self.sql_identifier} AS {self.sql_alias} '''


class Param(SampleElement):
    """ Описание Параметра в СВД """
    _TEMPLATE = OrderedDict([
        # Тип параметра
        ('ctype', FieldType(str, "String",
                            check_ctype,
                            ERR_MSG_NOTCTYPE)),
        # Метка для форм
        ('label', FieldType(str, "{{name}}",
                            None, None)),
    ])


class Sample:
    """ Описание схемы выборки данных (СВД).

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

    def __setstate__(self, state: dict) -> None:
        """
            Принять описание СВД, проверить, дополнить и сохранить в атрибуты класса

        :param state: словарь с описанием СВД
        :return: None
        """
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
                attribute = f"fields[{field_name}]"  # для точной идентификации где произошла ошибка валидации
                try:
                    # прогоняем через класс-описатель поля, чтобы проверить и дополнить структуру
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
                    # прогоняем через класс-описатель параметра, чтобы проверить и дополнить структуру
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
            Генерация списка таблиц для SQL-фразы WHERE

        :param fields: коллекция имён полей
        :return: список таблиц с алиасами
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
