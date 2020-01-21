from django.urls import path
from . import views

app_name = 'production'
urlpatterns = [
    
    # /prod/ -> Production List
    path('', views.ProdList.as_view(), name='prod_list'),
    
    # /prod/prod_create/ -> Production Create
    path('prod_create/', views.ProdCreate.as_view(), name='prod_create'),
    
    # /prod/prod_update/1/ -> Production #1 Update
    path('prod_update/<int:pk>/', views.ProdUpdate.as_view(), name='prod_update'),
    
    # /prod/prod_delete/1/ -> Production #1 Delete
    path('prod_delete/<int:pk>/', views.ProdDelete.as_view(), name='prod_delete'),
]
