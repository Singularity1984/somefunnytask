from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Sum, Avg, Count
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
import csv
from .models import *
from .forms import CheckoutForm, ConstructorForm, PhotoUploadForm, RegisterForm

def is_florist(user):
    return user.groups.filter(name='Флористы').exists() or user.is_superuser

def is_courier(user):
    return user.groups.filter(name='Курьеры').exists() or user.is_superuser

def catalog_view(request):
    bouquets = ReadyBouquet.objects.filter(is_active=True)
    
    search_query = request.GET.get('search', '')
    if search_query:
        bouquets = bouquets.filter(name__icontains=search_query)
    
    price_max = request.GET.get('price_max')
    if price_max:
        bouquets = bouquets.filter(price__lte=price_max)
        
    color_filter = request.GET.get('color', '')
    if color_filter:
        bouquets = bouquets.filter(recipe__variety__color__icontains=color_filter).distinct()

    in_stock = request.GET.get('in_stock')
    if in_stock == 'yes':
        bouquets = bouquets.filter(price__gt=0)
        
    sort_by = request.GET.get('sort', '-id')
    if sort_by in ['price', '-price', 'name', '-name', 'id', '-id']:
        bouquets = bouquets.order_by(sort_by)

    paginator = Paginator(bouquets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'price_max': price_max,
        'color_filter': color_filter,
        'in_stock': in_stock,
    }
    return render(request, 'catalog.html', context)

def constructor_view(request):
    varieties = FlowerVariety.objects.all()
    packagings = Packaging.objects.all()
    form = ConstructorForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            packaging = form.cleaned_data['packaging']
            card_text = form.cleaned_data['card_text']

            total_price = 0
            selected_items = []

            for key, value in request.POST.items():
                if key.startswith('variety_') and value.isdigit() and int(value) > 0:
                    variety_id = key.split('_')[1]
                    stems_count = int(value)
                    variety = FlowerVariety.objects.get(id=variety_id)
                    selected_items.append((variety, stems_count))
                    total_price += variety.sale_price * stems_count

            if not selected_items:
                messages.error(request, "Вы не выбрали ни одного цветка!")
                return render(request, 'constructor.html', {
                    'varieties': varieties,
                    'packagings': packagings,
                    'form': form,
                })

            custom_bouquet = CustomBouquet.objects.create(
                user=request.user if request.user.is_authenticated else None,
                packaging=packaging,
                card_text=card_text
            )

            for variety, stems_count in selected_items:
                CustomBouquetItem.objects.create(
                    custom_bouquet=custom_bouquet,
                    variety=variety,
                    stems_count=stems_count
                )

            if packaging:
                total_price += packaging.price

            custom_bouquet.total_price = total_price
            custom_bouquet.save()

            messages.success(request, "Букет добавлен в корзину.")
            return redirect('cart')

    return render(request, 'constructor.html', {
        'varieties': varieties,
        'packagings': packagings,
        'form': form,
    })

@login_required
def buy_ready_bouquet(request, bouquet_id):
    bouquet = get_object_or_404(ReadyBouquet, id=bouquet_id)
    cart = CustomBouquet.objects.filter(user=request.user, is_ordered=False).first()
    
    if not cart:
        cart = CustomBouquet.objects.create(user=request.user)
    
    for recipe_item in bouquet.recipe.all():
        item, created = CustomBouquetItem.objects.get_or_create(
            custom_bouquet=cart,
            variety=recipe_item.variety,
            defaults={'stems_count': recipe_item.stems_count}
        )
        if not created:
            item.stems_count += recipe_item.stems_count
            item.save()
            
    total = sum(item.variety.sale_price * item.stems_count for item in cart.items.all())
    cart.total_price = total
    cart.save()
    
    messages.success(request, f"Букет '{bouquet.name}' добавлен в корзину!")
    return redirect('cart')

@login_required
def cart_view(request):
    cart = CustomBouquet.objects.filter(user=request.user, is_ordered=False).first()
    if cart and cart.packaging:
        cart.total_price = sum(item.variety.sale_price * item.stems_count for item in cart.items.all()) + cart.packaging.price
        cart.save()
    return render(request, 'cart.html', {'cart': cart})

