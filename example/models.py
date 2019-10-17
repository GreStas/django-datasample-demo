from django.contrib.auth import get_user_model
from django.db import models

__all__ = (
    'Catalog',
    'Product',
    'Service',
    'Tarif',
)


class Catalog(models.Model):
    class Meta:
        verbose_name = 'Группа товаров'
        verbose_name_plural = 'Каталог групп товаров'

    name = models.CharField(
        max_length=100,
        verbose_name='Наименование раздела каталога',
    )
    manager = models.ForeignKey(
        get_user_model(),
        related_name="%(class)s_managers",
        on_delete=models.PROTECT,
        db_index=True,
        verbose_name='Менеджер раздела каталога',
    )
    sellers = models.ManyToManyField(
        get_user_model(),
        related_name="%(class)s_sellers",
        db_index=True,
        verbose_name='Сертифицированные продавцы',
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    name = models.CharField(
        max_length=50,
        verbose_name='Наименование товара',
    )
    label = models.SlugField(
        verbose_name='Метка на ценнике и в чеках',
    )
    description = models.TextField(verbose_name='Подробное описание товара',)
    catalog = models.ForeignKey(
        Catalog,
        on_delete=models.PROTECT,
        db_index=True,
        verbose_name='Группа товаров из каталога',
    )
    price = models.DecimalField(
        max_digits=18, decimal_places=2,
        default=0.0,
        verbose_name='Цена',
    )
    counts = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество',
    )

    def __str__(self):
        return self.name


class Service(models.Model):
    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'

    name = models.CharField(
        max_length=50,
        verbose_name='Наименование услуги',
    )
    label = models.SlugField(
        verbose_name='Метка на ценнике и в чеках',
    )
    description = models.TextField(verbose_name='Подробное описание услуги',)
    manager = models.ForeignKey(
        get_user_model(),
        related_name="%(class)s_managers",
        on_delete=models.PROTECT,
        db_index=True,
        verbose_name='Менеджер услуги',
    )

    def __str__(self):
        return self.name


class Tarif(models.Model):
    class Meta:
        verbose_name = 'Тариф на услугу для товара'
        verbose_name_plural = 'Тарифы на услуги по товарам'

    product = models.ForeignKey(
        Product,
        null=True, blank=True,
        on_delete=models.CASCADE,
        db_index=True,
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        db_index=True,
    )
    price = models.DecimalField(
        max_digits=18, decimal_places=4,
        default=0.0,
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='Активна',
    )
    archived = models.BooleanField(
        default=False,
        verbose_name='Доступен только для истории',
    )
    def __str__(self):
        return f"{'[-] '*self.is_active}{self.service.label}" + ('- ' + self.product.label) if self.product else ''
