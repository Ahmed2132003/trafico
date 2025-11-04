from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from decimal import Decimal
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.utils.translation import activate
from django.db.models import F
from smtplib import SMTPRecipientsRefused, SMTPException

from .models import (
    Product, Favorite, CartItem, Order, OrderItem,
    Governorate, ProductColor, ProductSize, Design
)
from decimal import Decimal, InvalidOperation

def product_list(request):
    products = Product.objects.all()
    favorites = Favorite.objects.filter(user=request.user).values_list('product_id', flat=True) if request.user.is_authenticated else []
    products_with_price = []
    for product in products:
        display_price = product.base_price
        if product.design_ownership == 'designer' and product.design and product.design.status == 'approved':
            display_price += product.design.commission_per_sale
        products_with_price.append({
            'product': product,
            'display_price': display_price
        })
    return render(request, 'products/product_list.html', {
        'products_with_price': products_with_price,
        'favorites': favorites,
        'user': request.user
    })

def check_superuser(user):
    return user.is_authenticated and user.is_superuser

def check_marketer_or_designer(user):
    return user.is_authenticated and user.user_type in ['marketer', 'designer']

@login_required
@user_passes_test(check_superuser, login_url='/users/login/')
def product_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        base_price = request.POST.get('base_price')
        image = request.POST.get('image', '')
        images = request.POST.get('images', '')
        stock = request.POST.get('stock')
        colors = request.POST.get('colors', '')
        sizes = request.POST.get('sizes', '')
        color_stocks = request.POST.get('color_stocks', '')
        size_stocks = request.POST.get('size_stocks', '')
        design_ownership = request.POST.get('design_ownership')
        design_id = request.POST.get('design_id')

        try:
            # التحقق من تسجيل الدخول
            if not request.user.is_authenticated:
                messages.error(request, _("يجب تسجيل الدخول لإضافة منتج"))
                return redirect('users:login')

            # التحقق من الحقول المطلوبة
            if not name or name.strip() == '':
                messages.error(request, _("يرجى إدخال اسم المنتج"))
                return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})

            # تحقق من السعر الأساسي
            if not base_price or base_price.strip() == '':
                messages.error(request, _("يرجى إدخال سعر أساسي صالح"))
                return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
            try:
                base_price = Decimal(base_price)
                if base_price <= 0:
                    messages.error(request, _("السعر الأساسي يجب أن يكون أكبر من صفر"))
                    return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
            except (ValueError, TypeError):
                messages.error(request, _("يرجى إدخال سعر أساسي صالح"))
                return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})

            # تحقق من المخزون
            if not stock or stock.strip() == '':
                messages.error(request, _("يرجى إدخال مخزون صالح"))
                return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
            try:
                stock = int(stock)
                if stock < 0:
                    messages.error(request, _("المخزون لا يمكن أن يكون سالبًا"))
                    return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
            except (ValueError, TypeError):
                messages.error(request, _("يرجى إدخال قيمة مخزون صالحة"))
                return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})

            # التحقق من الصور
            image_list = [img.strip() for img in images.split(',') if img.strip()] if images else []
            total_images = len(image_list) + 1 if image else len(image_list)
            if total_images < 1:
                messages.error(request, _("يجب إضافة صورة واحدة على الأقل (الرئيسية أو إضافية)"))
                return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
            if len(image_list) > 10:
                messages.error(request, _("لا يمكن إضافة أكثر من 10 صور إضافية"))
                return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})

            # تحقق من الألوان والمقاسات
            total_color_stock = 0
            total_size_stock = 0
            color_list = []
            size_list = []
            color_stock_list = []
            size_stock_list = []

            if colors and color_stocks:
                color_list = [color.strip() for color in colors.split(',') if color.strip()]
                color_stock_list = [stock.strip() for stock in color_stocks.split(',') if stock.strip()]
                if len(color_list) != len(color_stock_list):
                    messages.error(request, _("عدد الألوان لا يتطابق مع عدد المخزونات"))
                    return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
                for stock in color_stock_list:
                    try:
                        stock_value = int(stock)
                        if stock_value < 0:
                            messages.error(request, _("مخزون الألوان لا يمكن أن يكون سالبًا"))
                            return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
                        total_color_stock += stock_value
                    except (ValueError, TypeError):
                        messages.error(request, _("يرجى إدخال قيم مخزون ألوان صالحة"))
                        return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})

            if sizes and size_stocks:
                size_list = [size.strip() for size in sizes.split(',') if size.strip()]
                size_stock_list = [stock.strip() for stock in size_stocks.split(',') if stock.strip()]
                if len(size_list) != len(size_stock_list):
                    messages.error(request, _("عدد المقاسات لا يتطابق مع عدد المخزونات"))
                    return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
                for stock in size_stock_list:
                    try:
                        stock_value = int(stock)
                        if stock_value < 0:
                            messages.error(request, _("مخزون المقاسات لا يمكن أن يكون سالبًا"))
                            return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
                        total_size_stock += stock_value
                    except (ValueError, TypeError):
                        messages.error(request, _("يرجى إدخال قيم مخزون مقاسات صالحة"))
                        return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})

            # تحقق من تطابق المخزون
            if total_color_stock > stock:
                messages.error(request, _("مجموع مخزون الألوان أكبر من المخزون الكلي"))
                return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
            if total_size_stock > stock:
                messages.error(request, _("مجموع مخزون المقاسات أكبر من المخزون الكلي"))
                return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})

            # تحقق من ملكية التصميم
            if not design_ownership:
                messages.error(request, _("يرجى اختيار ملكية التصميم"))
                return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})

            # تحقق من التصميم
            design = None
            designer = None
            if design_ownership == 'designer':
                if not design_id:
                    messages.error(request, _("يرجى اختيار تصميم صالح"))
                    return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
                try:
                    design = Design.objects.get(id=design_id, status='approved')
                    designer = design.designer
                except Design.DoesNotExist:
                    messages.error(request, _("التصميم المحدد غير موجود أو غير معتمد"))
                    return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})

            # إنشاء المنتج
            product = Product.objects.create(
                name=name,
                description=description,
                base_price=base_price,
                image=image,
                images=image_list,
                stock=stock,
                design_ownership=design_ownership,
                design=design,
                designer=designer
            )

            # إضافة الألوان
            if color_list and color_stock_list:
                for color, stock in zip(color_list, color_stock_list):
                    ProductColor.objects.create(
                        product=product,
                        color=color,
                        stock=int(stock)
                    )

            # إضافة المقاسات
            if size_list and size_stock_list:
                for size, stock in zip(size_list, size_stock_list):
                    ProductSize.objects.create(
                        product=product,
                        size=size,
                        stock=int(stock)
                    )

            messages.success(request, _("تم إضافة المنتج بنجاح"))
            return redirect('products:product_list')

        except (ValueError, TypeError) as e:
            messages.error(request, str(e) if str(e).startswith("عمولة") else _("يرجى إدخال قيم صالحة"))
            return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})
        except Design.DoesNotExist:
            messages.error(request, _("التصميم المحدد غير موجود"))
            return render(request, 'products/product_add.html', {'designs': Design.objects.filter(status='approved')})

    designs = Design.objects.filter(status='approved')
    return render(request, 'products/product_add.html', {'designs': designs})

