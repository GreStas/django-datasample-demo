"""
    DataSample - Модель/Шаблон/Схема организации доступа к данным в БД.

Далее используется термин Схема Выборки Данных (СВД), представленная классом datasample.elements.Sample

Структура СВД объединяет базовый SQL-запрос и описание параметров
с описанием возможностей в использования полей для :
* выборки (select)
* фильтров (where и having)
* группировки (group by)
* сортировки (order by)

Для возможности отладки использутся фнукции
* compose - компанует итоговый SQL-запрос
* execute- компанует итоговый SQL-запрос и делает выборку данных

Функция execute в дальнейшем может использоваться для реальной выборки данных
на основе (пример в example/tests/example_schema.json):
* отлаженной СВД (ключ "sample")
* переданных значений параметров (ключ "params")
* настроек выборки (ключ "options")
"""
from .elements import Sample, SampleElementError
from .validators import check_params, check_options
from .sqlalchemytools import compose, execute
