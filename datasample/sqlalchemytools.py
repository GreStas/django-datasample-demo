"""
    Модуль преобразования СВД + значения параметров + Настройки в SQL
"""
from typing import Sequence  # , List, Tuple, Dict, DefaultDict, Set, FrozenSet, Union
from sqlalchemy import create_engine
from sqlalchemy.sql import text, select

from .elements import Sample, Field, OPERATIONS_ARGS
from .validators import check_params, check_options

__all__ = (
    'execute',
    'compose',
)


def execute(sample_meta: dict, params: dict, options: dict, db_settings: dict):
    """
        Выполнить запрос согласно параметризации

    :param sample_meta: описатель схемы доступа к данным
    :param params: значения параметров согласно схемы
    :param options: значения настроек согласно схемы
    :param db_settings: database connection settings like django.conf.settings.DATABASES
    :return:
    """
    # db_settings = dbs if dbs else settings.DATABASES.get('default')
    engine = create_engine(
        f"postgresql:/"
        f"/{db_settings.get('USER')}"
        f":{db_settings.get('PASSWORD')}"  # f":{db_settings.get('PASSWORD')}" 
        f"@{db_settings.get('HOST')}"
        f":{db_settings.get('PORT') if db_settings.get('PORT') else '5432'}"
        f"/{db_settings.get('NAME')}"
    )
    conn = engine.connect()
    query, kwargs = compose(sample_meta, params, options)
    return conn.execute(query, **kwargs).fetchall()


def compose(sample_meta: dict, params: dict, options: dict):
    """ Компиляция схемы и настроек запроса

    для использования в sqlalchemy.sql.select

    Рекомендуется для использования Разработчиками отчётов
    (как Back-End так и Fron-End) для проверки в тестах
    корректности сочетания значений настроек и параметров с описанием схемы доступа к данным.

    :param sample_meta: описатель схемы доступа к данным
    :param params: значения параметров согласно схемы
    :param options: значения настроек согласно схемы
    :return: tuple(
        query: str, - текст SQL-запроса с использованием bindary variables в нотации :BINDNAME
        dict(<bind_name>: <bind_value>), - словарь bindary variables
    )
    """
    # Валидируем описание СВД
    sample = Sample(sample_meta)
    # Валидируем параметры на соответсвие СВД
    check_params(params, sample)
    # Валидируем настроки на соответствие СВД
    check_options(options, sample)

    # Поля для SQL-фразы SELECT
    column_fields = [name for name, *_ in options['fields']]
    # Поля для SQL-фразы GROUP BY
    group_fields = options['group'] if 'group' in options else []
    # Поля для SQL-фразы HAVING
    having_fields = [field for field, *_ in options['having']] if 'having' in options else []
    # Поля для SQL-фразы ORDER BY
    order_fields = [field for field, *_ in options['order']] if 'order' in options else []
    # Все используемые поля
    using_fields = {*column_fields, *group_fields, *having_fields, *order_fields}

    fields = dict()  # Все используемые поля в словаре ИмяПоля:ЭлементПоля
    for field_name in using_fields:
        fields[field_name] = Field(field_name, **sample.fields)

    #
    # Сосавляем текст SQL-запроса
    #
    query = select([  # SELECT
        text(
            f'{operation}({fields[field_name].sql_identifier}) AS {fields[field_name].sql_alias} ' if operation
            else fields[field_name].sql_column
        )
        for field_name, operation in options['fields'] if field_name in column_fields
    ]
    ).select_from(  # FROM
        sample.sql_tables(using_fields)
    )

    # WHERE
    if 'filters' in options:
        filters = []
        for field_name, operation, args in options['filters']:
            filters.append(
                f'{fields[field_name].sql_identifier} '
                f'{operation} '
                f'{sql_op_args(operation, args, fields[field_name].state["ctype"])}'
            )
        query = query.where(text(
            '\n  AND '.join(filters)
        ))

    # GROUP BY
    if 'group' in options:
        query = query.group_by(text(', '.join([
            f'{fields[field_name].sql_identifier}'
            for field_name in options['group']
        ])))

    # HAVING
    if 'having' in options:
        havings = []
        for field_name, operation, args in options['having']:
            operation_for_column = options['fields'][column_fields.index('amount_11')][1]
            if operation_for_column:
                having_identifier = f'{operation_for_column}({fields[field_name].sql_identifier})'
            else:
                having_identifier = fields[field_name].sql_identifier
            havings.append(
                f'{having_identifier} '
                f'{operation} '
                f'{sql_op_args(operation, args, fields[field_name].state["ctype"])}'
            )
        query = query.having(text(
            '\n  AND '.join(havings)
        ))

    # ORDER BY
    if 'order' in options:
        query = query.order_by(text(', '.join([
            f'{fields[field_name].sql_alias} {direct}'
            for field_name, direct in options['order']
        ])))

    kwargs = {**params}
    return query, kwargs


def sql_op_args(op: str, args: Sequence, ctype: str) -> str:
    """ Транслировать значения операндов в строку """
    if OPERATIONS_ARGS[op] == tuple():
        return ''
    if OPERATIONS_ARGS[op] == ('<ctype>',):
        return repr(args[0])
    if OPERATIONS_ARGS[op] == ('<collection>',):
        return f"({','.join([repr(arg) for arg in args])})"
    if op in ('between', 'not between'):
        return f"{args[0]} and {args[1]}"