@login_required
@user_passes_test(check_superuser, login_url='/users/login/')
def product_edit(request, pk):
    product = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        base_price = request.POST.get('base_price')
        image = request.POST.get('image', '')
        images = request.POST.get('images', '')
        stock = request.POST.get('stock')
        colors = request.POST.get('colors')
        sizes = request.POST.get('sizes')
        color_stocks = request.POST.get('color_stocks')
        size_stocks = request.POST.get('size_stocks')
        design_ownership = request.POST.get('design_ownership')
        design_id = request.POST.get('design_id')

        try:
            stock = int(stock)
            image_list = [img.strip() for img in images.split(',') if img.strip()] if images else []
            if len(image_list) < 1:
                messages.error(request, _("يجب إضافة صورة واحدة على الأقل"))
                return render(request, 'products/product_edit.html', {'product': product})
            if len(image_list) > 10:
                messages.error(request, _("لا يمكن إضافة أكثر من 10 صور"))
                return render(request, 'products/product_edit.html', {'product': product})

            total_color_stock = 0
            total_size_stock = 0

            if colors and color_stocks:
                color_list = colors.split(',')
                stock_list = color_stocks.split(',')
                if len(color_list) != len(stock_list):
                    messages.error(request, _("عدد الألوان لا يتطابق مع عدد المخزونات"))
                    return render(request, 'products/product_edit.html', {'product': product})
                for stock in stock_list:
                    if stock.strip():
                        total_color_stock += int(stock.strip())

            if sizes and size_stocks:
                size_list = sizes.split(',')
                stock_list = size_stocks.split(',')
                if len(size_list) != len(stock_list):
                    messages.error(request, _("عدد المقاسات لا يتطابق مع عدد المخزونات"))
                    return render(request, 'products/product_edit.html', {'product': product})
                for stock in stock_list:
                    if stock.strip():
                        total_size_stock += int(stock.strip())

            if total_color_stock > stock:
                messages.error(request, _("مجموع مخزون الألوان أكبر من المخزون الكلي"))
                return render(request, 'products/product_edit.html', {'product': product})
            if total_size_stock > stock:
                messages.error(request, _("مجموع مخزون المقاسات أكبر من المخزون الكلي"))
                return render(request, 'products/product_edit.html', {'product': product})

            product.name = name
            product.description = description
            product.base_price = Decimal(base_price)
            product.image = image
            product.images = image_list
            product.stock = int(stock)
            product.design_ownership = design_ownership
            product.design = Design.objects.get(id=design_id) if design_ownership == 'designer' and design_id else None
            product.designer = Design.objects.get(id=design_id).designer if design_ownership == 'designer' and design_id else None
            product.save()
            product.colors.all().delete()
            product.sizes.all().delete()
            if colors and color_stocks:
                color_list = colors.split(',')
                stock_list = color_stocks.split(',')
                for color, stock in zip(color_list, stock_list):
                    if color.strip() and stock.strip():
                        ProductColor.objects.create(
                            product=product,
                            color=color.strip(),
                            stock=int(stock.strip())
                        )
            if sizes and size_stocks:
                size_list = sizes.split(',')
                stock_list = size_stocks.split(',')
                for size, stock in zip(size_list, stock_list):
                    if size.strip() and stock.strip():
                        ProductSize.objects.create(
                            product=product,
                            size=size.strip(),
                            stock=int(stock.strip())
                        )
            messages.success(request, _("تم تعديل المنتج بنجاح"))
            return redirect('products:product_list')
        except ValueError as e:
            messages.error(request, str(e) if str(e).startswith("عمولة") else _("يرجى إدخال قيم صالحة"))
        except Design.DoesNotExist:
            messages.error(request, _("التصميم المحدد غير موجود"))

    designs = Design.objects.filter(status='approved')
    return render(request, 'products/product_edit.html', {
        'product': product,
        'designs': designs,
        'images_json': json.dumps(product.images)  # تمرير الصور كـ JSON للنموذج
    })

