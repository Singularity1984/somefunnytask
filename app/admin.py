from django.contrib import admin
from .models import *

admin.site.site_header = "Управление магазином цветов"
admin.site.site_title = "Админка цветочного магазина"
admin.site.index_title = "Панель управления"

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(FlowerVariety)
class FlowerVarietyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'sale_price')

@admin.register(SupplyBatch)
class SupplyBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'variety', 'quantity_remaining', 'cut_date')
    list_filter = ('cut_date', 'variety')

@admin.register(ReadyBouquet)
class ReadyBouquetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)

admin.site.register(Packaging)
admin.site.register(BouquetRecipeItem)
admin.site.register(CustomBouquet)
admin.site.register(CustomBouquetItem)
admin.site.register(DeliverySlot)
admin.site.register(OrderItem)
admin.site.register(BouquetPhoto)
admin.site.register(StockAllocation)
admin.site.register(Review)