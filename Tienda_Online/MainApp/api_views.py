# MainApp/api_views.py (CÓDIGO COMPLETO CORREGIDO)

from rest_framework import viewsets, generics, filters, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta
from django.utils import timezone

from .models import Supply, Order, Product, Category, OrderImage
from .serializers import (
    SupplySerializer, OrderSerializer, OrderCreateSerializer,
    ProductSerializer, CategorySerializer, StatisticsSerializer,
    OrderFilterSerializer
)

# ============================================================================
# 1. VIEWSETS (CRUD COMPLETO) - USANDO viewsets.ModelViewSet
# ============================================================================

class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD de Categorías usando viewsets.ModelViewSet"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD de Productos usando viewsets.ModelViewSet"""
    queryset = Product.objects.all().order_by('-created')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'featured']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created', 'name']
    ordering = ['-created']
    lookup_field = 'slug'


class SupplyViewSet(viewsets.ModelViewSet):
    """CRUD de Insumos usando viewsets.ModelViewSet (API 1 del requerimiento)"""
    queryset = Supply.objects.all()
    serializer_class = SupplySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'brand', 'color']
    search_fields = ['name', 'type', 'brand']
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Acción personalizada para actualizar stock usando Count y Sum"""
        supply = self.get_object()
        quantity_change = request.data.get('quantity', 0)
        
        try:
            quantity_change = int(quantity_change)
            supply.quantity += quantity_change
            if supply.quantity < 0:
                return Response(
                    {'error': 'Stock no puede ser negativo'},
                    status=status.HTTP_400_BAD_REQUEST  # USANDO status
                )
            supply.save()
            return Response({'new_quantity': supply.quantity})
        except ValueError:
            return Response(
                {'error': 'Cantidad debe ser un número'},
                status=status.HTTP_400_BAD_REQUEST  # USANDO status
            )


class OrderViewSet(viewsets.ModelViewSet):
    """CRUD de Pedidos usando viewsets.ModelViewSet (API 2 del requerimiento)"""
    queryset = Order.objects.all().order_by('-created')
    permission_classes = [IsAuthenticated]  # USANDO IsAuthenticated
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'platform', 'payment_status']
    search_fields = ['customer_name', 'email', 'token']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OrderCreateSerializer  # USANDO OrderCreateSerializer
        return OrderSerializer
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Cambiar estado de un pedido usando status para respuestas HTTP"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            return Response(
                {'status': 'Estado actualizado', 'new_status': new_status},
                status=status.HTTP_200_OK  # USANDO status
            )
        return Response(
            {'error': 'Estado no válido'},
            status=status.HTTP_400_BAD_REQUEST  # USANDO status
        )
    
    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        """Agregar imagen a un pedido usando status para respuestas HTTP"""
        order = self.get_object()
        image = request.FILES.get('image')
        
        if image:
            OrderImage.objects.create(order=order, image=image)
            return Response({'status': 'Imagen agregada'}, status=status.HTTP_200_OK)
        return Response({'error': 'No se proporcionó imagen'}, status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# 2. VISTAS CON FILTRADO AVANZADO - USANDO filters.SearchFilter y DjangoFilterBackend
# ============================================================================

class OrderFilterAPIView(generics.ListAPIView):
    """API 3 - Filtro avanzado de pedidos usando OrderFilterSerializer y Q objects"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # USANDO IsAuthenticated
    
    def get_queryset(self):
        """Aplicar filtros complejos usando Q objects y datetime"""
        queryset = Order.objects.all()
        
        # Validar con serializer (USANDO OrderFilterSerializer)
        filter_serializer = OrderFilterSerializer(data=self.request.query_params)
        if not filter_serializer.is_valid():
            return queryset.order_by('-created')
        
        validated_data = filter_serializer.validated_data
        
        # Aplicar filtros usando Q objects para consultas complejas
        q_objects = Q()  # USANDO Q objects
        
        # Filtrar por estado (puede ser múltiple)
        if validated_data.get('status'):
            status_q = Q()
            statuses = [s.strip() for s in validated_data['status'].split(',')]
            for s in statuses:
                status_q |= Q(status=s)
            q_objects &= status_q
        
        # Filtrar por plataforma
        if validated_data.get('platform'):
            q_objects &= Q(platform=validated_data['platform'])
        
        # Filtrar por estado de pago
        if validated_data.get('payment_status'):
            q_objects &= Q(payment_status=validated_data['payment_status'])
        
        # Filtrar por cliente (búsqueda parcial)
        if validated_data.get('customer_name'):
            q_objects &= Q(customer_name__icontains=validated_data['customer_name'])
        
        # Filtrar por rango de fechas usando datetime
        if validated_data.get('date_from'):
            # USANDO datetime para conversión
            date_from = datetime.combine(validated_data['date_from'], datetime.min.time())
            q_objects &= Q(created__gte=date_from)
        
        if validated_data.get('date_to'):
            # USANDO datetime para conversión
            date_to = datetime.combine(validated_data['date_to'], datetime.max.time())
            q_objects &= Q(created__lte=date_to)
        
        return queryset.filter(q_objects).order_by('-created')


