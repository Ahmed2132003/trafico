from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from decimal import Decimal
import json
from .models import Product, Favorite, CartItem, Order, OrderItem, Governorate, ProductColor, ProductSize, Design

def is_superuser(user):
    return user.is_superuser

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
    return user.is_superuser

@login_required
@user_passes_test(is_superuser, login_url='/login/')


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
@user_passes_test(is_superuser, login_url='/login/')
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
@user_passes_test(is_superuser, login_url='/login/')
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



@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        color = request.POST.get('color')
        size = request.POST.get('size')
        marketer_commission = Decimal(request.POST.get('marketer_commission', '0.00')) if hasattr(request.user, 'user_type') and request.user.user_type == 'marketer' else Decimal('0.00')

        # التحقق من إدخال اللون والمقاس
        if not color:
            messages.error(request, _("يرجى اختيار لون"))
            return redirect('products:product_detail', product_id=product.id)
        if not size:
            messages.error(request, _("يرجى اختيار مقاس"))
            return redirect('products:product_detail', product_id=product.id)

        # التحقق من المخزون الأساسي
        if quantity <= 0 or quantity > product.stock:
            messages.error(request, _(f"الكمية المطلوبة ({quantity}) غير متوفرة في المخزون الكلي"))
            return redirect('products:product_detail', product_id=product.id)

        # التحقق من مخزون اللون
        try:
            product_color = ProductColor.objects.get(product=product, color=color)
            if quantity > product_color.stock:
                messages.error(request, _(f"الكمية المطلوبة ({quantity}) غير متوفرة لهذا اللون ({color})"))
                return redirect('products:product_detail', product_id=product.id)
        except ProductColor.DoesNotExist:
            messages.error(request, _(f"اللون المختار ({color}) غير متاح"))
            return redirect('products:product_detail', product_id=product.id)

        # التحقق من مخزون المقاس
        try:
            product_size = ProductSize.objects.get(product=product, size=size)
            if quantity > product_size.stock:
                messages.error(request, _(f"الكمية المطلوبة ({quantity}) غير متوفرة لهذا المقاس ({size})"))
                return redirect('products:product_detail', product_id=product.id)
        except ProductSize.DoesNotExist:
            messages.error(request, _(f"المقاس المختار ({size}) غير متاح"))
            return redirect('products:product_detail', product_id=product.id)

        with transaction.atomic():
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                color=color,
                size=size,
                defaults={'quantity': quantity, 'marketer_commission': marketer_commission}
            )
            if not created:
                new_quantity = cart_item.quantity + quantity
                # التحقق من المخزون مرة أخرى عند زيادة الكمية
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

import json
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder

def cart_view(request):
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

from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal

