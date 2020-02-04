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
    
    # /prod/usr_list/1/ -> ProdUser List for Production #1
    path('usr_list/<int:prod_id>/', views.UsrList.as_view(), name='usr_list'),
    
    # /prod/usr_update/1/ -> ProdUser #1 Update
    path('usr_update/<int:pk>/', views.UsrUpdate.as_view(), name='usr_update'),
    
    # /prod/usr_delete/1/ -> ProdUser #1 Delete
    path('usr_delete/<int:pk>/', views.UsrDelete.as_view(), name='usr_delete'),

    # /prod/invt_create/1/ -> Invitation Create for Production #1
    path('invt_create/<int:prod_id>/', views.InvtCreate.as_view(), name='invt_create'),

    # /prod/invt_delete/1/{usr_list|prod_list}/ -> Invitation #1 Delete
    path('invt_delete/<int:pk>/<str:from>/', views.InvtDelete.as_view(), name='invt_delete'),

    # /prod/prod_join/1/ -> Join to Production via Invitation #1
    path('prod_join/<int:invt_id>/', views.ProdJoin.as_view(), name='prod_join'),
]
