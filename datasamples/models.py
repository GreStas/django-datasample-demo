import pickle
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth import get_user_model
from django.db.transaction import atomic
from django.core.exceptions import ValidationError

__all__ = ('Sample',)


class Sample(models.Model):
    class Meta:
        unique_together = ('name', 'version',)
        verbose_name = "описание схемы выборки данных (СВД)"
        verbose_name_plural = "описания схем выборки данных (СВД)"

    name = models.CharField(max_length=32,
                            verbose_name="ID",
                            help_text="Идентификатор описания схемы компоновки данных")
    description = models.TextField(verbose_name="Описание",
                                   help_text="Подробное описание схемы компоновки данных")
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name="Создана",
                                   help_text="Дата создания")
    updated = models.DateTimeField(auto_now=True,
                                   verbose_name="Обновлена",
                                   help_text="Дата последнего изменения")
    is_active = models.BooleanField(default=False,
                                    verbose_name="Активна",
                                    help_text="Доступна для использования")
    deleted = models.BooleanField(default=False,
                                  verbose_name="Удалена",
                                  help_text="Пометка об удалении")
    version = models.CharField(max_length=16,
                               verbose_name="Версия",
                               help_text="устанавливается вручную")
    revision = models.BigIntegerField(default=0,
                                      verbose_name="№ изменения",
                                      help_text="порядковый номер изменения - автоинкримент")
    publisher = models.ForeignKey(
        get_user_model(),
        related_name="sample_publisher_set",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Опубликовал",
        help_text="Кто последний менял name, description, is_active, deleted, version",
    )
    author = models.ForeignKey(
        get_user_model(),
        related_name="sample_author_set",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Редактор",
        help_text="Кто последний менял description, metadata",
    )
    obj = models.BinaryField(help_text="бинарное представления объекта Sample")
    src = JSONField(help_text="Читабельное представление объекта Sample. "
                              "Автоматически генерируется из поля 'Sample.obj'")

    def __str__(self):
        return self.name

    def clean(self):
        messages = dict()
        if not str(self.name).isidentifier():
            messages.update({"name": [f"name is not Python identifier."]})
        if messages:
            raise ValidationError(messages)

    @atomic
    def save(self, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if bytes(self.obj) != bytes(old.obj):
                self.revision = old.revision + 1
        else:
            self.revision = 1
        # Если объект новый, или изменилась схема,
        # то прокачать metadata через объект Sample
        if not self.pk or bytes(self.obj) != bytes(old.obj):
            obj = pickle.loads(self.obj)
            self.src = obj.__getstate__()
        super().save(**kwargs)
