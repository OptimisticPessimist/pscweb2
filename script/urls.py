from django.urls import path
from . import views

app_name = 'script'
urlpatterns = [

    # /scrpt/ -> Script List
    path('', views.ScriptList.as_view(), name='scrpt_list'),

    # /scrpt/scrpt_create/ -> Script Create
    path('scrpt_create/', views.ScriptCreate.as_view(), name='scrpt_create'),
    # /scrpt/scrpt_update/1/ -> Script #1 Update
    path('scrpt_update/<int:pk>/', views.ScriptUpdate.as_view(),
         name='scrpt_update'),
    # /scrpt/scrpt_detail/1/ -> Script #1 Detail
    path('scrpt_detail/<int:pk>/', views.ScriptDetail.as_view(),
         name='scrpt_detail'),
    # /scrpt/scrpt_viewer/1/ -> Script #1 Viewer
    path('scrpt_viewer/<int:pk>/', views.ScriptViewer.as_view(),
         name='scrpt_viewer'),

    # /scrpt/prod_from_scrpt/1/ -> Create Production from Script #1
    path('prod_from_scrpt/<int:scrpt_id>/', views.ProdFromScript.as_view(),
         name='prod_from_scrpt'),
]