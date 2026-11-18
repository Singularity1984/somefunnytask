from django.db import models
from django.contrib.auth.models import User

class Supplier(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название поставщика")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uniq_supplier_name"),
        ]

    def __str__(self):
        return self.name

class FlowerVariety(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название цветка")
    color = models.CharField(max_length=50, verbose_name="Цвет")
    stem_length_cm = models.IntegerField(verbose_name="Длина стебля (см)")
    purchase_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Закупочная цена")
    sale_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена продажи")

    class Meta:
        verbose_name = "Сорт цветка"
        verbose_name_plural = "Сорта цветов"
        ordering = ["name", "color"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "color", "stem_length_cm"],
                name="uniq_variety_name_color_stem",
            ),
            models.CheckConstraint(
                condition=models.Q(stem_length_cm__gt=0),
                name="chk_variety_stem_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(purchase_price__gte=0),
                name="chk_variety_purchase_nonneg",
            ),
            models.CheckConstraint(
                condition=models.Q(sale_price__gte=models.F("purchase_price")),
                name="chk_variety_sale_ge_purchase",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.color})"

class SupplyBatch(models.Model):
    variety = models.ForeignKey(FlowerVariety, on_delete=models.CASCADE, verbose_name="Сорт цветка")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name="Поставщик")
    quantity_received = models.IntegerField(verbose_name="Получено (шт)")
    quantity_remaining = models.IntegerField(verbose_name="Остаток (шт)")
    delivery_date = models.DateField(verbose_name="Дата поставки")
    cut_date = models.DateField(verbose_name="Дата среза")
    purchase_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Закупочная цена")

    class Meta:
        verbose_name = "Партия поставки"
        verbose_name_plural = "Партии поставок"
        ordering = ["cut_date", "delivery_date"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity_received__gte=0),
                name="chk_batch_qty_received",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_remaining__gte=0),
                name="chk_batch_qty_remaining",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_remaining__lte=models.F("quantity_received")),
                name="chk_batch_remaining_le_recv",
            ),
            models.CheckConstraint(
                condition=models.Q(purchase_price__gte=0),
                name="chk_batch_price_nonneg",
            ),
        ]

    def __str__(self):
        return f"Партия {self.variety.name} от {self.cut_date} (остаток: {self.quantity_remaining})"

class Packaging(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название упаковки")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена")
    stock_qty = models.IntegerField(verbose_name="Количество на складе")

    class Meta:
        verbose_name = "Упаковка"
        verbose_name_plural = "Упаковки"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uniq_packaging_name"),
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="chk_packaging_price",
            ),
            models.CheckConstraint(
                condition=models.Q(stock_qty__gte=0),
                name="chk_packaging_stock",
            ),
        ]

    def __str__(self):
        return self.name

class ReadyBouquet(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название букета")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    photo = models.ImageField(upload_to='bouquets/', blank=True, null=True, verbose_name="Фото")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Готовый букет"
        verbose_name_plural = "Готовые букеты"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["name"], name="uniq_bouquet_name"),
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="chk_bouquet_price",
            ),
        ]

    def __str__(self):
        return self.name

class BouquetRecipeItem(models.Model):
    bouquet = models.ForeignKey(ReadyBouquet, related_name='recipe', on_delete=models.CASCADE, verbose_name="Букет")
    variety = models.ForeignKey(FlowerVariety, on_delete=models.CASCADE, verbose_name="Сорт цветка")
    stems_count = models.IntegerField(verbose_name="Количество стеблей")

    class Meta:
        verbose_name = "Состав букета"
        verbose_name_plural = "Составы букетов"
        ordering = ["bouquet", "variety"]
        constraints = [
            models.UniqueConstraint(
                fields=["bouquet", "variety"],
                name="uniq_recipe_bouquet_variety",
            ),
            models.CheckConstraint(
                condition=models.Q(stems_count__gt=0),
                name="chk_recipe_stems_positive",
            ),
        ]

    def __str__(self):
        return f"{self.bouquet.name} - {self.variety.name} ({self.stems_count} шт)"

class CustomBouquet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Пользователь")
    packaging = models.ForeignKey(Packaging, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Упаковка")
    card_text = models.CharField(max_length=255, blank=True, verbose_name="Текст открытки")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Итоговая цена")
    is_ordered = models.BooleanField(default=False, verbose_name="Заказан")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Собранный букет"
        verbose_name_plural = "Собранные букеты"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_price__gte=0),
                name="chk_custom_total_nonneg",
            ),
        ]

    def __str__(self):
        if self.pk:
            return f"Собранный букет №{self.pk}"
        return "Новый собранный букет"
