"""mtaobao URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from miniTaobao import views
from django.conf import settings
from django.conf.urls.static import static
from apscheduler.scheduler import Scheduler

sched = Scheduler()


@sched.interval_schedule(seconds=30)
def runTask():
    views.banRemove()


sched.start()


urlpatterns = [
      path('admin/', admin.site.urls),
      path('', views.index),
      path('login.html/', views.login),
      path('index.html/', views.index),
      path('cart/', views.cart),
      path('cart', views.cart),
      path('search/<inp>', views.searchResults),
      path('order/<itemId>-<isCart>', views.order),
      path('bought_items.html/', views.bought_items),
      path('register.html/', views.register),
      path('my.html/', views.my),
      path('my_shop.html/', views.my_shop),
      path('shop_orders.html/', views.shop_orders),
      path('shop_items.html/', views.shop_items),
      path('edit_item/<itemId>', views.edit_item),
      path('add_item.html/', views.add_item),
      path('item/<item_id>', views.item),
      path('item', views.item),
      path('developer.html/', views.developer),
      path('add_money.html/', views.add_money),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL,
                                                                                         document_root
                                                                                         =settings.STATIC_ROOT)

handler404 = views.page_not_found
handler500 = views.server_error
