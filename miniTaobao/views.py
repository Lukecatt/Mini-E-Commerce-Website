from django.shortcuts import render, redirect, HttpResponse
from miniTaobao.models import Buyer, Seller, Shop, Item, Order, CartOrder, BanIp
from decimal import Decimal
import random, time


# todo

# new upload image rename method
# delete cart items
# shop orders switch page

url = 'http://127.0.0.1:8000/'
# url = 'http://lucasjiang.net/'

VISIT_RECORD = {}


def banRemove():
    if BanIp.objects.all():
        for ip in BanIp.objects.all():
            if ip.time + 900 < time.time():
                ip.delete()


def throttle(request):
    ip = getIp(request)
    if ip not in VISIT_RECORD:
        VISIT_RECORD[ip] = [time.time()]
    else:
        ctime = time.time()
        VISIT_RECORD[ip].insert(0, ctime)
        if len(VISIT_RECORD[ip]) > 3:
            if VISIT_RECORD[ip][0] - VISIT_RECORD[ip][1] < 0.2 and VISIT_RECORD[ip][1] - VISIT_RECORD[ip][2] < 0.2 and \
                    VISIT_RECORD[ip][2] - VISIT_RECORD[ip][3] < 0.2:
                BanIp.objects.create(ip=ip, time=time.time())
            VISIT_RECORD[ip].pop()


