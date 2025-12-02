# urls.py de la APLICACIÓN (Ej: MainApp/urls.py)

from django.urls import path
from . import views # <-- ¡Esta importación es correcta aquí!
# No necesitas importar admin, settings, ni static aquí.

urlpatterns = [
    # Catálogo (Req. 7)
    path('', views.product_list, name='product_list'),
    
    # Detalle del Producto (Req. 8)
    path('producto/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Formulario de Solicitud (Req. 9)
    path('solicitar/', views.order_request, name='order_request'),
    
    # Seguimiento del Pedido (Req. 10)
    path("seguimiento/<str:token>/", views.order_track, name="order_track"),


    path("order/<uuid:order_id>/", views.order_detail, name="order_detail"),

]