from django.urls import path
from . import views

app_name = 'myadmin'

protected = views.myadmin_login_required

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', protected(views.dashboard), name='dashboard'),
    path('products/', protected(views.products), name='products'),
    path('products/add/', protected(views.add_product), name='add_product'),
    path('products/edit/<int:product_id>/', protected(views.edit_product), name='edit_product'),
    path('products/update/<int:product_id>/', protected(views.update_product), name='update_product'),
    path('products/delete/<int:product_id>/', protected(views.delete_product), name='delete_product'),
    path('categories/', protected(views.categories), name='categories'),
    path('categories/add/', protected(views.add_category), name='add_category'),
    path('categories/edit/<int:category_id>/', protected(views.edit_category), name='edit_category'),
    path('categories/delete/<int:category_id>/', protected(views.delete_category), name='delete_category'),
    path('orders/', protected(views.orders), name='orders'),
    path('orders/update/<int:order_id>/', protected(views.update_order_status), name='update_order_status'),
    path('orders/view-receipt/<int:order_id>/', protected(views.view_receipt_page), name='view_receipt_page'),
    path('users/', protected(views.users), name='users'),
    path('users/edit/<int:user_id>/', protected(views.edit_user), name='edit_user'),
    path('users/delete/<int:user_id>/', protected(views.delete_user), name='delete_user'),
    path('contacts/', protected(views.contacts), name='contacts'),
    path('contacts/read/<int:contact_id>/', protected(views.mark_contact_read), name='mark_contact_read'),
    path('wishlists/', protected(views.wishlists), name='wishlists'),
    path('carts/', protected(views.carts), name='carts'),
    path('addresses/', protected(views.addresses), name='addresses'),
    path('settings/', protected(views.settings), name='settings'),
    path('farmers/', protected(views.farmers), name='farmers'),
    path('farmers/add/', protected(views.add_farmer), name='add_farmer'),
    path('farmers/edit/<int:farmer_id>/', protected(views.edit_farmer), name='edit_farmer'),
]