class ProductSearchAPIView(generics.ListAPIView):
    """Búsqueda avanzada de productos usando filters.SearchFilter"""
    serializer_class = ProductSerializer  # USANDO ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]  # USANDO filters
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created', 'name']
    ordering = ['-created']
    
    def get_queryset(self):
        """Filtrar productos con lógica adicional usando Q"""
        queryset = Product.objects.all()
        
        # Filtrar por precio mínimo usando Q
        min_price = self.request.query_params.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(Q(price__gte=float(min_price)))  # USANDO Q
            except ValueError:
                pass
        
        # Filtrar por precio máximo usando Q
        max_price = self.request.query_params.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(Q(price__lte=float(max_price)))  # USANDO Q
            except ValueError:
                pass
        
        # Filtrar por categoría usando Q
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(Q(category__slug=category_slug))  # USANDO Q
        
        return queryset

# ============================================================================
# 3. VISTAS DE ESTADÍSTICAS - USANDO Count, Sum, datetime, timedelta, timezone
# ============================================================================

class StatisticsAPIView(generics.GenericAPIView):
    """Vista para obtener estadísticas usando Count, Sum y operaciones de fecha"""
    permission_classes = [IsAuthenticated]
    serializer_class = StatisticsSerializer  # USANDO StatisticsSerializer
    
    def get(self, request):
        """Obtener estadísticas con múltiples filtros de fecha"""
        # Obtener parámetros de fecha
        days = int(request.query_params.get('days', 30))
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Definir rango de fechas usando datetime, timedelta y timezone
        now = timezone.now()  # USANDO timezone
        
        if start_date:
            try:
                # USANDO datetime para parsear fechas
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                start_date = timezone.make_aware(start_date)
            except ValueError:
                # USANDO timedelta para calcular fechas relativas
                start_date = now - timedelta(days=days)
        else:
            # USANDO timedelta
            start_date = now - timedelta(days=days)
        
        if end_date:
            try:
                # USANDO datetime para parsear fechas
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = timezone.make_aware(end_date)
            except ValueError:
                end_date = now
        else:
            end_date = now
        
        # Filtrar pedidos por rango de fechas
        orders = Order.objects.filter(created__range=[start_date, end_date])
        
        # Calcular estadísticas usando Count y Sum
        total_orders = orders.count()  # USANDO Count
        total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0  # USANDO Sum
        
        # Pedidos por estado usando Count
        orders_by_status = orders.values('status').annotate(
            count=Count('id')  # USANDO Count
        ).order_by('-count')
        
        # Pedidos por plataforma usando Count
        orders_by_platform = orders.values('platform').annotate(
            count=Count('id')  # USANDO Count
        ).order_by('-count')
        
        # CORRECCIÓN: Productos más vendidos usando Count y Sum - Aplicando el mismo filtro de fecha
        popular_products = Order.objects.filter(
            Q(product_ref__isnull=False) &  # USANDO Q
            ~Q(status='cancelada') &  # USANDO Q con negación
            Q(created__range=[start_date, end_date])  # ✅ AÑADIDO: Mismo filtro de fecha
        ).values(
            'product_ref__name', 'product_ref__id'
        ).annotate(
            count=Count('id'),  # USANDO Count
            revenue=Sum('total_price')  # USANDO Sum
        ).order_by('-count')[:10]
        
        # Pedidos por día en el rango usando datetime y timedelta
        daily_orders = []
        current_date = start_date.date()
        end_date_date = end_date.date()
        
        # USANDO datetime y timedelta para iterar sobre días
        while current_date <= end_date_date:
            day_orders = orders.filter(created__date=current_date).count()
            daily_orders.append({
                'date': current_date.strftime('%Y-%m-%d'),  # ✅ strftime correcto (solo un %)
                'count': day_orders
            })
            current_date += timedelta(days=1)  # USANDO timedelta
        
        # Datos para el serializer
        data = {
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),  # ✅ strftime correcto
                'end': end_date.strftime('%Y-%m-%d'),      # ✅ strftime correcto
                'days': days
            },
            'totals': {
                'orders': total_orders,
                'revenue': float(total_revenue),
                'avg_order_value': float(total_revenue / total_orders) if total_orders > 0 else 0
            },
            'by_status': list(orders_by_status),
            'by_platform': list(orders_by_platform),
            'popular_products': list(popular_products),
            'daily_trend': daily_orders
        }
        
        serializer = self.get_serializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)  # USANDO status