class CustomBouquetItem(models.Model):
    custom_bouquet = models.ForeignKey(CustomBouquet, related_name='items', on_delete=models.CASCADE, verbose_name="Собранный букет")
    variety = models.ForeignKey(FlowerVariety, on_delete=models.CASCADE, verbose_name="Сорт цветка")
    stems_count = models.IntegerField(verbose_name="Количество стеблей")

    class Meta:
        verbose_name = "Позиция собранного букета"
        verbose_name_plural = "Позиции собранных букетов"
        ordering = ["custom_bouquet", "variety"]
        constraints = [
            models.UniqueConstraint(
                fields=["custom_bouquet", "variety"],
                name="uniq_custom_item_bq_variety",
            ),
            models.CheckConstraint(
                condition=models.Q(stems_count__gt=0),
                name="chk_citem_stems_positive",
            ),
        ]

    def __str__(self):
        return f"{self.custom_bouquet} - {self.variety.name} ({self.stems_count} шт)"

class DeliverySlot(models.Model):
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")

    class Meta:
        verbose_name = "Интервал доставки"
        verbose_name_plural = "Интервалы доставки"
        ordering = ["date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["date", "start_time", "end_time"],
                name="uniq_delivery_slot",
            ),
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="chk_slot_time_order",
            ),
        ]

    def __str__(self):
        return f"{self.date} ({self.start_time} - {self.end_time})"

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('reserved', 'Зарезервирован'),
        ('assembly', 'Сборка'),
        ('on_approval', 'На согласовании фото'),
        ('approved', 'Одобрен'),
        ('delivering', 'У курьера'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Покупатель")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    delivery_slot = models.ForeignKey(DeliverySlot, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Интервал доставки")
    address = models.TextField(verbose_name="Адрес")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="chk_order_total_nonneg",
            ),
        ]

    def __str__(self):
        if self.pk:
            return f"Заказ №{self.pk}"
        return "Новый заказ"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Заказ")
    ready_bouquet = models.ForeignKey(ReadyBouquet, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Готовый букет")
    custom_bouquet = models.ForeignKey(CustomBouquet, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Свой букет")
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за шт")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"
        ordering = ["order", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="chk_orderitem_qty_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="chk_orderitem_price_nonneg",
            ),
            models.CheckConstraint(
                condition=models.Q(ready_bouquet__isnull=False) | models.Q(custom_bouquet__isnull=False),
                name="chk_orderitem_one_bouquet",
            ),
            models.CheckConstraint(
                condition=models.Q(ready_bouquet__isnull=True) | models.Q(custom_bouquet__isnull=True),
                name="chk_orderitem_not_both",
            ),
        ]

    def __str__(self):
        return f"Позиция заказа №{self.order_id} - {self.quantity} шт"

class BouquetPhoto(models.Model):
    order = models.ForeignKey(Order, related_name='photos', on_delete=models.CASCADE, verbose_name="Заказ")
    image = models.ImageField(upload_to='order_photos/', verbose_name="Фото")
    is_approved = models.BooleanField(default=False, verbose_name="Одобрено клиентом")
    buyer_comment = models.TextField(blank=True, verbose_name="Комментарий клиента")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Фото готового букета"
        verbose_name_plural = "Фото готовых букетов"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Фото к заказу №{self.order_id}"

class StockAllocation(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Заказ")
    batch = models.ForeignKey(SupplyBatch, on_delete=models.CASCADE, verbose_name="Партия")
    stems_count = models.IntegerField(verbose_name="Списано стеблей")
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Себестоимость")

    class Meta:
        verbose_name = "Списание партии"
        verbose_name_plural = "Списания партий (FIFO)"
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "batch"],
                name="uniq_stock_order_batch",
            ),
            models.CheckConstraint(
                condition=models.Q(stems_count__gt=0),
                name="chk_stock_stems_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_cost__gte=0),
                name="chk_stock_cost_nonneg",
            ),
        ]

    def __str__(self):
        return f"Списание по заказу №{self.order_id}: {self.stems_count} шт"

class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, verbose_name="Заказ")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    rating = models.IntegerField(verbose_name="Оценка (1-5)")
    text = models.TextField(verbose_name="Текст отзыва")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="chk_review_rating_range",
            ),
        ]

    def __str__(self):
        return f"Отзыв к заказу №{self.order_id}: {self.rating}/5"