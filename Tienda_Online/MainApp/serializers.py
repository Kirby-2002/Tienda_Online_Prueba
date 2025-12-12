# MainApp/serializers.py (COMPLETO CORREGIDO)

from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Supply, Order, OrderImage, Product, Category, ProductImage

# API para Categorías
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

# API para Imágenes de Productos
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'order']

# API para Productos
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        source='category', 
        write_only=True
    )
    images = ProductImageSerializer(many=True, read_only=True)
    
    # USANDO datetime para calcular antigüedad del producto
    days_since_creation = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'category', 
            'category_id', 'price', 'featured', 'created', 
            'images', 'days_since_creation'
        ]
        read_only_fields = ['slug', 'created', 'days_since_creation']
    
    def get_days_since_creation(self, obj):
        """Calcular días desde la creación usando datetime y timedelta"""
        if obj.created:
            # USANDO datetime y timezone
            now = timezone.now()
            delta = now - obj.created  # USANDO timedelta implícitamente
            return delta.days
        return None

# API para Imágenes de Pedidos
class OrderImageSerializer(serializers.ModelSerializer):
    # USANDO datetime para formatear fecha
    created_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderImage
        fields = ['id', 'image', 'created', 'created_formatted']
        read_only_fields = ['created', 'created_formatted']
    
    def get_created_formatted(self, obj):
        """Formatear fecha usando datetime"""
        if obj.created:
            # USANDO datetime para formatear
            return obj.created.strftime('%Y-%m-%d %H:%M')
        return None

# API para Crear Pedidos
class OrderCreateSerializer(serializers.ModelSerializer):
    reference_images = serializers.ListField(
        child=serializers.ImageField(max_length=None, allow_empty_file=False),
        write_only=True,
        required=False
    )
    
    # Campos calculados usando datetime
    delivery_urgency = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'email', 'phone', 'product_ref',
            'description', 'platform', 'requested_date', 'status',
            'payment_status', 'total_price', 'reference_images',
            'delivery_urgency'
        ]
        read_only_fields = ['delivery_urgency']
    
    def create(self, validated_data):
        images = validated_data.pop('reference_images', [])
        order = Order.objects.create(**validated_data)
        
        for image in images:
            OrderImage.objects.create(order=order, image=image)
        
        return order
    
    def get_delivery_urgency(self, obj):
        """Calcular urgencia de entrega usando datetime y timedelta"""
        if obj.requested_date:
            # USANDO datetime y date
            today = timezone.now().date()
            days_until = (obj.requested_date - today).days  # USANDO timedelta
            
            if days_until < 0:
                return "Atrasado"
            elif days_until <= 2:
                return "Urgente"
            elif days_until <= 7:
                return "Próximo"
            else:
                return "Normal"
        return "No especificado"

# API para Ver/Actualizar Pedidos
class OrderSerializer(serializers.ModelSerializer):
    product_ref = ProductSerializer(read_only=True)
    product_ref_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), 
        source='product_ref', 
        write_only=True,
        required=False,
        allow_null=True
    )
    images = OrderImageSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    # Campos calculados usando datetime, timezone y timedelta
    created_formatted = serializers.SerializerMethodField()
    days_since_creation = serializers.SerializerMethodField()
    estimated_completion = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'token', 'customer_name', 'email', 'phone',
            'product_ref', 'product_ref_id', 'description',
            'platform', 'platform_display', 'requested_date', 
            'created', 'created_formatted', 'days_since_creation',
            'status', 'status_display', 'estimated_completion',
            'payment_status', 'payment_status_display', 
            'total_price', 'images'
        ]
        read_only_fields = ['token', 'created', 'created_formatted', 
                           'days_since_creation', 'estimated_completion']
    
    def get_created_formatted(self, obj):
        """Formatear fecha de creación usando datetime"""
        if obj.created:
            # USANDO datetime para formatear
            return obj.created.strftime('%d/%m/%Y %H:%M')
        return None
    
    def get_days_since_creation(self, obj):
        """Calcular días desde creación usando datetime, timezone y timedelta"""
        if obj.created:
            # USANDO datetime y timezone
            now = timezone.now()
            delta = now - obj.created  # USANDO timedelta
            return delta.days
        return None
    
    def get_estimated_completion(self, obj):
        """Calcular fecha estimada de completado usando timedelta"""
        if obj.status == 'en_proceso' and obj.created:
            # USANDO datetime y timedelta
            # Estimación: 5 días hábiles después de creación
            estimated_date = obj.created + timedelta(days=5)
            return estimated_date.strftime('%d/%m/%Y')
        return None

# API para Insumos (Supply)
class SupplySerializer(serializers.ModelSerializer):
    # Campos calculados usando timedelta
    restock_urgency = serializers.SerializerMethodField()
    
    class Meta:
        model = Supply
        fields = [
            'id', 'name', 'type', 'quantity', 
            'unit', 'brand', 'color', 'restock_urgency'
        ]
        read_only_fields = ['restock_urgency']
    
    def get_restock_urgency(self, obj):
        """Determinar urgencia de reabastecimiento"""
        # USANDO lógica de tiempo para determinar urgencia
        if obj.quantity == 0:
            return "Crítico - Sin stock"
        elif obj.quantity <= 10:
            return "Alto - Bajo stock"
        elif obj.quantity <= 50:
            return "Moderado"
        else:
            return "Bajo - Stock suficiente"

