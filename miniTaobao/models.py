from django.db import models
import random


def image_upload_to(instance, filename):
    return 'upload/images/' + str(random.randint(1, 1000)) + "_" * random.randint(1, 5) + filename + str(
        random.randint(100, 999))


class Buyer(models.Model):
    username = models.CharField(max_length=40)
    password = models.CharField(max_length=40)
    id = models.AutoField(primary_key=True)
    money = models.DecimalField(default=1000, decimal_places=2, max_digits=63)
    time_registered = models.DateTimeField(auto_now_add=True, null=True)
    ip = models.CharField(max_length=30, default=None)

    def __str__(self):
        return self.username


class Seller(models.Model):
    username = models.CharField(max_length=40)
    password = models.CharField(max_length=40)
    id = models.AutoField(primary_key=True)
    money = models.DecimalField(default=1000, decimal_places=2, max_digits=63)
    time_registered = models.DateTimeField(auto_now_add=True, null=True)
    ip = models.CharField(max_length=30, default=None)

    def __str__(self):
        return self.username


class Shop(models.Model):
    owner = models.ForeignKey('Seller', on_delete=models.SET_NULL, null=True)
    shop_name = models.CharField(max_length=40, unique=True)
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return self.shop_name + '(owned by: {})'.format(self.owner)


class Item(models.Model):
    name = models.CharField(max_length=40)
    nameLower = models.CharField(max_length=40)
    picture = models.ImageField(upload_to=image_upload_to)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    description = models.TextField(null=True)
    shop = models.ForeignKey('Shop', on_delete=models.SET_NULL, null=True)
    stock = models.IntegerField()
    isSelling = models.BooleanField(null=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    item = models.ForeignKey('Item', on_delete=models.SET_NULL, null=True)
    qty = models.IntegerField()
    shop = models.ForeignKey('Shop', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(decimal_places=2, max_digits=63, null=True)
    isBuyer = models.NullBooleanField()
    buyerB = models.ForeignKey('Buyer', on_delete=models.SET_NULL, null=True)
    buyerS = models.ForeignKey('Seller', on_delete=models.SET_NULL, null=True)
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.item) + '  ' + str(self.time)


class CartOrder(models.Model):
    item = models.ForeignKey('Item', on_delete=models.SET_NULL, null=True)
    isBuyer = models.NullBooleanField()
    buyerB = models.ForeignKey('Buyer', on_delete=models.SET_NULL, null=True)
    buyerS = models.ForeignKey('Seller', on_delete=models.SET_NULL, null=True)
    time = models.DateTimeField(auto_now_add=True)
    qty = models.IntegerField(null=True)

    def __str__(self):
        return str(self.item) + '  ' + str(self.time)


class BanIp(models.Model):
    ip = models.CharField(max_length=30)
    time = models.FloatField()

    def __str__(self):
        return self.ip
