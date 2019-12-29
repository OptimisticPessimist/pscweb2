from django.urls import path
from . import views

app_name = 'script'
urlpatterns = [
    
    # /scrpt/ -> Script List
    path('', views.ScriptList.as_view(), name='scrpt_list'),
    
    # /scrpt/scrpt_detail/1/ -> Script #1 Detail
    path('scrpt_detail/<int:pk>/', views.ScriptDetail.as_view(),
        name='scrpt_detail'),
    
    # /scrpt/prod_from_scrpt/1/ -> Create Production from Script #1
    path('prod_from_scrpt/<int:scrpt_id>/', views.ProdFromScript.as_view(),
        name='prod_from_scrpt'),
]
