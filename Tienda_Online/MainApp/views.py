from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Product, Category, Order, OrderImage
from .forms import OrderRequestForm
from django.contrib import messages

# --- VISTA 1: CATÁLOGO DE PRODUCTOS ---
def product_list(request):
    products = Product.objects.all().order_by('-created')
    categories = Category.objects.all()
    
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).distinct()

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': query,
    }
    return render(request, 'MainApp/product_list.html', context)

# --- VISTA 2: DETALLE DEL PRODUCTO ---
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    context = {'product': product}
    return render(request, 'MainApp/product_detail.html', context)

# --- VISTA 3: FORMULARIO DE SOLICITUD ---
def order_request(request, product_slug=None):
    initial_product = None
    if product_slug:
        initial_product = get_object_or_404(Product, slug=product_slug)
    
    if request.method == 'POST':
        form = OrderRequestForm(request.POST, request.FILES)
        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.platform = 'web'
            new_order.status = 'solicitado'
            new_order.payment_status = 'pendiente'
            new_order.save()

            for file in request.FILES.getlist('reference_images'):
                OrderImage.objects.create(order=new_order, image=file)

            messages.success(request, "¡Solicitud enviada correctamente!")
            return redirect('order_track', token=new_order.token)
        else:
            messages.error(request, "Error en el formulario. Por favor, revisa los datos.")
    else:
        initial_data = {}
        if initial_product:
            initial_data['product_ref'] = initial_product
        form = OrderRequestForm(initial=initial_data)

    return render(request, 'MainApp/order_request_form.html', {
        'form': form,
        'product_ref': initial_product,
    })

# --- VISTA 4: SEGUIMIENTO DEL PEDIDO ---
def order_track(request, token):
    order = get_object_or_404(Order, token=token)
    context = {'order': order}
    return render(request, 'MainApp/order_tracking.html', context)

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "order_detail.html", {"order": order})

# --- VISTA 5: DASHBOARD ADMINISTRATIVO (CORREGIDO timezone) ---
@login_required
def dashboard_reports(request):
    """Vista protegida para reportes del sistema - CORREGIDO timezone"""
    # Obtener parámetros de filtro
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status_filter = request.GET.get('status')
    platform_filter = request.GET.get('platform')
    
    # Filtrar órdenes
    orders = Order.objects.all()
    
    # Aplicar filtros básicos
    if status_filter:
        orders = orders.filter(status=status_filter)
    if platform_filter:
        orders = orders.filter(platform=platform_filter)
    
    # 1. Cantidad de pedidos por estado
    orders_by_status = orders.values('status').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # 2. Productos más solicitados
    popular_products = Order.objects.filter(product_ref__isnull=False).values(
        'product_ref__name'
    ).annotate(
        total_orders=Count('id')
    ).order_by('-total_orders')[:10]
    
    # 3. Pedidos por plataforma
    orders_by_platform = orders.values('platform').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # 4. Estadísticas mensuales CORREGIDO - con timezone.make_aware
    monthly_orders = []
    
    # Obtener los últimos 6 meses
    now = timezone.now()
    for i in range(5, -1, -1):  # Últimos 6 meses
        # Calcular inicio y fin del mes
        if now.month - i <= 0:
            year = now.year - 1
            month = now.month - i + 12
        else:
            year = now.year
            month = now.month - i
        
        # CORREGIDO: Usar make_aware para añadir zona horaria
        start_date = timezone.make_aware(datetime(year, month, 1))
        
        # Calcular el último día del mes
        if month == 12:
            end_date = timezone.make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)
        else:
            end_date = timezone.make_aware(datetime(year, month + 1, 1)) - timedelta(seconds=1)
        
        # Contar pedidos del mes
        month_count = Order.objects.filter(
            created__gte=start_date,
            created__lte=end_date
        ).count()
        
        monthly_orders.append({
            'month': f"{year}-{month:02d}",  # Formato YYYY-MM
            'total': month_count
        })
    
    # 5. Estadísticas generales
    total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0
    avg_order_value = total_revenue / orders.count() if orders.count() > 0 else 0
    
    # Preparar contexto
    context = {
        'orders_by_status': list(orders_by_status),
        'popular_products': list(popular_products),
        'orders_by_platform': list(orders_by_platform),
        'monthly_orders': monthly_orders,
        'total_orders': orders.count(),
        'total_revenue': total_revenue,
        'avg_order_value': round(avg_order_value, 2),
        'filter_params': {
            'date_from': date_from,
            'date_to': date_to,
            'status': status_filter,
            'platform': platform_filter,
        }
    }
    
    return render(request, 'MainApp/dashboard_reports.html', context)

# --- VISTA 6: API PARA GRÁFICOS (CORREGIDO timezone) ---
@login_required
def get_chart_data(request):
    """API para obtener datos de gráficos en formato JSON - CORREGIDO timezone"""
    chart_type = request.GET.get('type', 'status')
    
    if chart_type == 'status':
        data = Order.objects.values('status').annotate(total=Count('id')).order_by('-total')
        result = {
            'labels': [item['status'] for item in data],
            'data': [item['total'] for item in data]
        }
    
    elif chart_type == 'platform':
        data = Order.objects.values('platform').annotate(total=Count('id')).order_by('-total')
        result = {
            'labels': [item['platform'] for item in data],
            'data': [item['total'] for item in data]
        }
    
    elif chart_type == 'monthly':
        # CORREGIDO: con timezone.make_aware
        monthly_data = []
        now = timezone.now()
        
        for i in range(5, -1, -1):  # Últimos 6 meses
            if now.month - i <= 0:
                year = now.year - 1
                month = now.month - i + 12
            else:
                year = now.year
                month = now.month - i
            
            # CORREGIDO: Usar make_aware
            start_date = timezone.make_aware(datetime(year, month, 1))
            
            if month == 12:
                end_date = timezone.make_aware(datetime(year + 1, 1, 1)) - timedelta(seconds=1)
            else:
                end_date = timezone.make_aware(datetime(year, month + 1, 1)) - timedelta(seconds=1)
            
            month_count = Order.objects.filter(
                created__gte=start_date,
                created__lte=end_date
            ).count()
            
            monthly_data.append({
                'month': f"{year}-{month:02d}",
                'total': month_count
            })
        
        result = {
            'labels': [item['month'] for item in monthly_data],
            'data': [item['total'] for item in monthly_data]
        }
    
    else:
        result = {'error': 'Tipo de gráfico no válido'}
    
    return JsonResponse(result)