@login_required
def create_order(request):
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        phone_number = request.POST.get('phone_number')
        secondary_phone_number = request.POST.get('secondary_phone_number')
        governorate_id = request.POST.get('governorate')
        address = request.POST.get('address')
        notes = request.POST.get('notes')
        marketer_commission = Decimal(request.POST.get('marketer_commission', '0.00')) if hasattr(request.user, 'user_type') and request.user.user_type == 'marketer' else Decimal('0.00')
        governorate = get_object_or_404(Governorate, id=governorate_id)
        cart_items = CartItem.objects.filter(user=request.user).select_related('product').prefetch_related('product__colors', 'product__sizes')
        
        if not cart_items:
            messages.error(request, _("العربة فارغة"))
            return redirect('products:cart')

        # التحقق من اللون والمقاس والكمية من النموذج
        for item in cart_items:
            color = request.POST.get(f'color_{item.id}', item.color)  # استخدام القيمة الموجودة كـ default
            size = request.POST.get(f'size_{item.id}', item.size)
            quantity_str = request.POST.get(f'quantity_{item.id}', str(item.quantity))
            
            try:
                quantity = int(quantity_str)
            except ValueError:
                messages.error(request, _(f"كمية غير صالحة للمنتج {item.product.name}"))
                return redirect('products:cart')

            # التحقق من إدخال اللون والمقاس
            if not color:
                messages.error(request, _(f"يرجى اختيار لون للمنتج {item.product.name}"))
                return redirect('products:cart')
            if not size:
                messages.error(request, _(f"يرجى اختيار مقاس للمنتج {item.product.name}"))
                return redirect('products:cart')
            if quantity <= 0:
                messages.error(request, _(f"يرجى إدخال كمية صالحة للمنتج {item.product.name}"))
                return redirect('products:cart')

            # التحقق من مخزون المنتج
            if quantity > item.product.stock:
                messages.error(request, _(f"الكمية المطلوبة ({quantity}) غير متوفرة في المخزون الكلي للمنتج {item.product.name}"))
                return redirect('products:cart')

            # التحقق من مخزون اللون
            try:
                product_color = ProductColor.objects.get(product=item.product, color=color)
                if quantity > product_color.stock:
                    messages.error(request, _(f"الكمية المطلوبة ({quantity}) غير متوفرة لهذا اللون ({color}) للمنتج {item.product.name}"))
                    return redirect('products:cart')
            except ProductColor.DoesNotExist:
                messages.error(request, _(f"اللون المختار ({color}) غير متاح للمنتج {item.product.name}"))
                return redirect('products:cart')

            # التحقق من مخزون المقاس
            try:
                product_size = ProductSize.objects.get(product=item.product, size=size)
                if quantity > product_size.stock:
                    messages.error(request, _(f"الكمية المطلوبة ({quantity}) غير متوفرة لهذا المقاس ({size}) للمنتج {item.product.name}"))
                    return redirect('products:cart')
            except ProductSize.DoesNotExist:
                messages.error(request, _(f"المقاس المختار ({size}) غير متاح للمنتج {item.product.name}"))
                return redirect('products:cart')

            # تحديث CartItem باللون والمقاس والكمية الجديدة
            item.color = color
            item.size = size
            item.quantity = quantity
            item.marketer_commission = marketer_commission if hasattr(request.user, 'user_type') and request.user.user_type == 'marketer' else item.marketer_commission
            item.save()

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                customer_name=customer_name,
                phone_number=phone_number,
                secondary_phone_number=secondary_phone_number,
                governorate=governorate,
                address=address,
                notes=notes,
                total_price=Decimal('0.00'),
                status='pending'
            )
            total_price = Decimal(governorate.shipping_cost)

            for item in cart_items:
                # تقليل المخزون الأساسي
                item.product.stock -= item.quantity
                item.product.save()

                # تقليل مخزون اللون
                product_color = ProductColor.objects.get(product=item.product, color=item.color)
                product_color.stock -= item.quantity
                product_color.save()

                # تقليل مخزون المقاس
                product_size = ProductSize.objects.get(product=item.product, size=item.size)
                product_size.stock -= item.quantity
                product_size.save()

                # إنشاء عنصر الطلب
                order_item = OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    color=item.color,
                    size=item.size,
                    marketer_commission=marketer_commission if hasattr(request.user, 'user_type') and request.user.user_type == 'marketer' else item.marketer_commission,
                    marketer=request.user if hasattr(request.user, 'user_type') and request.user.user_type == 'marketer' else item.marketer,
                    designer_commission=item.product.design.commission_per_sale if item.product.design_ownership == 'designer' and item.product.design and item.product.design.status == 'approved' else Decimal('0.00')
                )
                total_price += order_item.total_price()
                item.delete()
            
            order.total_price = total_price
            order.save()

        # إرسال بريد إلكتروني لتأكيد الطلب
        subject = _("طلبك قيد المراجعة")
        message = _(
            f"عزيزي {customer_name},\n\n"
            f"تم استلام طلبك رقم {order.id} بنجاح وهو الآن قيد المراجعة.\n"
            f"تفاصيل الطلب:\n"
            f"- العنوان: {address}, {governorate.name}\n"
            f"- رقم الهاتف: {phone_number}\n"
            f"- تكلفة الشحن: {governorate.shipping_cost} جنيه\n"
            f"- المنتجات:\n"
        )
        for item in order.order_items.all():
            item_price = item.product.base_price + item.designer_commission + item.marketer_commission
            message += f"  - {item.product.name} (الكمية: {item.quantity}, اللون: {item.color}, المقاس: {item.size}, السعر: {item_price * item.quantity} جنيه)\n"
        message += _(
            f"\nالسعر الإجمالي: {order.total_price} جنيه\n"
            f"سنتواصل معك قريبًا لتأكيد الطلب.\n"
            f"شكرًا لتسوقك مع ترافيكو!"
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [request.user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        messages.success(request, _("تم إنشاء الطلب بنجاح وسيتم إرسال تأكيد إلى بريدك الإلكتروني"))
        return redirect('products:product_list')
    
    governorates = Governorate.objects.all()
    cart_items = CartItem.objects.filter(user=request.user).select_related('product').prefetch_related('product__colors', 'product__sizes')
    total_cart_price = Decimal('0.00')
    for item in cart_items:
        item_price = item.product.base_price
        if item.product.design_ownership == 'designer' and item.product.design and item.product.design.status == 'approved':
            item_price += item.product.design.commission_per_sale
        item_price += item.marketer_commission
        total_cart_price += item_price * item.quantity
    return render(request, 'products/create_order.html', {
        'cart_items': cart_items,
        'governorates': governorates,
        'total_cart_price': total_cart_price,
        'is_marketer': hasattr(request.user, 'user_type') and request.user.user_type == 'marketer'
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