@login_required
@user_passes_test(check_superuser, login_url='/users/login/')
def product_delete(request, pk):
    product = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, _("تم حذف المنتج بنجاح"))
        return redirect('products:product_list')
    return render(request, 'products/product_delete.html', {'product': product})

@login_required
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, _("تم إضافة المنتج للمفضلة"))
    else:
        favorite.delete()
        messages.info(request, _("تم إزالة المنتج من المفضلة"))
    return redirect('products:product_list')

@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'products/favorite_list.html', {'favorites': favorites})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        color = request.POST.get('color')
        size = request.POST.get('size')
        marketer_commission = Decimal(request.POST.get('marketer_commission', '0.00')) if request.user.is_authenticated and request.user.user_type == 'marketer' else Decimal('0.00')

        if not color:
            messages.error(request, _("يرجى اختيار لون"))
            return redirect('products:product_detail', product_id=product.id)
        if not size:
            messages.error(request, _("يرجى اختيار مقاس"))
            return redirect('products:product_detail', product_id=product.id)

        if quantity <= 0 or quantity > product.stock:
            messages.error(request, _(f"الكمية المطلوبة ({quantity}) غير متوفرة في المخزون الكلي"))
            return redirect('products:product_detail', product_id=product.id)

        try:
            product_color = ProductColor.objects.get(product=product, color=color)
            if quantity > product_color.stock:
                messages.error(request, _(f"الكمية المطلوبة ({quantity}) غير متوفرة لهذا اللون ({color})"))
                return redirect('products:product_detail', product_id=product.id)
        except ProductColor.DoesNotExist:
            messages.error(request, _(f"اللون المختار ({color}) غير متاح"))
            return redirect('products:product_detail', product_id=product.id)

        try:
            product_size = ProductSize.objects.get(product=product, size=size)
            if quantity > product_size.stock:
                messages.error(request, _(f"الكمية المطلوبة ({quantity}) غير متوفرة لهذا المقاس ({size})"))
                return redirect('products:product_detail', product_id=product.id)
        except ProductSize.DoesNotExist:
            messages.error(request, _(f"المقاس المختار ({size}) غير متاح"))
            return redirect('products:product_detail', product_id=product.id)

        with transaction.atomic():
            if request.user.is_authenticated:
                cart_item, created = CartItem.objects.get_or_create(
                    user=request.user,
                    product=product,
                    color=color,
                    size=size,
                    defaults={'quantity': quantity, 'marketer_commission': marketer_commission}
                )
                if not created:
                    new_quantity = cart_item.quantity + quantity
                    if new_quantity > product.stock:
                        messages.error(request, _(f"الكمية المطلوبة ({new_quantity}) غير متوفرة في المخزون الكلي"))
                        return redirect('products:product_detail', product_id=product.id)
                    if new_quantity > product_color.stock:
                        messages.error(request, _(f"الكمية المطلوبة ({new_quantity}) غير متوفرة لهذا اللون ({color})"))
                        return redirect('products:product_detail', product_id=product.id)
                    if new_quantity > product_size.stock:
                        messages.error(request, _(f"الكمية المطلوبة ({new_quantity}) غير متوفرة لهذا المقاس ({size})"))
                        return redirect('products:product_detail', product_id=product.id)
                    cart_item.quantity = new_quantity

                cart_item.marketer_commission = marketer_commission
                if request.user.user_type == 'marketer':
                    cart_item.marketer = request.user
                cart_item.save()
            else:
                # للزوار: استخدام الـ session لتخزين السلة
                cart = request.session.get('cart', {})
                cart_key = f"{product_id}_{color}_{size}"
                if cart_key in cart:
                    new_quantity = cart[cart_key]['quantity'] + quantity
                    if new_quantity > product.stock:
                        messages.error(request, _(f"الكمية المطلوبة ({new_quantity}) غير متوفرة في المخزون الكلي"))
                        return redirect('products:product_detail', product_id=product.id)
                    if new_quantity > product_color.stock:
                        messages.error(request, _(f"الكمية المطلوبة ({new_quantity}) غير متوفرة لهذا اللون ({color})"))
                        return redirect('products:product_detail', product_id=product.id)
                    if new_quantity > product_size.stock:
                        messages.error(request, _(f"الكمية المطلوبة ({new_quantity}) غير متوفرة لهذا المقاس ({size})"))
                        return redirect('products:product_detail', product_id=product.id)
                    cart[cart_key]['quantity'] = new_quantity
                else:
                    cart[cart_key] = {
                        'product_id': product_id,
                        'quantity': quantity,
                        'color': color,
                        'size': size,
                        'marketer_commission': str(marketer_commission)
                    }
                request.session['cart'] = cart
                request.session.modified = True
        
        messages.success(request, _("تم إضافة المنتج إلى العربة"))
        return redirect('products:cart')

    # تمرير الألوان والمقاسات إلى القالب
    colors = product.colors.all()
    sizes = product.sizes.all()
    return render(request, 'products/add_to_cart.html', {
        'product': product,
        'colors': colors,
        'sizes': sizes
    })