def getIp(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        ip = request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']
    return ip


def ban_crawl(request):
    ip = getIp(request)
    agent = request.META.get('HTTP_USER_AGENT')
    if 'Mozilla' not in agent and 'Safari' not in agent and 'Chrome' not in agent:
        exist_ip = BanIp.objects.filter(ip=ip)
        if exist_ip:
            exist_ip[0].time = time.time()
            exist_ip[0].save()
        else:
            BanIp.objects.create(ip=ip, time=time.time())


def isBan(request):
    ip = getIp(request)
    if BanIp.objects.filter(ip=ip):
        return True
    return False


def check_request(request):
    ban_crawl(request)
    throttle(request)
    if isBan(request):
        return redirect('https://www.baidu.com')


def index(request):
    check_request(request)
    if request.method == "POST":
        search_input = request.POST.get("search_input")
        return redirect(url + "search/" + search_input)
    request.session.setdefault('is_login', False)
    request.session.setdefault('is_buyer', None)
    itemsRaw = list(Item.objects.filter(isSelling=True, stock__gt=0))
    items = []
    if len(itemsRaw) < 5:
        return render(request, 'index.html', {'items': itemsRaw})
    else:
        for i in range(5):
            item = random.choice(itemsRaw)
            items.append(item)
            itemsRaw.remove(item)
        return render(request, 'index.html', {'items': items})


def login(request):
    check_request(request)
    if request.method == 'GET':
        return render(request, 'login.html', {'url': url})
    username = request.POST.get('username')
    password = request.POST.get('password')

    if username.find('*') > 0 or username.find('=') > 0 or username.find('"') > 0 or username.find("'") > 0:
        return render(request, 'login.html',
                      {'status': 'Cannot contain {}{}{}{}'.format('=', '*', '"', "'"), 'url': url})
    if password.find('*') > 0 or password.find('=') > 0 or password.find('"') > 0 or password.find("'") > 0:
        return render(request, 'login.html',
                      {'status': 'Cannot contain {},{},{}, or {}'.format('=', '*', '"', "'"), 'url': url})
    if Buyer.objects.filter(username=username, password=password):
        request.session['is_login'] = True
        request.session['is_buyer'] = True
        request.session['id'] = Buyer.objects.get(username=username).id
        request.session['username'] = username
        return redirect(url)
    elif Seller.objects.filter(username=username, password=password):
        request.session['is_login'] = True
        request.session['is_buyer'] = False
        request.session['id'] = Seller.objects.get(username=username).id
        request.session['username'] = username
        if Shop.objects.filter(owner_id=request.session['id']):
            request.session['shop_id'] = Shop.objects.get(owner_id=request.session['id']).id
        return redirect(url)
    else:
        return render(request, 'login.html', {'status': 'Username or password is incorrect', 'url': url})


def register(request):
    check_request(request)
    if request.session['is_buyer']:
        return redirect(url)
    if request.method == 'GET':
        return render(request, 'register.html', {'url': url})
    username = request.POST.get('username')
    password = request.POST.get('password')
    confirm = request.POST.get('confirm')
    if username.find('*') > 0 or username.find('=') > 0 or username.find('"') > 0 or username.find("'") > 0:
        return render(request, 'register.html',
                      {'status': 'Cannot contain {}{}{}{}'.format('=', '*', '"', "'"), 'url': url})
    if password.find('*') > 0 or password.find('=') > 0 or password.find('"') > 0 or password.find("'") > 0:
        return render(request, 'register.html',
                      {'status': 'Cannot contain {},{},{}, or {}'.format('=', '*', '"', "'"), 'url': url})
    if len(username) > 40:
        return render(request, 'register.html', {'status': 'Username too long', 'url': url})
    if username == "":
        return render(request, 'register.html', {'status': 'Username cannot be empty', 'url': url})
    if len(password) > 40 or len(password) < 4:
        return render(request, 'register.html', {'status': 'Password is too long or short', 'url': url})
    if Buyer.objects.filter(username=username) or Seller.objects.filter(username=username):
        return render(request, 'register.html', {'status': 'Username already used', 'url': url})
    if password != confirm:
        return render(request, 'register.html', {'status': 'Passwords must be identical', 'url': url})
    if password == "" or confirm == "":
        return render(request, 'register.html', {'status': 'Password cannot be empty', 'url': url})
    if request.POST.get('type') == 'Buyer':
        request.session['is_buyer'] = True
        request.session['is_login'] = True
        Buyer.objects.create(username=username, password=password, ip=getIp(request))
        request.session['id'] = Buyer.objects.get(username=username).id
    else:
        request.session['is_buyer'] = False
        request.session['is_login'] = True
        Seller.objects.create(username=username, password=password, ip=getIp(request))
        request.session['id'] = Seller.objects.get(username=username).id
    return redirect(url)


def searchResults(request, inp):
    check_request(request)
    if request.method == 'POST':
        return redirect(url + 'search/' + request.POST.get('searchInput'))
    results = Item.objects.filter(nameLower__contains=inp.lower(), isSelling=True)
    if not results:
        return render(request, 'search_results.html', {'status': inp + ' was not found. Due to the lack of users, '
                                                                       'there is only a small number of items.'
            , 'url': url})
    else:
        return render(request, 'search_results.html', {'items': results, 'url': url})


def my(request):
    check_request(request)
    if not request.session['is_login']:
        return redirect(url + 'login.html/')
    if request.session['is_buyer']:
        user = Buyer.objects.get(id=request.session['id'])
    else:
        user = Seller.objects.get(id=request.session['id'])
    if request.method == 'POST':
        request.session.flush()
        return redirect(url)
    return render(request, 'my.html', {'money': user.money, 'url': url})


def my_shop(request):
    ban_crawl(request)
    throttle(request)
    if isBan(request):
        return redirect('https://www.baidu.com')
    if not request.session['is_login'] or request.session['is_buyer']:
        return redirect(url)
    if request.method == 'GET':
        if Shop.objects.filter(owner_id=request.session['id']):
            request.session['shop'] = True
            request.session['shop_name'] = Shop.objects.get(owner_id=request.session['id']).shop_name
        else:
            request.session['shop'] = False
            request.session['shop_name'] = 'Shop register'
        return render(request, 'my_shop.html', {'url': url})
    if not request.session['shop']:
        request.session['shop_name'] = request.POST.get('shop_name')
        if Shop.objects.filter(shop_name=request.session['shop_name']):
            return render(request, 'my_shop.html', {'status': 'Shop name already used', 'url': url})
        if len(request.session['shop_name']) > 20:
            return render(request, 'my_shop.html', {'status': 'Shop name too long', 'url': url})
        Shop.objects.create(owner_id=request.session['id'], shop_name=request.session['shop_name'])
        request.session['shop_id'] = Shop.objects.get(owner_id=request.session['id']).id
    return redirect(url + 'my_shop.html')


def shop_items(request):
    check_request(request)
    if request.session['is_buyer'] or not request.session['is_login']:
        return redirect(url)
    if request.method == 'GET':
        items = Item.objects.filter(shop_id=request.session['shop_id'])
        return render(request, 'shop_items.html', {'items': items, 'url': url})


def add_item(request):
    check_request(request)
    if not request.session['is_login'] or request.session['is_buyer']:
        return redirect(url)
    if request.method == 'GET':
        return render(request, 'add_item.html', {'url': url})
    name = request.POST.get('name')
    price = request.POST.get('price')
    picture = request.FILES['img']
    description = request.POST.get('description')
    stock = request.POST.get('stock')
    if len(str(stock)) > 10:
        return render(request, 'add_item.html', {'status': 'Stock exceeds max number of digits', 'url': url})
    if len(str(price)) > 10:
        return render(request, 'add_item.html', {'status': 'Price exceeds max number of digits', 'url': url})
    if len(name) > 40:
        return render(request, 'add_item.html', {'status': 'Name is too long', 'url': url})
    if len(str(description)) > 2000:
        return render(request, 'add_item.html', {'status': 'Description is too long'})
    Item.objects.create(name=name, nameLower=name.lower(), price=float(price), picture=picture, description=description,
                        shop=Shop.objects.get(id=request.session['shop_id']), stock=stock, isSelling=True)
    return redirect(url + 'shop_items.html')


def item(request, item_id):
    check_request(request)
    if not item_id:
        return render(request, 'item.html', {'description': 'This item has been removed by its owner.'})
    item = Item.objects.get(id=item_id)
    return render(request, 'item.html',
                  {"picture": item.picture, "name": item.name, "price": item.price, "shop": item.shop.shop_name,
                   "stock": item.stock, "description": item.description, "itemId": item.id,
                   'isSelling': item.isSelling
                      , 'url': url})


def order(request, itemId, isCart):
    check_request(request)
    if not request.session['is_login']:
        return redirect(url + 'login.html')
    item = Item.objects.get(id=itemId)
    owner = item.shop.owner
    if request.method == 'POST':
        if request.session['is_buyer']:
            user = Buyer.objects.get(id=request.session['id'])
        else:
            user = Seller.objects.get(id=request.session['id'])
        count = int(request.POST.get('count'))
        if count == 0:
            return render(request, 'order.html', {'url': url, 'item': item, 'status': 'Invalid quantity:0'})
        total = item.price * Decimal(count)
        if isCart == 'False':
            if user.money >= total:
                if user == owner:
                    item.stock = item.stock - count
                    item.save()
                    if request.session['is_buyer']:
                        Order.objects.create(item=item, isBuyer=request.session['is_buyer'],
                                             qty=count, price=total, buyerB=user, shop=item.shop)
                    else:
                        Order.objects.create(item=item, isBuyer=request.session['is_buyer'], qty=count, price=total,
                                             buyerS=user, shop=item.shop)
                else:
                    user.money = user.money - total
                    user.save()
                    item.stock = item.stock - count
                    item.save()
                    owner.money = owner.money + total
                    owner.save()
                    if request.session['is_buyer']:
                        Order.objects.create(item=item, isBuyer=request.session['is_buyer'],
                                             qty=count, price=total, buyerB=user, shop=item.shop)
                    else:
                        Order.objects.create(item=item, isBuyer=request.session['is_buyer'], qty=count, price=total
                                             , buyerS=user, shop=item.shop)
                return render(request, 'thankyou.html', {'url': url})
            else:
                return render(request, 'order.html',
                              {'status': 'You do not have enough money.', 'item': item, 'url': url})
        else:
            if request.session['is_buyer']:
                order_exist = CartOrder.objects.filter(buyerB=user, item=item)
                if not order_exist:
                    CartOrder.objects.create(item=item, isBuyer=True, buyerB=user, qty=count)
                else:
                    order_exist[0].qty += count
                    order_exist[0].save()
            else:
                order_exist = CartOrder.objects.filter(buyerS=user, item=item)
                if not order_exist:
                    CartOrder.objects.create(item=item, isBuyer=False, buyerS=user, qty=count)
                else:
                    order_exist[0].qty += count
                    order_exist[0].save()
            return redirect(url + 'item/' + str(itemId))
    return render(request, 'order.html', {"item": item, 'url': url})


def cart(request):
    check_request(request)
    if not request.session['is_login']:
        return redirect(url + 'login.html/')
    if request.method == 'GET':
        if request.session['is_buyer']:
            user = Buyer.objects.get(id=request.session['id'])
            orders = list(CartOrder.objects.filter(buyerB=user)[::-1])
        else:
            user = Seller.objects.get(id=request.session['id'])
            orders = list(CartOrder.objects.filter(buyerS=user)[::-1])
        for order in orders:
            if not order.item:
                orders.remove(order)
        return render(request, 'cart.html', {'orders': orders, 'url': url})
    elif request.method == 'POST':
        cartOrders = []
        if request.session['is_buyer']:
            user = Buyer.objects.get(id=request.session['id'])
        else:
            user = Seller.objects.get(id=request.session['id'])
        for i in request.POST.keys():
            print(request.POST)
            if 'qty' in i:
                if request.session['is_buyer']:
                    order_temp = CartOrder.objects.get(item=Item.objects.get(id=int(i.split('qty')[0])),
                                                       buyerB=user)
                else:
                    order_temp = CartOrder.objects.get(item=Item.objects.get(id=int(i.split('qty')[0])),
                                                       buyerS=user)
                    if order_temp.item.shop.owner == user:
                        return render(request, 'cart.html', {'orders': CartOrder.objects.filter(buyerS=user),
                                                             'url': url, 'status': 'You cannot buy your own items'})
                if request.POST[i] == 0:
                    return render(request, 'cart.html', {'orders': CartOrder.objects.filter(buyerB=user),
                                                         'url': url,
                                                         'status': 'Invalid quantity:0'})
                if int(request.POST[i]) > order_temp.item.stock:
                    if request.session['is_buyer']:
                        return render(request, 'cart.html', {'orders': CartOrder.objects.filter(buyerB=user),
                                                             'url': url,
                                                             'status': 'Stock insufficient for ' + order_temp.item.name})
                    else:
                        return render(request, 'cart.html',
                                      {'orders': CartOrder.objects.filter(buyerB=user), 'url': url,
                                       'status': 'Stock insufficient for ' + order_temp.item.name})
                order_temp.qty = int(request.POST[i])
                order_temp.save()
                if i.split('qty')[0] in request.POST:
                    cartOrders.append(order_temp)
            continue
        if not cartOrders:
            return redirect(url + 'cart')
        total = 0
        for i in cartOrders:
            money_temp = Decimal(i.qty) * i.item.price
            if i.item.shop.owner != user:
                total += money_temp
        if total > user.money:
            if request.session['is_buyer']:
                return render(request, 'cart.html',
                              {'orders': CartOrder.objects.filter(buyerB=user), 'url': url,
                               'status': 'Money is not enough'})
            else:
                return render(request, 'cart.html',
                              {'orders': CartOrder.objects.filter(buyerS=user), 'url': url,
                               'status': 'Money is not enough'})
        user.money -= total
        user.save()
        for i in cartOrders:
            if request.session['is_buyer']:
                Order.objects.create(item=i.item, isBuyer=True, qty=i.qty, price=Decimal(i.qty) * i.item.price,
                                     buyerB=user, shop=i.item.shop)
            else:
                Order.objects.create(item=i.item, isBuyer=False, qty=i.qty, price=Decimal(i.qty) * i.item.price,
                                     buyerS=user, shop=i.item.shop)
            i.item.stock -= int(i.qty)
            i.item.save()
            seller = Seller.objects.get(shop=i.item.shop)
            seller.money = seller.money + Decimal(i.qty) * i.item.price
            seller.save()
            i.delete()
        return render(request, 'thankyou.html', {'url': url})


def bought_items(request):
    check_request(request)
    if not request.session['is_login']:
        return redirect(url + 'login.html/')
    if request.session['is_buyer']:
        orders = list(Order.objects.filter(buyerB=request.session['id'], isBuyer=True)[::-1])
    else:
        orders = list(Order.objects.filter(buyerS=request.session['id'], isBuyer=False)[::-1])
    for order in orders:
        if not order.item:
            orders.remove(order)
    if not orders:
        return render(request, 'bought_items.html', {'url': url, 'status': 'Empty. Maybe buy some things?'})
    return render(request, 'bought_items.html', {'orders': orders, 'url': url})


def developer(request):
    check_request(request)
    return render(request, 'developer.html', {'url': url})


def shop_orders(request):
    check_request(request)
    if not request.session['is_login'] or request.session['is_buyer']:
        return redirect(url + 'login.html/')
    shop = Shop.objects.get(id=request.session['shop_id'])
    orders = Order.objects.filter(shop=shop)[::-1]
    for order in orders:
        if not order.item:
            orders.remove(order)
    if not orders:
        return render(request, 'shop_orders.html', {'status': 'There are no orders yet. :-(', 'url': url})
    return render(request, 'shop_orders.html', {'orders': orders, 'url': url})


def edit_item(request, itemId):
    check_request(request)
    if request.session['is_buyer'] or not request.session['is_login']:
        return redirect(url + 'login.html/')
    item = Item.objects.get(id=itemId)
    if request.method == 'GET':
        name = item.name
        price = item.price
        description = item.description
        stock = item.stock
        isSelling = item.isSelling
        locals().update({'url': url})
        return render(request, 'edit_item.html',
                      locals())
    if 'remove' in request.POST:
        item.isSelling = False
        item.save()
        return redirect(url + 'shop_items.html/')
    elif 'add' in request.POST:
        item.isSelling = True
        item.save()
        return redirect(url + 'shop_items.html/')
    else:
        item_name = request.POST.get('name')
        item_price = request.POST.get('price')
        item_stock = request.POST.get('stock')
        item_description = request.POST.get('description')
        if len(str(item_name)) > 40:
            status = 'Item name is too long'
            return render(request, 'edit_item.html', {locals()})
        if len(str(item_price)) > 10:
            status = 'Price exceeds max number of digits'
            return render(request, 'edit_item.html', {locals()})
        if len(str(item_stock)) > 10:
            status = 'Stock exceeds max number of digits'
            return render(request, 'edit_item.html', {locals()})
        if len(str(item_description)) > 2000:
            status = 'Description is too long'
            return render(request, 'edit_item.html', {locals()})
        item.name = item_name
        item.price = item_price
        item.stock = item_stock
        item.description = item.description
        item.save()
        if request.FILES.get('img'):
            item.picture = request.FILES['img']
        item.save()
        return redirect(url + 'shop_items.html/')


def add_money(request):
    check_request(request)
    if not request.session['is_login']:
        return redirect(url + 'login.html/')
    if request.session['is_buyer']:
        user = Buyer.objects.get(id=request.session['id'])
    else:
        user = Seller.objects.get(id=request.session['id'])
    if user.money > 100000000:
        return render(request, 'add_money.html', {'money': user.money, 'url': url, 'status': 'Maximum amount of money '
                                                                                             'reached'})
    if request.method == 'GET':
        return render(request, 'add_money.html', {'money': user.money, 'url': url})
    if request.method == 'POST':
        amount = int(request.POST.get('amount'))
        if amount > 100000:
            return render(request, 'add_money.html', {'money': user.money, 'url': url, 'status': 'You can only add '
                                                                                                 '100000 at most.'})
        user.money += Decimal(amount)
        user.save()
        return redirect(url + 'my.html/')


def page_not_found(request, exception):
    check_request(request)
    return render(request, '404.html')


def server_error(request):
    check_request(request)
    return render(request, '500.html')