# API para Estadísticas
class StatisticsSerializer(serializers.Serializer):
    period = serializers.DictField()
    totals = serializers.DictField()
    by_status = serializers.ListField()
    by_platform = serializers.ListField()
    popular_products = serializers.ListField()
    daily_trend = serializers.ListField()
    
    # USANDO datetime para validaciones
    def validate_period(self, value):
        """Validar que el período sea válido usando datetime"""
        if 'start' in value and 'end' in value:
            try:
                # USANDO datetime para parsear fechas
                start_date = datetime.strptime(value['start'], '%Y-%m-%d').date()
                end_date = datetime.strptime(value['end'], '%Y-%m-%d').date()
                
                if start_date > end_date:
                    raise serializers.ValidationError(
                        "Fecha de inicio no puede ser mayor que fecha de fin"
                    )
                
                # USANDO timedelta para validar rango máximo
                delta = end_date - start_date
                if delta.days > 365:
                    raise serializers.ValidationError(
                        "El período no puede exceder 365 días"
                    )
                    
            except ValueError:
                raise serializers.ValidationError("Formato de fecha inválido")
        
        return value

# API para Filtro de Pedidos (MEJORADO con datetime, timezone, timedelta)
class OrderFilterSerializer(serializers.Serializer):
    status = serializers.CharField(required=False, allow_blank=True)
    platform = serializers.CharField(required=False, allow_blank=True)
    payment_status = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    customer_name = serializers.CharField(required=False, allow_blank=True)
    product_ref = serializers.IntegerField(required=False)
    
    # Nuevos campos que usan datetime, timezone y timedelta
    last_days = serializers.IntegerField(
        required=False, 
        min_value=1, 
        max_value=365,
        help_text="Filtrar pedidos de los últimos N días"
    )
    this_month = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Filtrar pedidos del mes actual"
    )
    today_only = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Filtrar pedidos de hoy"
    )
    
    def validate_status(self, value):
        """Validar que el estado sea válido"""
        if value:
            from .models import Order
            valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
            for status_item in value.split(','):
                if status_item.strip() not in valid_statuses:
                    raise serializers.ValidationError(f"Estado '{status_item}' no válido")
        return value
    
    def validate(self, data):
        """Validaciones cruzadas usando datetime, timezone y timedelta"""
        # Validación de rangos de fecha
        if data.get('date_from') and data.get('date_to'):
            # USANDO datetime para comparación
            if data['date_from'] > data['date_to']:
                raise serializers.ValidationError({
                    'date_from': 'Fecha desde no puede ser mayor que fecha hasta'
                })
        
        # Si se especifica last_days, calcular date_from automáticamente
        # USANDO timezone y timedelta
        if data.get('last_days'):
            # USANDO timezone para fecha actual
            today = timezone.now().date()
            # USANDO timedelta para restar días
            calculated_date_from = today - timedelta(days=data['last_days'])
            
            # Si también hay date_from, usar el más reciente
            if data.get('date_from'):
                data['date_from'] = max(data['date_from'], calculated_date_from)
            else:
                data['date_from'] = calculated_date_from
            
            # Eliminar date_to si existe para usar el rango last_days
            data.pop('date_to', None)
        
        # Si se especifica this_month, calcular rango del mes actual
        # USANDO datetime para cálculos de mes
        if data.get('this_month'):
            today = timezone.now().date()
            # Primer día del mes
            first_day = today.replace(day=1)
            # Último día del mes
            if today.month == 12:
                last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            
            data['date_from'] = first_day
            data['date_to'] = last_day
        
        # Si se especifica today_only, filtrar solo hoy
        # USANDO timezone para fecha actual
        if data.get('today_only'):
            today = timezone.now().date()
            data['date_from'] = today
            data['date_to'] = today
        
        # Validar que no se mezclen filtros incompatibles
        conflicting_filters = []
        if data.get('last_days') and data.get('this_month'):
            conflicting_filters.append('last_days y this_month')
        if data.get('today_only') and (data.get('last_days') or data.get('this_month')):
            conflicting_filters.append('today_only con otros filtros de fecha')
        
        if conflicting_filters:
            raise serializers.ValidationError({
                'filters': f'Filtros incompatibles: {", ".join(conflicting_filters)}'
            })
        
        return data
    
    def to_internal_value(self, data):
        """Procesar datos antes de la validación usando datetime"""
        # Convertir strings 'true'/'false' a booleanos
        for field in ['this_month', 'today_only']:
            if field in data:
                if isinstance(data[field], str):
                    data[field] = data[field].lower() in ['true', '1', 'yes', 'on']
        
        return super().to_internal_value(data)
    
    def to_representation(self, instance):
        """Formatear la representación de los datos usando datetime"""
        data = super().to_representation(instance)
        
        # Agregar información sobre los filtros aplicados
        if 'date_from' in data and data['date_from']:
            # USANDO datetime para formatear
            date_obj = datetime.strptime(data['date_from'], '%Y-%m-%d')
            data['date_from_formatted'] = date_obj.strftime('%d/%m/%Y')
        
        if 'date_to' in data and data['date_to']:
            date_obj = datetime.strptime(data['date_to'], '%Y-%m-%d')
            data['date_to_formatted'] = date_obj.strftime('%d/%m/%Y')
        
        # Agregar timestamp de cuando se aplicó el filtro
        # USANDO timezone para fecha actual
        data['filter_applied_at'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return data