def cart_view(request):
    cart_items = []
    total_cart_price = Decimal('0.00')
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user).select_related('product', 'product__design')
        total_cart_price = sum(
            (item.product.base_price + item.marketer_commission + (
                item.product.design.commission_per_sale
                if item.product.design_ownership == 'designer' and item.product.design and item.product.design.status == 'approved'
                else 0
            )) * item.quantity
            for item in cart_items
        )
        
        # تحويل cart_items إلى JSON
        cart_items_json = [
            {
                'price': float(item.product.base_price) if item.product and item.product.base_price else 0.0,
                'quantity': item.quantity if item.quantity else 1,
                'commission': float(item.marketer_commission) if item.marketer_commission else 0.0,
                'designer_commission': (
                    float(item.product.design.commission_per_sale)
                    if item.product.design_ownership == 'designer' and item.product.design and item.product.design.status == 'approved' and item.product.design.commission_per_sale
                    else 0.0
                )
            }
            for item in cart_items
            if item.product and item.quantity
        ]
    else:
        cart = request.session.get('cart', {})
        cart_items_json = []
        for cart_key, item_data in cart.items():
            product = get_object_or_404(Product, id=item_data['product_id'])
            item_price = product.base_price
            if product.design_ownership == 'designer' and product.design and product.design.status == 'approved':
                item_price += product.design.commission_per_sale
            item_price += Decimal(item_data['marketer_commission'])
            total_cart_price += item_price * item_data['quantity']
            cart_items.append({
                'id': cart_key,
                'product': product,
                'quantity': item_data['quantity'],
                'color': item_data['color'],
                'size': item_data['size'],
                'marketer_commission': Decimal(item_data['marketer_commission']),
                'total_price': item_price * item_data['quantity']
            })
            cart_items_json.append({
                'price': float(product.base_price),
                'quantity': item_data['quantity'],
                'commission': float(Decimal(item_data['marketer_commission'])),
                'designer_commission': float(product.design.commission_per_sale) if product.design_ownership == 'designer' and product.design and product.design.status == 'approved' else 0.0
            })
    
    return render(request, 'products/cart.html', {
        'cart_items': cart_items,
        'governorates': Governorate.objects.all(),
        'total_cart_price': total_cart_price,
        'cart_items_json': json.dumps(cart_items_json, cls=DjangoJSONEncoder)
    })

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, _("تم إزالة المنتج من العربة"))
    return redirect('products:cart')

