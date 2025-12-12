# urls.py de la APLICACIÓN (Ej: MainApp/urls.py)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import *
from . import views

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'supplies', SupplyViewSet)
router.register(r'orders', OrderViewSet)

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

    # Dashboard protegido
    path('dashboard/', views.dashboard_reports, name='dashboard_reports'),

    # API para datos del gráfico
    path('api/chart-data/', views.get_chart_data, name='get_chart_data'),

    # APIs de CRUD (viewsets)
    path('api/', include(router.urls)),

    # APIs de filtrado y búsqueda
    path('api/filter-orders/', OrderFilterAPIView.as_view(), name='filter-orders'),
    path('api/search-products/', ProductSearchAPIView.as_view(), name='search-products'),

    # APIs de estadísticas
    path('api/statistics/', StatisticsAPIView.as_view(), name='statistics'),
    path('api/dashboard-stats/', DashboardStatsAPIView.as_view(), name='dashboard-stats'),
    path('api/product-inventory/', ProductInventoryAPIView.as_view(), name='product-inventory'),

    # API por rango de fechas
    path('api/orders/<int:year>/', OrderByDateRangeAPIView.as_view(), name='orders-by-year'),
    path('api/orders/<int:year>/<int:month>/', OrderByDateRangeAPIView.as_view(), name='orders-by-month'),
    path('api/orders/<int:year>/<int:month>/<int:day>/', OrderByDateRangeAPIView.as_view(), name='orders-by-day'),
]
