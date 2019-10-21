from .utils import add_message
from .elements import Sample, CTYPES, SampleElementError, check_op_args

__all__ = (
    'check_params',
    'check_options',
)


def check_params(params: dict, sample: Sample) -> bool:
    """
        Проверить параметры на соответсвие описанию схемы выборки

    :param params: словарь значений параметров
    :param sample: объект Описание схемы выборки данных
    :return: True или вызов исключения
    """
    messages = dict()
    for param_name, param_state in sample.params.items():
        if param_name not in params:
            raise ValueError(f"Parameter '{param_name}' is not defined.")
        elif not isinstance(params[param_name], CTYPES[param_state['ctype']]):
            messages[f"params[{param_name}]"] = \
                f"Incorect type: given {type(params[param_name])} but waiting one of {CTYPES[param_state['ctype']]}"
    if messages:
        raise SampleElementError(messages)
    return True


def check_options(options: dict, sample: Sample):
    """ Проверить настройки на соответсвие описанию схемы выборки """
    messages = dict()

    # Поля должны быть из описания схемы, не скрытые, и обязательные
    if 'fields' in options.keys():
        if not isinstance(options['fields'], (tuple, list, set)):
            add_message(messages,
                        f"options[fields]",
                        f"'fields' должно быть перечислением имён полей.")
        # Собрать в options_fields множество всех имён полей, упомянутых в настройках
        options_fields = set()
        for field in options['fields']:
            if isinstance(field, str):
                options_fields.add(field)
            elif isinstance(field, (tuple, list)):
                options_fields.add(field[0])
            else:
                add_message(messages, 'options[fields]',
                            f"'{field}' описание поля может быть "
                            f"<field_name>:str | tuple(<field_name>:str, <operation>:str)")

        # Допустимые поля СВД для использования в настройках
        sample_fields = {name for name, state in sample.fields.items() if not state['hidden']}
        # Не предусмотренные в СВД поля
        unknown_fields = options_fields - sample_fields
        if unknown_fields:
            add_message(messages,
                        'options[fields]',
                        f"не известные поля: {unknown_fields}")
        # Обязательныве поля, которые отсутствуют в настройках
        mandatory_absent_fields = \
            {name for name, state in sample.fields.items() if state['mandatory']} - options_fields
        if mandatory_absent_fields:
            add_message(messages,
                        'options[fields]',
                        f"отсутсвуют обязательные поля: {mandatory_absent_fields}")
    else:
        add_message(messages,
                    'options',
                    "В настройках отсутсвет описание полей 'fields'")

    if 'filters' in options.keys():
        for field_name, operation, args in options['filters']:
            # В фильтрации могут участвовать только известные поля
            if field_name not in sample.fields.keys():
                add_message(messages,
                            'options[filters]',
                            f"не известное поле в фильтре: {field_name}")

            # В фильтрации могут участвовать только поля с признаком фильтарции
            # и допустимой для этого типа операцией сравнения
            elif bool(sample.fields[field_name]['filtered']) and operation not in sample.fields[field_name]['filtered']:
                add_message(messages,
                            f"options[filters][{field_name}]",
                            f"не допустимая операция: {repr(operation)}")
            else:
                # Проверяем корректность операндов
                try:
                    check_op_args(operation, args)
                except ValueError as e:
                    add_message(messages,
                                f"options[filters][{field_name}]",
                                f"не допустимые параметры для '{operation}'({repr(args)}): {str(e)}")

    if 'group' in options.keys():
        if not isinstance(options['group'], (tuple, list, set)):
            add_message(messages,
                        f"options[group]",
                        f"'group' должно быть перечислением имён полей.")
        # Могут входить только ключевые поля
        order_fields = {*options['group']}
        sample_orders = {name for name, state in sample.fields.items() if state['key']}
        unknown_orders = order_fields - sample_orders
        if unknown_orders:
            add_message(messages,
                        'options[group]',
                        f"не известные или недопустимые для группировки поля: {unknown_orders}")

    if 'having' in options.keys():
        if not isinstance(options['having'], (tuple, list, set)):
            add_message(messages,
                        f"options[having]",
                        f"'having' должно быть перечислением имён полей.")
        # Могут входить только вычислимые поля
        having_fields = {descriptor[0] for descriptor in options['having']}
        sample_calcs = {name for name, state in sample.fields.items() if state['having']}
        unknown_havings = having_fields - sample_calcs
        if unknown_havings:
            add_message(messages,
                        'options[having]',
                        f"не известные или недопустимые для отсева поля: {unknown_havings}")
        # Только допустимые операции
        for field_name, operation, args in options['having']:
            if bool(sample.fields[field_name]['having']) and operation not in sample.fields[field_name]['having']:
                add_message(messages,
                            f"options[having][{field_name}]",
                            f"недопустимая операция: {repr(operation)}")

    if 'order' in options.keys():
        if not isinstance(options['order'], (tuple, list, set)):
            add_message(messages,
                        f"options[order]",
                        f"'order' должно быть перечислением имён полей.")
        order_fields = {field for field, *_ in options['order']}
        sample_orders = {name for name, state in sample.fields.items() if state['ordered']}
        unknown_orders = order_fields - sample_orders
        if unknown_orders:
            add_message(messages,
                        'options[order]',
                        f"не известные или недопустимые для сортировки поля: {unknown_orders}")
        for field_name, direct in options['order']:
            if direct not in ('asc', 'desc'):
                add_message(messages,
                            f"options[order]",
                            f"неизвестный тип сортировки '{direct}' для поля {field_name}.")

    if messages:
        raise SampleElementError(messages)
    return True