def remove_from_cart_guest(request, cart_key):
    if not request.user.is_authenticated:
        cart = request.session.get('cart', {})
        if cart_key in cart:
            del cart[cart_key]
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, _("تم إزالة المنتج من العربة"))
        return redirect('products:cart')

@require_POST
@csrf_protect
def save_shipping_selection(request):
    try:
        data = json.loads(request.body)
        governorate_id = data.get('governorate_id')
        raw_shipping_cost = data.get('shipping_cost')

        if not governorate_id:
            return JsonResponse({'success': False, 'error': 'Missing governorate_id'}, status=400)

        # تنظيف تكلفة الشحن
        try:
            shipping_cost = str(float(raw_shipping_cost)) if raw_shipping_cost else "0.00"
        except (ValueError, TypeError):
            shipping_cost = "0.00"

        # حفظ في السيشن
        request.session['selected_governorate_id'] = str(governorate_id)
        request.session['selected_shipping_cost'] = shipping_cost
        request.session.modified = True

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def create_order(request):
    if request.method == 'POST':
        # بيانات العميل
        customer_name = request.POST.get('customer_name')
        phone_number = request.POST.get('phone_number')
        secondary_phone_number = request.POST.get('secondary_phone_number')
        governorate_id = request.POST.get('governorate')
        address = request.POST.get('address')
        notes = request.POST.get('notes')
        email = request.POST.get('email') if not request.user.is_authenticated else request.user.email
        marketer_commission = Decimal(request.POST.get('marketer_commission', '0.00')) if (
            request.user.is_authenticated and request.user.user_type == 'marketer'
        ) else Decimal('0.00')

        # تحقق من المحافظة
        if not governorate_id:
            messages.error(request, _("يرجى اختيار محافظة صالحة"))
            return redirect('products:create_order')
        governorate = get_object_or_404(Governorate, id=governorate_id)

        # تحقق من الإيميل
        if not request.user.is_authenticated and not email:
            messages.error(request, _("يرجى إدخال بريد إلكتروني"))
            return redirect('products:create_order')

        # جلب العربة
        cart_items = []
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        else:
            cart = request.session.get('cart', {})
            for key, data in cart.items():
                product = get_object_or_404(Product, id=data['product_id'])
                cart_items.append({
                    'id': key,
                    'product': product,
                    'quantity': int(data['quantity']),
                    'color': data['color'],
                    'size': data['size'],
                    'marketer_commission': Decimal(data.get('marketer_commission', '0.00')),
                    'marketer': None
                })

        if not cart_items:
            messages.error(request, _("العربة فارغة"))
            return redirect('products:cart')

        # تحديث الكميات والألوان والمقاسات
        for item in cart_items:
            is_model = hasattr(item, 'id')
            item_id = item.id if is_model else item['id']
            product = item.product if is_model else item['product']

            # الكمية
            qty_str = request.POST.get(f'quantity_{item_id}')
            try:
                quantity = int(qty_str)
                if quantity <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messages.error(request, _(f"كمية غير صالحة لـ {product.name}"))
                return redirect('products:create_order')

            # اللون والمقاس
            color = request.POST.get(f'color_{item_id}', item.color if is_model else item['color'])
            size = request.POST.get(f'size_{item_id}', item.size if is_model else item['size'])

            # تحقق من المخزون
            if quantity > product.stock:
                messages.error(request, _(f"الكمية ({quantity}) غير متوفرة لـ {product.name}"))
                return redirect('products:create_order')

            try:
                color_obj = ProductColor.objects.get(product=product, color=color)
                if quantity > color_obj.stock:
                    messages.error(request, _(f"اللون {color} غير متوفر"))
                    return redirect('products:create_order')
            except ProductColor.DoesNotExist:
                messages.error(request, _(f"اللون {color} غير متاح"))
                return redirect('products:create_order')

            try:
                size_obj = ProductSize.objects.get(product=product, size=size)
                if quantity > size_obj.stock:
                    messages.error(request, _(f"المقاس {size} غير متوفر"))
                    return redirect('products:create_order')
            except ProductSize.DoesNotExist:
                messages.error(request, _(f"المقاس {size} غير متاح"))
                return redirect('products:create_order')

            # تحديث العربة
            if request.user.is_authenticated:
                item.quantity = quantity
                item.color = color
                item.size = size
                item.save()
            else:
                cart = request.session.get('cart', {})
                cart_key = str(item['id'])
                cart[cart_key]['quantity'] = quantity
                cart[cart_key]['color'] = color
                cart[cart_key]['size'] = size
                request.session['cart'] = cart
                request.session.modified = True

        # إنشاء الطلب
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                customer_name=customer_name,
                phone_number=phone_number,
                secondary_phone_number=secondary_phone_number,
                governorate=governorate,
                address=address,
                notes=notes,
                total_price=Decimal('0.00'),
                status='pending',
                email=email
            )
            total_price = Decimal(governorate.shipping_cost)

            for item in cart_items:
                is_model = hasattr(item, 'id')
                product = item.product if is_model else item['product']
                quantity = int(item.quantity if is_model else item['quantity'])
                color = item.color if is_model else item['color']
                size = item.size if is_model else item['size']
                marketer_comm = item.marketer_commission if is_model else item['marketer_commission']

                # خصم المخزون
                product.stock -= quantity
                product.save()

                ProductColor.objects.filter(product=product, color=color).update(stock=F('stock') - quantity)
                ProductSize.objects.filter(product=product, size=size).update(stock=F('stock') - quantity)

                # عمولة المصمم
                designer_comm = Decimal('0.00')
                if (product.design_ownership == 'designer' and
                        product.design and product.design.status == 'approved'):
                    designer_comm = product.design.commission_per_sale

                # إنشاء عنصر الطلب
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    color=color,
                    size=size,
                    marketer_commission=marketer_comm,
                    designer_commission=designer_comm
                )

                total_price += (product.base_price + designer_comm + marketer_comm) * quantity

                # حذف من العربة
                if request.user.is_authenticated:
                    item.delete()
                else:
                    cart = request.session.get('cart', {})
                    del cart[str(item['id'])]
                    request.session['cart'] = cart
                    request.session.modified = True

            order.total_price = total_price
            order.save()

        # إرسال إيميل
        try:
            send_mail(
                subject=_("طلبك قيد المراجعة"),
                message=_(
                    f"عزيزي {customer_name},\n\n"
                    f"تم استلام طلبك رقم {order.id} بنجاح!\n"
                    f"الإجمالي: {order.total_price} جنيه (شامل الشحن)\n"
                    f"سنتواصل معك قريبًا.\nشكرًا لتسوقك مع ترافيكو!"
                ),
                from_email=None,
                recipient_list=[email],
                fail_silently=False
            )
        except (SMTPRecipientsRefused, SMTPException):
            messages.warning(request, _("تم الطلب لكن فشل إرسال الإيميل"))

        messages.success(request, _("تم إنشاء الطلب بنجاح!"))
        return redirect('products:product_list')

    # ====================== GET ======================
    governorates = Governorate.objects.all()
    selected_governorate_id = request.session.get('selected_governorate_id')
    selected_shipping_cost = request.session.get('selected_shipping_cost', '0.00')

    if not selected_governorate_id:
        messages.warning(request, _("يرجى اختيار المحافظة أولاً"))
        return redirect('products:cart')

    try:
        selected_governorate = Governorate.objects.get(id=selected_governorate_id)
    except Governorate.DoesNotExist:
        messages.error(request, _("المحافظة غير صالحة"))
        return redirect('products:cart')

    try:
        shipping_cost = Decimal(selected_shipping_cost)
    except (InvalidOperation, ValueError):
        shipping_cost = Decimal('0.00')

    cart_item_details = []
    total_cart_price = Decimal('0.00')
    is_marketer = request.user.is_authenticated and request.user.user_type == 'marketer'
    current_marketer_commission = Decimal('0.00')

    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user).select_related('product', 'product__design')
        for item in items:
            designer_comm = item.product.design.commission_per_sale if (
                item.product.design_ownership == 'designer' and
                item.product.design and item.product.design.status == 'approved'
            ) else Decimal('0.00')
            display_price = item.product.base_price + designer_comm
            unit_price = display_price + item.marketer_commission
            line_total = unit_price * item.quantity
            total_cart_price += line_total

            cart_item_details.append({
                'item_id': item.id,
                'product': item.product,
                'quantity': item.quantity,
                'color': item.color,
                'size': item.size,
                'marketer_comm': item.marketer_commission,
                'designer_comm': designer_comm,
                'display_price': display_price,
                'unit_price': unit_price,
                'line_total': line_total,
            })
    else:
        cart = request.session.get('cart', {})
        for key, data in cart.items():
            product = get_object_or_404(Product, id=data['product_id'])
            designer_comm = product.design.commission_per_sale if (
                product.design_ownership == 'designer' and
                product.design and product.design.status == 'approved'
            ) else Decimal('0.00')
            marketer_comm = Decimal(data.get('marketer_commission', '0.00'))
            display_price = product.base_price + designer_comm
            unit_price = display_price + marketer_comm
            line_total = unit_price * int(data['quantity'])
            total_cart_price += line_total

            cart_item_details.append({
                'item_id': key,
                'product': product,
                'quantity': int(data['quantity']),
                'color': data['color'],
                'size': data['size'],
                'marketer_comm': marketer_comm,
                'designer_comm': designer_comm,
                'display_price': display_price,
                'unit_price': unit_price,
                'line_total': line_total,
            })

    if is_marketer and cart_item_details:
        commissions = [d['marketer_comm'] for d in cart_item_details]
        if len(set(commissions)) == 1:
            current_marketer_commission = commissions[0]

    grand_total = total_cart_price + shipping_cost

    return render(request, 'products/create_order.html', {
        'cart_item_details': cart_item_details,
        'governorates': governorates,
        'selected_governorate': selected_governorate,
        'shipping_cost': shipping_cost,
        'total_cart_price': total_cart_price,
        'grand_total': grand_total,
        'is_marketer': is_marketer,
        'current_marketer_commission': current_marketer_commission,
    })
    
        
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorites = Favorite.objects.filter(user=request.user).values_list('product_id', flat=True) if request.user.is_authenticated else []
    display_price = product.base_price
    if product.design_ownership == 'designer' and product.design and product.design.status == 'approved':
        display_price += product.design.commission_per_sale
    availability = 'https://schema.org/InStock' if product.stock > 0 else 'https://schema.org/OutOfStock'
    return render(request, 'products/product_detail.html', {
        'product': product,
        'favorites': favorites,
        'user': request.user,
        'display_price': display_price,
        'availability': availability,
        'images': product.images or [product.image] if product.image else ['https://via.placeholder.com/300']
    })

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import activate

@csrf_exempt
def set_language(request, lang_code):
    if request.method == 'POST':
        if lang_code in ['ar', 'en']:
            activate(lang_code)
            request.session['django_language'] = lang_code
            return JsonResponse({'status': 'success', 'language': lang_code})
        return JsonResponse({'status': 'error', 'message': 'Invalid language code'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)



