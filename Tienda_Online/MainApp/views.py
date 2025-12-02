# MainApp/views.py (CÓDIGO CORREGIDO)

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Product, Category, Order, OrderImage
from .forms import OrderRequestForm
from django.contrib import messages

# --- VISTA 1: CATÁLOGO DE PRODUCTOS (Req. 7) ---

def product_list(request):
    products = Product.objects.all().order_by('-created')
    categories = Category.objects.all()
    
    # Filtrado por categoría
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # Buscador de productos
    query = request.GET.get('q')
    if query:
        # Búsqueda por nombre y descripción
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).distinct()

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': query,
    }
    # 🚨 CORRECCIÓN 1: De 'personal_shop/product_list.html' a 'MainApp/product_list.html'
    return render(request, 'MainApp/product_list.html', context)


# --- VISTA 2: DETALLE DEL PRODUCTO (Req. 8) ---

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    context = {
        'product': product,
    }
    # 🚨 CORRECCIÓN 2: De 'personal_shop/product_detail.html' a 'MainApp/product_detail.html'
    return render(request, 'MainApp/product_detail.html', context)


# --- VISTA 3: FORMULARIO DE SOLICITUD DE PEDIDO (Req. 9) ---

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
            
            if 'reference_images' in request.FILES:
                for file in request.FILES.getlist('reference_images'):
                    OrderImage.objects.create(order=new_order, image=file)
            
            tracking_url = request.build_absolute_uri(
                redirect('order_track', token=new_order.token).url
            )
            
            messages.success(request, f"¡Solicitud enviada! Usa esta URL para el seguimiento: {tracking_url}")
            
            return redirect('order_track', token=new_order.token)
        else:
            messages.error(request, "Error en el formulario. Por favor, revisa los datos.")
    else:
        initial_data = {}
        if initial_product:
            initial_data['product_ref'] = initial_product
        
        form = OrderRequestForm(initial=initial_data)

    context = {
        'form': form,
        'product_ref': initial_product,
    }
    # 🚨 CORRECCIÓN 3: De 'personal_shop/order_request_form.html' a 'MainApp/order_request_form.html'
    return render(request, 'MainApp/order_request_form.html', context)


# --- VISTA 4: SEGUIMIENTO DEL PEDIDO (Req. 10) ---

def order_track(request, token):
    order = get_object_or_404(Order, token=token)

    context = {
        'order': order,
    }
    return render(request, 'MainApp/order_tracking.html', context)


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "order_detail.html", {"order": order})

