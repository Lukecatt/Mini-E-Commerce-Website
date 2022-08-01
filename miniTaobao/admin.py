from django.contrib import admin
from miniTaobao import models
# Register your models here.

admin.site.register(models.Buyer)
admin.site.register(models.Seller)
admin.site.register(models.Shop)
admin.site.register(models.Item)
admin.site.register(models.Order)
admin.site.register(models.CartOrder)
admin.site.register(models.BanIp)