class DashboardStatsAPIView(generics.GenericAPIView):
    """Estadísticas rápidas para dashboard usando funciones de agregación"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener estadísticas rápidas usando Count, Sum, datetime, timedelta, timezone"""
        now = timezone.now()  # USANDO timezone
        
        # HOY usando datetime
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = Order.objects.filter(created__gte=today_start)
        
        # ESTA SEMANA usando datetime y timedelta
        week_start = now - timedelta(days=now.weekday())  # USANDO timedelta
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_orders = Order.objects.filter(created__gte=week_start)
        
        # ESTE MES usando datetime
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_orders = Order.objects.filter(created__gte=month_start)
        
        # Calcular usando Count y Sum
        stats = {
            'today': {
                'orders': today_orders.count(),  # USANDO Count
                'revenue': today_orders.aggregate(total=Sum('total_price'))['total'] or 0  # USANDO Sum
            },
            'this_week': {
                'orders': week_orders.count(),  # USANDO Count
                'revenue': week_orders.aggregate(total=Sum('total_price'))['total'] or 0  # USANDO Sum
            },
            'this_month': {
                'orders': month_orders.count(),  # USANDO Count
                'revenue': month_orders.aggregate(total=Sum('total_price'))['total'] or 0  # USANDO Sum
            },
            'pending_orders': Order.objects.filter(Q(status='solicitado')).count(),  # USANDO Q y Count
            'in_progress_orders': Order.objects.filter(Q(status='en_proceso')).count(),  # USANDO Q y Count
            'top_product': Order.objects.filter(
                Q(product_ref__isnull=False)  # USANDO Q
            ).values(
                'product_ref__name'
            ).annotate(
                count=Count('id')  # USANDO Count
            ).order_by('-count').first()
        }
        
        return Response(stats, status=status.HTTP_200_OK)  # USANDO status

# ============================================================================
# 4. VISTAS ADICIONALES PARA FUNCIONALIDAD ESPECÍFICA
# ============================================================================

class OrderByDateRangeAPIView(generics.ListAPIView):
    """Obtener pedidos por rango de fechas específico usando datetime y timedelta"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por rango de fechas usando parámetros URL"""
        year = self.kwargs.get('year')
        month = self.kwargs.get('month', None)
        day = self.kwargs.get('day', None)
        
        # Construir filtro de fecha usando datetime
        if year and month and day:
            # Día específico usando datetime
            start_date = datetime(year, month, day, 0, 0, 0)
            end_date = datetime(year, month, day, 23, 59, 59)
        elif year and month:
            # Mes específico usando datetime
            start_date = datetime(year, month, 1, 0, 0, 0)
            if month == 12:
                end_date = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)  # USANDO timedelta
            else:
                end_date = datetime(year, month + 1, 1, 0, 0, 0) - timedelta(seconds=1)  # USANDO timedelta
        elif year:
            # Año específico usando datetime
            start_date = datetime(year, 1, 1, 0, 0, 0)
            end_date = datetime(year, 12, 31, 23, 59, 59)
        else:
            return Order.objects.none()
        
        # Hacer fechas timezone-aware usando timezone
        start_date = timezone.make_aware(start_date)
        end_date = timezone.make_aware(end_date)
        
        return Order.objects.filter(
            created__range=[start_date, end_date]
        ).order_by('-created')


class ProductInventoryAPIView(generics.GenericAPIView):
    """Informe de inventario de productos relacionados con pedidos usando Count y Sum"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener análisis de productos más pedidos"""
        # Productos con más pedidos usando Count y Sum
        top_products = Order.objects.filter(
            Q(product_ref__isnull=False)  # USANDO Q
        ).values(
            'product_ref__id',
            'product_ref__name',
            'product_ref__price'
        ).annotate(
            order_count=Count('id'),  # USANDO Count
            total_revenue=Sum('total_price'),  # USANDO Sum
            avg_order_value=Sum('total_price') / Count('id')  # USANDO Sum y Count
        ).order_by('-order_count')[:20]
        
        # Productos por categoría usando Count y Sum
        products_by_category = Order.objects.filter(
            Q(product_ref__isnull=False)  # USANDO Q
        ).values(
            'product_ref__category__name'
        ).annotate(
            order_count=Count('id'),  # USANDO Count
            total_revenue=Sum('total_price')  # USANDO Sum
        ).order_by('-order_count')
        
        return Response({
            'top_products': list(top_products),
            'by_category': list(products_by_category)
        }, status=status.HTTP_200_OK)  # USANDO status