@transaction.atomic
@login_required
def checkout_view(request, bouquet_id):
    custom_bouquet = get_object_or_404(CustomBouquet, id=bouquet_id, user=request.user)
    slots = DeliverySlot.objects.all()
    form = CheckoutForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        address = form.cleaned_data['address']
        slot = form.cleaned_data.get('slot')

        if not slot:
            messages.error(request, "Выберите интервал доставки.")
            return render(request, 'checkout.html', {'bouquet': custom_bouquet, 'slots': slots, 'form': form})

        order = Order.objects.create(
            user=request.user,
            status='reserved',
            delivery_slot=slot,
            address=address,
            phone=form.cleaned_data['phone'],
            total_amount=custom_bouquet.total_price
        )
        
        OrderItem.objects.create(
            order=order,
            custom_bouquet=custom_bouquet,
            quantity=1,
            unit_price=custom_bouquet.total_price
        )

        for item in custom_bouquet.items.all():
            need_stems = item.stems_count
            variety = item.variety
            
            batches = SupplyBatch.objects.select_for_update().filter(
                variety=variety, quantity_remaining__gt=0
            ).order_by('cut_date')
            
            for batch in batches:
                if need_stems <= 0: break
                take_amount = min(batch.quantity_remaining, need_stems)
                batch.quantity_remaining -= take_amount
                batch.save()
                need_stems -= take_amount
                StockAllocation.objects.create(order=order, batch=batch, stems_count=take_amount, unit_cost=batch.purchase_price)
            
            if need_stems > 0:
                messages.error(request, f"Извините, на складе не хватает {variety.name}!")
                raise ValueError(f"Не хватает остатков для {variety.name}") 
        
        order.status = 'assembly'
        order.save()
        
        custom_bouquet.is_ordered = True
        custom_bouquet.save()

        send_mail(
            subject=f'Заказ #{order.id} оформлен',
            message=f'Сумма: {order.total_amount} руб.',
            from_email='noreply@flowershop.ru',
            recipient_list=['client@example.com'],
            fail_silently=False,
        )

        messages.success(request, "Заказ оформлен, флорист приступил к сборке.")
        return redirect('order_success', order_id=order.id)

    return render(request, 'checkout.html', {'bouquet': custom_bouquet, 'slots': slots, 'form': form})

def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'success.html', {'order': order})

@login_required
def profile_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'profile.html', {'orders': orders})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status in ['new', 'assembly']:
        order.status = 'cancelled'
        order.save()
        messages.success(request, "Заказ отменен.")
    return redirect('profile')

@login_required
def approve_photo(request, photo_id):
    photo = get_object_or_404(BouquetPhoto, id=photo_id, order__user=request.user)
    if request.method == 'POST':
        photo.is_approved = True
        photo.save()
        order = photo.order
        order.status = 'approved'
        order.save()
        messages.success(request, "Фото одобрено! Заказ передан курьеру.")
    return redirect('profile')

@login_required
def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    response.write('\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID', 'Клиент', 'Сумма', 'Статус', 'Дата'])
    orders = Order.objects.filter(user=request.user)
    for order in orders:
        writer.writerow([order.id, order.user.username, order.total_amount, order.get_status_display(), order.created_at.strftime("%d.%m.%Y")])
    return response

@user_passes_test(is_florist, login_url='login')
def florist_dashboard(request):
    orders = Order.objects.filter(status__in=['assembly', 'on_approval']).order_by('id')
    return render(request, 'florist.html', {'orders': orders})

