from django.db import models

# Create your models here.
from django.db import models

from django.db import models
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField("Nombre", max_length=200)
    slug = models.SlugField("Slug", max_length=220, unique=True)
    description = models.TextField("Descripción", blank=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    price = models.DecimalField("Precio base", max_digits=10, decimal_places=2)
    featured = models.BooleanField("Destacado", default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"Imagen de {self.product.name}"

class Supply(models.Model):
    name = models.CharField("Nombre", max_length=150)
    type = models.CharField("Tipo", max_length=100, blank=True)
    quantity = models.DecimalField("Cantidad disponible", max_digits=10, decimal_places=2)
    unit = models.CharField("Unidad", max_length=50, blank=True, null=True)
    brand = models.CharField("Marca", max_length=100, blank=True)
    color = models.CharField("Color", max_length=50, blank=True)

    class Meta:
        verbose_name = "Insumo"
        verbose_name_plural = "Insumos"

    def __str__(self):
        return self.name

class Order(models.Model):
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
        ('presencial', 'Presencial'),
        ('web', 'Sitio Web'),
        ('otro', 'Otro'),
    ]

    STATUS_CHOICES = [
        ('solicitado','Solicitado'),
        ('aprobado', 'Aprobado'),
        ('en_proceso', 'En proceso'),
        ('realizada', 'Realizada'),
        ('entregada', 'Entregada'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]

    PAYMENT_STATUS = [
        ('pendiente','Pendiente'),
        ('parcial','Parcial'),
        ('pagado','Pagado'),
    ]

    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer_name = models.CharField("Nombre cliente", max_length=200)
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Teléfono / Red social", max_length=100, blank=True)
    product_ref = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField("Descripción del pedido", blank=True)
    platform = models.CharField("Plataforma", max_length=50, choices=PLATFORM_CHOICES, default='web')
    requested_date = models.DateField("Fecha requerida", null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField("Estado", max_length=30, choices=STATUS_CHOICES, default='solicitado')
    payment_status = models.CharField("Estado de pago", max_length=20, choices=PAYMENT_STATUS, default='pendiente')
    total_price = models.DecimalField("Precio final (opcional)", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        return f"Pedido {self.id} - {self.customer_name}"

class OrderImage(models.Model):
    order = models.ForeignKey(Order, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='orders/')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagen pedido {self.order.id}"

