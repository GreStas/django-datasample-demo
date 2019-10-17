from django.contrib import admin

from .models import *


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('label', 'name', 'counts', 'price')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('label', 'name', 'manager')


@admin.register(Tarif)
class TarifAdmin(admin.ModelAdmin):
    list_display = ('service', 'product', 'price', 'is_active', 'archived')