@user_passes_test(is_florist, login_url='login')
def upload_photo(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            BouquetPhoto.objects.create(order=order, image=form.cleaned_data['photo'])
            order.status = 'on_approval'
            order.save()
            messages.success(request, "Фото загружено!")
        else:
            messages.error(request, "Не удалось загрузить фото, проверьте файл.")
    return redirect('florist_dashboard')

@user_passes_test(is_courier, login_url='login')
def courier_dashboard(request):
    orders = Order.objects.filter(status='approved').order_by('created_at')
    return render(request, 'courier.html', {'orders': orders})

@user_passes_test(is_courier, login_url='login')
def mark_delivered(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST' and order.status == 'approved':
        order.status = 'delivered'
        order.save()
        messages.success(request, f"Заказ #{order.id} доставлен!")
    return redirect('courier_dashboard')

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def analytics_dashboard(request):
    return render(request, 'analytics.html')

def dashboard_api(request):
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    avg_check = Order.objects.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
    custom_orders = Order.objects.filter(items__custom_bouquet__isnull=False).count()
    share = (custom_orders / total_orders * 100) if total_orders > 0 else 0
    status_counts = Order.objects.values('status').annotate(count=Count('id'))
    
    return JsonResponse({
        'total_orders': total_orders,
        'total_revenue': float(total_revenue),
        'avg_check': round(float(avg_check), 2),
        'custom_share': round(share, 1),
        'chart_labels': [item['status'] for item in status_counts],
        'chart_data': [item['count'] for item in status_counts]
    })

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно! Добро пожаловать.")
            return redirect('catalog')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('catalog')

def update_cart_total(cart):
    if cart:
        total = sum(item.variety.sale_price * item.stems_count for item in cart.items.all())
        if cart.packaging:
            total += cart.packaging.price
        cart.total_price = total
        cart.save()

def item_json(cart, item_id, count, removed=False):
    if cart:
        total = cart.total_price if cart.total_price else 0
        return JsonResponse({
            'ok': True,
            'item': item_id,
            'count': count,
            'removed': removed,
            'total': str(total),
        })
    return JsonResponse({'ok': False})

@login_required
def increase_item(request, item_id):
    item = get_object_or_404(CustomBouquetItem, id=item_id, custom_bouquet__user=request.user)
    item.stems_count += 1
    item.save()
    update_cart_total(item.custom_bouquet)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return item_json(item.custom_bouquet, item.id, item.stems_count)
    return redirect('cart')

@login_required
def decrease_item(request, item_id):
    item = get_object_or_404(CustomBouquetItem, id=item_id, custom_bouquet__user=request.user)
    if item.stems_count > 1:
        item.stems_count -= 1
        item.save()
        update_cart_total(item.custom_bouquet)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return item_json(item.custom_bouquet, item.id, item.stems_count)
    else:
        cart = item.custom_bouquet
        item.delete()
        update_cart_total(cart)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return item_json(cart, item_id, 0, True)
    return redirect('cart')

@login_required
def remove_item(request, item_id):
    item = get_object_or_404(CustomBouquetItem, id=item_id, custom_bouquet__user=request.user)
    cart = item.custom_bouquet
    item.delete()
    update_cart_total(cart)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return item_json(cart, item_id, 0, True)
    return redirect('cart')

def search_api(request):
    text = request.GET.get('q', '')
    bouquets = ReadyBouquet.objects.filter(is_active=True)

    if text:
        bouquets = bouquets.filter(name__icontains=text)

    bouquets = bouquets.order_by('-id')[:20]

    data = []
    for bouquet in bouquets:
        data.append({
            'id': bouquet.id,
            'name': bouquet.name,
            'price': str(bouquet.price),
            'photo': bouquet.photo.url if bouquet.photo else '',
        })

    return JsonResponse({'bouquets': data})

def bouquet_detail(request, bouquet_id):
    bouquet = get_object_or_404(ReadyBouquet, id=bouquet_id, is_active=True)
    return render(request, 'bouquet_detail.html', {'bouquet': bouquet})

def search_page(request):
    text = request.GET.get('q', '')
    bouquets = ReadyBouquet.objects.filter(is_active=True)

    if text:
        bouquets = bouquets.filter(name__icontains=text)

    paginator = Paginator(bouquets, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'search.html', {'page_obj': page_obj, 'query': text})

def about_page(request):
    return render(request, 'about.html')

def contacts_page(request):
    return render(request, 'contacts.html')