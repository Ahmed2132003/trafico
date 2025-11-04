from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from products.models import Order, OrderItem, Product, Design, Governorate ,ProductColor, ProductSize
from django.db.models import Sum, Count
from django.db import models, transaction
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from .models import WithdrawalRequest, BonusRequest
from users.models import User, Profile
from django.http import JsonResponse
import json
from django.utils.translation import activate
import logging
from django.urls import reverse
# إعداد Logging
logger = logging.getLogger(__name__)

def user_is_marketer(user):
    return user.is_authenticated and user.user_type == 'marketer'

def user_is_designer(user):
    return user.is_authenticated and user.user_type == 'designer'

def user_is_superuser(user):
    return user.is_authenticated and user.is_superuser
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

def dashboard(request):
    user = request.user
    if not user.is_authenticated or (not user.is_superuser and user.user_type == 'customer'):
        return redirect(reverse('products:product_list'))
    period = request.GET.get('period', 'month')
    now = timezone.now()
    if period == '90days':
        start_date = now - timedelta(days=90)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    context = {
        'user': user,
        'user_type': user.user_type,
        'orders': [],
        'stats': {},
        'period': period,
    }

    if user.user_type == 'customer':
        orders = Order.objects.filter(user=user, created_at__gte=start_date)
        paginator = Paginator(orders, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        stats = {
            'pending': orders.filter(status='pending').count(),
            'shipped': orders.filter(status='shipped').count(),
            'completed': orders.filter(status='completed').count(),
            'cancelled': orders.filter(status='cancelled').count(),
            'total_orders': orders.count(),
        }
        context['orders'] = page_obj
        context['stats'] = stats

    elif user.user_type == 'marketer':
        orders = OrderItem.objects.filter(
            marketer=user,
            order__status__in=['pending', 'shipped', 'completed', 'cancelled'],
            order__created_at__gte=start_date
        )
        paginator = Paginator(orders, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        total_earnings = user.total_earnings or Decimal('0.00')
        total_withdrawals = WithdrawalRequest.objects.filter(
            user=user,
            status='approved'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_bonuses = BonusRequest.objects.filter(
            user=user,
            status='approved',
            created_at__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        remaining_balance = total_earnings - total_withdrawals
        remaining_balance = max(remaining_balance, Decimal('0.00'))
        stats = {
            'pending': orders.filter(order__status='pending').count(),
            'shipped': orders.filter(order__status='shipped').count(),
            'completed': orders.filter(order__status='completed').count(),
            'cancelled': orders.filter(order__status='cancelled').count(),
            'total_earnings': total_earnings,
            'total_withdrawals': total_withdrawals,
            'total_bonuses': total_bonuses,  
            'remaining_balance': remaining_balance,
            'total_orders': orders.count(),
        }
        context['orders'] = page_obj
        context['stats'] = stats

    elif user.user_type == 'designer':
        designs = Design.objects.filter(designer=user, created_at__gte=start_date)
        orders = OrderItem.objects.filter(
            product__design__designer=user,
            product__design__status='approved',
            order__status__in=['pending', 'shipped', 'completed', 'cancelled'],
            order__created_at__gte=start_date
        )
        paginator = Paginator(orders, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        total_earnings = user.total_earnings or Decimal('0.00')
        total_withdrawals = WithdrawalRequest.objects.filter(
            user=user,
            status='approved'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_bonuses = BonusRequest.objects.filter(
            user=user,
            status='approved',
            created_at__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        remaining_balance = total_earnings - total_withdrawals
        remaining_balance = max(remaining_balance, Decimal('0.00'))
        stats = {
            'pending': orders.filter(order__status='pending').count(),
            'shipped': orders.filter(order__status='shipped').count(),
            'completed': orders.filter(order__status='completed').count(),
            'cancelled': orders.filter(order__status='cancelled').count(),
            'total_designs': designs.count(),
            'total_earnings': total_earnings,
            'total_withdrawals': total_withdrawals,
            'total_bonuses': total_bonuses,  
            'remaining_balance': remaining_balance,
            'total_orders': orders.count(),
        }
        context['orders'] = page_obj
        context['designs'] = designs
        context['stats'] = stats

    elif user.is_superuser:
        orders = Order.objects.filter(created_at__gte=start_date).order_by('-created_at')
        designs = Design.objects.filter(created_at__gte=start_date)
        withdrawals = WithdrawalRequest.objects.filter(created_at__gte=start_date)
        bonuses = BonusRequest.objects.filter(created_at__gte=start_date)
        paginator = Paginator(orders, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        total_bonuses = BonusRequest.objects.filter(
            status='approved',
            created_at__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        stats = {
            'pending': orders.filter(status='pending').count(),
            'shipped': orders.filter(status='shipped').count(),
            'completed': orders.filter(status='completed').count(),
            'cancelled': orders.filter(status='cancelled').count(),
            'total_orders': orders.count(),
            'pending_designs': designs.filter(status='pending').count(),
            'approved_designs': designs.filter(status='approved').count(),
            'rejected_designs': designs.filter(status='rejected').count(),
            'total_designs': designs.count(),
            'pending_withdrawals': withdrawals.filter(status='pending').count(),
            'approved_withdrawals': withdrawals.filter(status='approved').count(),
            'failed_withdrawals': withdrawals.filter(status='failed').count(),
            'total_withdrawals': withdrawals.count(),
            'pending_bonuses': bonuses.filter(status='pending').count(),
            'approved_bonuses': bonuses.filter(status='approved').count(),
            'rejected_bonuses': bonuses.filter(status='rejected').count(),
            'total_bonuses': total_bonuses,  # إضافة إجمالي المكافآت
        }
        context['orders'] = page_obj
        context['designs'] = designs
        context['withdrawals'] = withdrawals if withdrawals.exists() else None
        context['bonuses'] = bonuses if bonuses.exists() else None
        context['stats'] = stats

    return render(request, 'dashboard/dashboard.html', context)

@login_required
@user_passes_test(user_is_marketer, login_url='/dashboard/')
def withdrawal_request(request):
    user = request.user
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        wallet_number = request.POST.get('wallet_number')
        payment_method = request.POST.get('payment_method')
        amount = Decimal(request.POST.get('amount', '0.00'))
        
        total_earnings = user.total_earnings or Decimal('0.00')
        total_withdrawals = WithdrawalRequest.objects.filter(
            user=user,
            status='approved'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        remaining_balance = total_earnings - total_withdrawals
        
        print(f"Withdrawal Request - Username: {user.username}, Requested Amount: {amount}, Total Earnings: {total_earnings}, Total Withdrawals: {total_withdrawals}, Remaining Balance: {remaining_balance}")
        
        if amount > remaining_balance:
            messages.error(request, _("المبلغ المطلوب أكبر من رصيدك المتاح"))
            return redirect('dashboard:withdrawal_request')
        
        withdrawal = WithdrawalRequest.objects.create(
            user=user,
            full_name=full_name,
            address=address,
            phone_number=phone_number,
            wallet_number=wallet_number,
            payment_method=payment_method,
            amount=amount,
            status='pending'
        )
        superusers = User.objects.filter(is_superuser=True)
        for superuser in superusers:
            try:
                send_mail(
                    'طلب سحب جديد',
                    f'تم تقديم طلب سحب جديد من {user.username} ({user.get_user_type_display()}).\nالمبلغ: {amount} جنيه\nرقم الطلب: {withdrawal.id}',
                    settings.EMAIL_HOST_USER,
                    [superuser.email],
                    fail_silently=True,
                )
            except Exception as e:
                messages.warning(request, f'خطأ في إرسال إشعار للإدارة: {str(e)}')
        
        messages.success(request, _("تم تقديم طلب السحب بنجاح"))
        return redirect('dashboard:dashboard')
    
    total_earnings = user.total_earnings or Decimal('0.00')
    total_withdrawals = WithdrawalRequest.objects.filter(
        user=user,
        status='approved'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    remaining_balance = total_earnings - total_withdrawals
    
    return render(request, 'dashboard/withdrawal_request.html', {
        'user': user,
        'remaining_balance': remaining_balance,
    })
@login_required
@user_passes_test(user_is_designer, login_url='/dashboard/')
def designer_withdrawal_request(request):
    user = request.user
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        wallet_number = request.POST.get('wallet_number')
        amount = Decimal(request.POST.get('amount', '0.00'))
        
        total_earnings = user.total_earnings or Decimal('0.00')
        total_withdrawals = WithdrawalRequest.objects.filter(
            user=user,
            status='approved'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        remaining_balance = total_earnings - total_withdrawals
        
        print(f"Designer Withdrawal Request - Username: {user.username}, Requested Amount: {amount}, Total Earnings: {total_earnings}, Total Withdrawals: {total_withdrawals}, Remaining Balance: {remaining_balance}")
        
        if amount > remaining_balance:
            messages.error(request, _("المبلغ المطلوب أكبر من رصيدك المتاح"))
            return redirect('dashboard:designer_withdrawal_request')
        
        withdrawal = WithdrawalRequest.objects.create(
            user=user,
            full_name=full_name,
            address=address,
            phone_number=phone_number,
            wallet_number=wallet_number,
            amount=amount,
            status='pending'
        )
        superusers = User.objects.filter(is_superuser=True)
        for superuser in superusers:
            try:
                send_mail(
                    'طلب سحب جديد من مصمم',
                    f'تم تقديم طلب سحب جديد من {user.username} (مصمم).\nالمبلغ: {amount} جنيه\nرقم الطلب: {withdrawal.id}',
                    settings.EMAIL_HOST_USER,
                    [superuser.email],
                    fail_silently=True,
                )
            except Exception as e:
                messages.warning(request, f'خطأ في إرسال إشعار للإدارة: {str(e)}')
        
        messages.success(request, _("تم تقديم طلب السحب بنجاح"))
        return redirect('dashboard:dashboard')
    
    total_earnings = user.total_earnings or Decimal('0.00')
    total_withdrawals = WithdrawalRequest.objects.filter(
        user=user,
        status='approved'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    remaining_balance = total_earnings - total_withdrawals
    
    return render(request, 'dashboard/designer_withdrawal_request.html', {
        'user': user,
        'remaining_balance': remaining_balance,
    })

@login_required
def withdrawal_history(request):
    period = request.GET.get('period', 'month')
    now = timezone.now()
    if period == '90days':
        start_date = now - timedelta(days=90)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    withdrawals = WithdrawalRequest.objects.filter(
        user=request.user,
        created_at__gte=start_date
    ).values('id', 'amount', 'status', 'created_at').annotate(transaction_type=models.Value('withdrawal', output_field=models.CharField()))
    
    bonuses = BonusRequest.objects.filter(
        user=request.user,
        status='approved',
        created_at__gte=start_date
    ).values('id', 'amount', 'status', 'created_at').annotate(transaction_type=models.Value('bonus', output_field=models.CharField()))
    
    transactions = list(withdrawals) + list(bonuses)
    transactions = sorted(transactions, key=lambda x: x['created_at'], reverse=True)
    
    print(f"Withdrawal History - Username: {request.user.username}, Total Transactions: {len(transactions)}, Withdrawals: {len(withdrawals)}, Bonuses: {len(bonuses)}")
    
    return render(request, 'dashboard/withdrawal_history.html', {
        'transactions': transactions,
        'period': period,
    })

@login_required
def bonus_request(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        completed_orders = OrderItem.objects.filter(
            marketer=request.user,
            order__status='completed',
            order__created_at__gte=timezone.now() - timedelta(days=30)
        ).count() if request.user.user_type == 'marketer' else OrderItem.objects.filter(
            product__design__designer=request.user,
            product__design__status='approved',
            order__status='completed',
            order__created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        bonus = BonusRequest.objects.create(
            user=request.user,
            full_name=full_name,
            completed_orders=completed_orders,
            status='pending'
        )
        superusers = User.objects.filter(is_superuser=True)
        for superuser in superusers:
            try:
                send_mail(
                    subject='طلب مكافأة جديد',
                    message=(
                        f'تم تقديم طلب مكافأة جديد من {request.user.username} ({request.user.get_user_type_display()}).\n'
                        f'رقم الطلب: {bonus.id}\n'
                        f'الاسم الكامل: {full_name}\n'
                        f'عدد الطلبات المكتملة (آخر 30 يوم): {completed_orders}\n'
                        f'الحالة: قيد المراجعة'
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[superuser.email],
                    fail_silently=True
                )
            except Exception as e:
                messages.warning(request, f'خطأ في إرسال إشعار للإدارة: {str(e)}')
        
        messages.success(request, _("تم تقديم طلب المكافأة بنجاح"))
        print(f"Bonus Request - Username: {request.user.username}, Completed Orders: {completed_orders}")
        return redirect('dashboard:dashboard')
    
    completed_orders = OrderItem.objects.filter(
        marketer=request.user,
        order__status='completed',
        order__created_at__gte=timezone.now() - timedelta(days=30)
    ).count() if request.user.user_type == 'marketer' else OrderItem.objects.filter(
        product__design__designer=request.user,
        product__design__status='approved',
        order__status='completed',
        order__created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    return render(request, 'dashboard/bonus_request.html', {
        'user': request.user,
        'completed_orders': completed_orders
    })

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def manage_orders(request):
    period = request.GET.get('period', 'month')
    now = timezone.now()
    if period == '90days':
        start_date = now - timedelta(days=90)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    orders = Order.objects.filter(created_at__gte=start_date)
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    stats = {
        'pending': orders.filter(status='pending').count(),
        'shipped': orders.filter(status='shipped').count(),
        'completed': orders.filter(status='completed').count(),
        'cancelled': orders.filter(status='cancelled').count(),
        'total_orders': orders.count(),
    }
    
    # تعديل: استخدام username آمن للطلبات بدون مستخدم
    completed_orders_data = [
        (order.id, order.created_at, order.status, 
         order.user.username if order.user else 'غير مسجل')
        for order in orders.filter(status='completed')
    ]
    
    print(f"Manage Orders - Username: {request.user.username}, Total Orders: {orders.count()}, Completed Orders: {stats['completed']}")
    print(f"Completed Orders IDs and Dates: {completed_orders_data}")
    print(f"Start Date: {start_date}")
    print(f"Orders in Paginator: {[(order.id, order.created_at) for order in page_obj]}")
    
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id)
        
        if new_status in ['pending', 'shipped', 'completed', 'cancelled']:
            old_status = order.status
            order.status = new_status
            order.save()
            
            if new_status == 'completed' and old_status != 'completed':
                for item in order.order_items.all():
                    if item.marketer:
                        with transaction.atomic():
                            item.marketer.total_earnings += item.marketer_commission * Decimal(str(item.quantity))
                            item.marketer.save()
                            print(f"Updated total_earnings for marketer {item.marketer.username}: {item.marketer.total_earnings}")
                    if item.product.design_ownership == 'designer' and item.product.design and item.product.designer:
                        with transaction.atomic():
                            item.product.designer.total_earnings += item.designer_commission * Decimal(str(item.quantity))
                            item.product.designer.save()
                            print(f"Updated total_earnings for designer {item.product.designer.username}: {item.product.designer.total_earnings}")
            
            # إرسال إشعارات للمسوق والمصمم
            for item in order.order_items.all():
                if item.marketer:
                    try:
                        send_mail(
                            'تحديث حالة الطلب',
                            f'تفاصيل الطلب:\n'
                            f'رقم الطلب: {order.id}\n'
                            f'اسم العميل: {order.customer_name}\n'
                            f'الحالة الجديدة: {order.get_status_display()}',
                            settings.EMAIL_HOST_USER,
                            [item.marketer.email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        messages.warning(request, f'خطأ في إرسال إشعار للمسوق: {str(e)}')
                if item.product.design_ownership == 'designer' and item.product.design and item.product.designer:
                    try:
                        send_mail(
                            'تحديث حالة الطلب',
                            f'تفاصيل الطلب:\n'
                            f'رقم الطلب: {order.id}\n'
                            f'اسم العميل: {order.customer_name}\n'
                            f'الحالة الجديدة: {order.get_status_display()}',
                            settings.EMAIL_HOST_USER,
                            [item.product.designer.email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        messages.warning(request, f'خطأ في إرسال إشعار للمصمم: {str(e)}')
            
            messages.success(request, _("تم تحديث حالة الطلب بنجاح"))
        else:
            messages.error(request, _("حالة غير صالحة"))
        
        return redirect('dashboard:manage_orders')
    
    return render(request, 'dashboard/manage_orders.html', {
        'orders': page_obj,
        'stats': stats,
        'period': period,
    })
@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # إحصائيات بسيطة للطلب
    stats = {
        'total_items': order.order_items.count(),
        'total_price': order.total_price,
        'status': order.get_status_display(),
        'created_at': order.created_at,
        'customer_name': order.customer_name,
        'phone_number': order.phone_number,
        'address': order.address,
        'governorate': order.governorate.name if order.governorate else 'غير محدد',
        'notes': order.notes or 'لا توجد ملاحظات',
    }
    
    # عناصر الطلب
    items = order.order_items.all()
    
    print(f"Order Detail - Order ID: {order.id}, User: {order.user.username if order.user else 'غير مسجل'}, Total Items: {stats['total_items']}")
    
    return render(request, 'dashboard/order_detail.html', {
        'order': order,
        'items': items,
        'stats': stats,
    })
    
@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def manage_products(request):
    product = None
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if 'delete' in request.POST:
            try:
                product = get_object_or_404(Product, id=product_id)
                product.delete()
                messages.success(request, _("تم حذف المنتج بنجاح"))
                print(f"Deleted Product - ID: {product_id}")
            except Exception as e:
                messages.error(request, _("خطأ في حذف المنتج: ") + str(e))
                print(f"Error deleting product {product_id}: {str(e)}")
            return redirect('dashboard:manage_products')
        else:
            name = request.POST.get('name')
            description = request.POST.get('description')
            base_price = request.POST.get('base_price')
            image = request.POST.get('image')
            stock = request.POST.get('stock')
            design_ownership = request.POST.get('design_ownership')
            design_id = request.POST.get('design_id')
            designer_id = request.POST.get('designer_id')
            colors = request.POST.get('colors')
            sizes = request.POST.get('sizes')
            color_stocks = request.POST.get('color_stocks')
            size_stocks = request.POST.get('size_stocks')

            try:
                with transaction.atomic():
                    if product_id:
                        product = get_object_or_404(Product, id=product_id)
                        product.name = name
                        product.description = description
                        product.base_price = Decimal(base_price)
                        product.image = image
                        product.stock = int(stock)
                        product.design_ownership = design_ownership
                        product.design = Design.objects.get(id=design_id) if design_id and design_ownership == 'designer' else None
                        product.designer = User.objects.get(id=designer_id) if designer_id and design_ownership == 'designer' else None
                        product.save()

                        # حذف الألوان والمقاسات القديمة
                        product.colors.all().delete()
                        product.sizes.all().delete()

                        # إضافة الألوان الجديدة
                        if colors and color_stocks:
                            color_list = colors.split(',')
                            stock_list = color_stocks.split(',')
                            if len(color_list) == len(stock_list):
                                for color, stock in zip(color_list, stock_list):
                                    if color.strip() and stock.strip():
                                        ProductColor.objects.create(
                                            product=product,
                                            color=color.strip(),
                                            stock=int(stock.strip())
                                        )

                        # إضافة المقاسات الجديدة
                        if sizes and size_stocks:
                            size_list = sizes.split(',')
                            stock_list = size_stocks.split(',')
                            if len(size_list) == len(stock_list):
                                for size, stock in zip(size_list, stock_list):
                                    if size.strip() and stock.strip():
                                        ProductSize.objects.create(
                                            product=product,
                                            size=size.strip(),
                                            stock=int(stock.strip())
                                        )

                        messages.success(request, _("تم تحديث المنتج بنجاح"))
                        print(f"Updated Product - ID: {product_id}, Name: {name}")
                    else:
                        product = Product.objects.create(
                            name=name,
                            description=description,
                            base_price=Decimal(base_price),
                            image=image,
                            stock=int(stock),
                            design_ownership=design_ownership,
                            design=Design.objects.get(id=design_id) if design_id and design_ownership == 'designer' else None,
                            designer=User.objects.get(id=designer_id) if designer_id and design_ownership == 'designer' else None
                        )

                        # إضافة الألوان
                        if colors and color_stocks:
                            color_list = colors.split(',')
                            stock_list = color_stocks.split(',')
                            if len(color_list) == len(stock_list):
                                for color, stock in zip(color_list, stock_list):
                                    if color.strip() and stock.strip():
                                        ProductColor.objects.create(
                                            product=product,
                                            color=color.strip(),
                                            stock=int(stock.strip())
                                        )

                        # إضافة المقاسات
                        if sizes and size_stocks:
                            size_list = sizes.split(',')
                            stock_list = size_stocks.split(',')
                            if len(size_list) == len(stock_list):
                                for size, stock in zip(size_list, stock_list):
                                    if size.strip() and stock.strip():
                                        ProductSize.objects.create(
                                            product=product,
                                            size=size.strip(),
                                            stock=int(stock.strip())
                                        )

                        messages.success(request, _("تم إنشاء المنتج بنجاح"))
                        print(f"Created Product - ID: {product.id}, Name: {name}")
            except Exception as e:
                messages.error(request, _("خطأ في إنشاء/تحديث المنتج: ") + str(e))
                print(f"Error managing product: {str(e)}")
                return redirect('dashboard:manage_products')

    # معالجة طلب GET
    try:
        if request.GET.get('product_id'):
            product = get_object_or_404(Product, id=request.GET.get('product_id'))
    except Exception as e:
        messages.error(request, _("خطأ في تحميل المنتج: ") + str(e))
        print(f"Error loading product for edit: {str(e)}")
        product = None

    products = Product.objects.all()
    designs = Design.objects.filter(status='approved')
    designers = User.objects.filter(user_type='designer')
    print(f"Manage Products - Total Products: {products.count()}")
    return render(request, 'dashboard/manage_products.html', {
        'products': products,
        'designs': designs,
        'designers': designers,
        'product': product,
    })

@login_required
@user_passes_test(user_is_designer, login_url='/dashboard/')
def submit_design(request):
    if request.method == 'POST':
        pdf_url = request.POST.get('pdf_url')
        commission_per_sale = request.POST.get('commission_per_sale')
        
        try:
            commission_per_sale = Decimal(commission_per_sale)
            design = Design.objects.create(
                designer=request.user,
                pdf_url=pdf_url,
                commission_per_sale=commission_per_sale,
                status='pending'
            )
            superusers = User.objects.filter(is_superuser=True)
            for superuser in superusers:
                try:
                    send_mail(
                        'طلب تصميم جديد',
                        f'تم تقديم تصميم جديد من {request.user.username}.\nرابط PDF: {pdf_url}\nرقم الطلب: {design.id}\nعمولة البيع: {commission_per_sale} جنيه',
                        settings.EMAIL_HOST_USER,
                        [superuser.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    messages.warning(request, f'خطأ في إرسال إشعار للإدارة: {str(e)}')
            messages.success(request, _("تم تقديم التصميم بنجاح"))
            print(f"Submitted Design - ID: {design.id}, Designer: {request.user.username}, Commission: {commission_per_sale}")
        except Exception as e:
            messages.error(request, _("خطأ في تقديم التصميم: ") + str(e))
            print(f"Error submitting design: {str(e)}")
        
        return redirect('dashboard:dashboard')
    
    return render(request, 'dashboard/submit_design.html', {'user': request.user})


def user_is_superuser(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def manage_designs(request):
    design = None
    if request.method == 'POST':
        design_id = request.POST.get('design_id')
        if 'delete' in request.POST:
            try:
                design = get_object_or_404(Design, id=design_id)
                designer_email = design.designer.email
                design.delete()
                messages.success(request, _("تم حذف التصميم بنجاح"))
                print(f"Deleted Design - ID: {design_id}")
                try:
                    send_mail(
                        'حذف التصميم',
                        f'تم حذف التصميم رقم {design_id} من النظام.\nيرجى التواصل مع الإدارة لمزيد من التفاصيل.',
                        settings.EMAIL_HOST_USER,
                        [designer_email],
                        fail_silently=True,
                    )
                except Exception as e:
                    messages.warning(request, f'خطأ في إرسال إشعار للمصمم: {str(e)}')
            except Exception as e:
                messages.error(request, _("خطأ في حذف التصميم: ") + str(e))
                print(f"Error deleting design {design_id}: {str(e)}")
            return redirect('dashboard:manage_designs')
        else:
            pdf_url = request.POST.get('pdf_url')
            commission_per_sale = request.POST.get('commission_per_sale')
            status = request.POST.get('status')
            designer_id = request.POST.get('designer_id')
            try:
                with transaction.atomic():
                    if design_id:
                        # تعديل تصميم موجود
                        design = get_object_or_404(Design, id=design_id)
                        old_status = design.status
                        design.pdf_url = pdf_url
                        design.commission_per_sale = Decimal(commission_per_sale)
                        design.status = status
                        design.designer = User.objects.get(id=designer_id)
                        design.save()
                        messages.success(request, _("تم تحديث التصميم بنجاح"))
                        print(f"Updated Design - ID: {design_id}, PDF URL: {pdf_url}, Commission: {commission_per_sale}, Status: {status}, Designer ID: {designer_id}")
                        if old_status != status or design_id:
                            try:
                                send_mail(
                                    'تحديث حالة التصميم',
                                    f'تفاصيل التصميم:\n'
                                    f'رقم التصميم: {design.id}\n'
                                    f'رابط PDF: {pdf_url}\n'
                                    f'العمولة لكل بيع: {commission_per_sale} جنيه\n'
                                    f'الحالة الجديدة: {design.get_status_display()}\n'
                                    f'المصمم: {design.designer.username}',
                                    settings.EMAIL_HOST_USER,
                                    [design.designer.email],
                                    fail_silently=True,
                                )
                            except Exception as e:
                                messages.warning(request, f'خطأ في إرسال إشعار للمصمم: {str(e)}')
                    else:
                        # إضافة تصميم جديد
                        design = Design.objects.create(
                            pdf_url=pdf_url,
                            commission_per_sale=Decimal(commission_per_sale),
                            status=status,
                            designer=User.objects.get(id=designer_id)
                        )
                        messages.success(request, _("تم إنشاء التصميم بنجاح"))
                        print(f"Created Design - ID: {design.id}, PDF URL: {pdf_url}, Commission: {commission_per_sale}, Status: {status}, Designer ID: {designer_id}")
                        try:
                            send_mail(
                                'إنشاء تصميم جديد',
                                f'تم إنشاء تصميم جديد:\n'
                                f'رقم التصميم: {design.id}\n'
                                f'رابط PDF: {pdf_url}\n'
                                f'العمولة لكل بيع: {commission_per_sale} جنيه\n'
                                f'الحالة: {design.get_status_display()}\n'
                                f'المصمم: {design.designer.username}',
                                settings.EMAIL_HOST_USER,
                                [design.designer.email],
                                fail_silently=True,
                            )
                        except Exception as e:
                            messages.warning(request, f'خطأ في إرسال إشعار للمصمم: {str(e)}')
            except Exception as e:
                messages.error(request, _("خطأ في إنشاء/تحديث التصميم: ") + str(e))
                print(f"Error managing design: {str(e)}")
                return redirect('dashboard:manage_designs')

    # معالجة طلب GET
    try:
        if request.GET.get('design_id'):
            design = get_object_or_404(Design, id=request.GET.get('design_id'))
    except Exception as e:
        messages.error(request, _("خطأ في تحميل التصميم: ") + str(e))
        print(f"Error loading design for edit: {str(e)}")
        design = None

    designs = Design.objects.all()
    designers = User.objects.filter(user_type='designer')
    print(f"Manage Designs - Total Designs: {designs.count()}, Total Designers: {designers.count()}")
    return render(request, 'dashboard/manage_designs.html', {
        'designs': designs,
        'designers': designers,
        'design': design
    })
@login_required
def order_stats(request):
    user = request.user
    period = request.GET.get('period', 'month')
    now = timezone.now()
    if period == '90days':
        start_date = now - timedelta(days=90)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    context = {
        'period': period,
        'stats': {},
        'income': Decimal('0.00'),
        'expenses': Decimal('0.00'),
        'net_profit': Decimal('0.00'),
        'total_withdrawals': Decimal('0.00'),
        'total_bonuses': Decimal('0.00'),
    }

    if user.is_superuser:
        orders = Order.objects.filter(created_at__gte=start_date)
        stats = {
            'pending': orders.filter(status='pending').count(),
            'shipped': orders.filter(status='shipped').count(),
            'completed': orders.filter(status='completed').count(),
            'cancelled': orders.filter(status='cancelled').count(),
            'total_orders': orders.count(),
        }
        income = orders.filter(status='completed').aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        withdrawals = WithdrawalRequest.objects.filter(
            status='approved',
            created_at__gte=start_date,
            user__user_type__in=['marketer', 'designer']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        bonuses = BonusRequest.objects.filter(
            status='approved',
            created_at__gte=start_date,
            user__user_type__in=['marketer', 'designer']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_expenses = withdrawals + bonuses
        total_withdrawals = WithdrawalRequest.objects.filter(
            status='approved',
            user__user_type__in=['marketer', 'designer']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_bonuses = BonusRequest.objects.filter(
            status='approved',
            user__user_type__in=['marketer', 'designer']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        completed_orders = orders.filter(status='completed')
        print(f"Superuser Order Stats - Username: {user.username}, Total Orders: {stats['total_orders']}, Completed Orders: {stats['completed']}, Income: {income}, Expenses: {total_expenses}, Total Withdrawals: {total_withdrawals}, Total Bonuses: {total_bonuses}, Net Profit: {income - total_expenses}")
        print(f"Completed Orders IDs and Dates: {[(order.id, order.created_at) for order in completed_orders]}")
        print(f"Start Date: {start_date}")
        
        context['stats'] = stats
        context['income'] = income
        context['expenses'] = total_expenses
        context['net_profit'] = income - total_expenses
        context['total_withdrawals'] = total_withdrawals
        context['total_bonuses'] = total_bonuses

    elif user.user_type == 'marketer':
        orders = OrderItem.objects.filter(
            marketer=user,
            order__status__in=['pending', 'shipped', 'completed', 'cancelled'],
            order__created_at__gte=start_date
        )
        total_earnings = user.total_earnings or Decimal('0.00')
        total_withdrawals = WithdrawalRequest.objects.filter(
            user=user,
            status='approved',
            created_at__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        remaining_balance = total_earnings - total_withdrawals
        remaining_balance = max(remaining_balance, Decimal('0.00'))
        
        print(f"Marketer Order Stats - Username: {user.username}, Total Earnings: {total_earnings}, Total Withdrawals: {total_withdrawals}, Remaining Balance: {remaining_balance}")
        print(f"Marketer Orders: {[(order.order.id, order.order.created_at, order.order.status) for order in orders]}")
        
        stats = {
            'pending': orders.filter(order__status='pending').count(),
            'shipped': orders.filter(order__status='shipped').count(),
            'completed': orders.filter(order__status='completed').count(),
            'cancelled': orders.filter(order__status='cancelled').count(),
            'total_orders': orders.count(),
            'total_earnings': total_earnings,
            'total_withdrawals': total_withdrawals,
            'remaining_balance': remaining_balance,
        }
        context['stats'] = stats
        context['total_earnings'] = total_earnings
        context['total_withdrawals'] = total_withdrawals
        context['remaining_balance'] = remaining_balance

    elif user.user_type == 'designer':
        orders = OrderItem.objects.filter(
            product__design__designer=user,
            product__design__status='approved',
            order__status__in=['pending', 'shipped', 'completed', 'cancelled'],
            order__created_at__gte=start_date
        )
        designs = Design.objects.filter(designer=user, created_at__gte=start_date)
        total_earnings = user.total_earnings or Decimal('0.00')
        total_withdrawals = WithdrawalRequest.objects.filter(
            user=user,
            status='approved',
            created_at__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        remaining_balance = total_earnings - total_withdrawals
        remaining_balance = max(remaining_balance, Decimal('0.00'))
        
        print(f"Designer Order Stats - Username: {user.username}, Total Designs: {designs.count()}, Total Earnings: {total_earnings}, Total Withdrawals: {total_withdrawals}, Remaining Balance: {remaining_balance}")
        print(f"Designer Orders: {[(order.order.id, order.order.created_at, order.order.status) for order in orders]}")
        
        stats = {
            'pending': orders.filter(order__status='pending').count(),
            'shipped': orders.filter(order__status='shipped').count(),
            'completed': orders.filter(order__status='completed').count(),
            'cancelled': orders.filter(order__status='cancelled').count(),
            'total_designs': designs.count(),
            'total_orders': orders.count(),
            'total_earnings': total_earnings,
            'total_withdrawals': total_withdrawals,
            'remaining_balance': remaining_balance,
        }
        context['stats'] = stats
        context['total_earnings'] = total_earnings
        context['total_withdrawals'] = total_withdrawals
        context['remaining_balance'] = remaining_balance

    return render(request, 'dashboard/order_stats.html', context)

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def update_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['pending', 'approved', 'failed']:
            withdrawal.status = new_status
            withdrawal.save()
            
            try:
                send_mail(
                    'تحديث حالة طلب السحب',
                    f'تفاصيل طلب السحب:\n'
                    f'رقم الطلب: {withdrawal.id}\n'
                    f'اسم المستخدم: {withdrawal.user.username}\n'
                    f'الاسم الكامل: {withdrawal.full_name}\n'
                    f'العنوان: {withdrawal.address}\n'
                    f'رقم الهاتف: {withdrawal.phone_number}\n'
                    f'رقم المحفظة: {withdrawal.wallet_number}\n'
                    f'المبلغ: {withdrawal.amount} جنيه\n'
                    f'الحالة الجديدة: {withdrawal.get_status_display()}',
                    settings.EMAIL_HOST_USER,
                    [withdrawal.user.email],
                    fail_silently=True,
                )
            except Exception as e:
                messages.warning(request, f'خطأ في إرسال إشعار للمستخدم: {str(e)}')
            
            messages.success(request, _("تم تحديث حالة طلب السحب بنجاح"))
        else:
            messages.error(request, _("حالة غير صالحة"))
        
        return redirect('dashboard:manage_withdrawals')
    
    return redirect('dashboard:manage_withdrawals')

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def manage_withdrawals(request):
    if request.method == 'POST':
        withdrawal_id = request.POST.get('withdrawal_id')
        new_status = request.POST.get('status')
        withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
        
        if new_status in ['pending', 'approved', 'failed']:
            old_status = withdrawal.status
            withdrawal.status = new_status
            withdrawal.save()
            
            try:
                send_mail(
                    'تحديث حالة طلب السحب',
                    f'تفاصيل طلب السحب:\n'
                    f'رقم الطلب: {withdrawal.id}\n'
                    f'اسم المستخدم: {withdrawal.user.username}\n'
                    f'الاسم الكامل: {withdrawal.full_name}\n'
                    f'العنوان: {withdrawal.address}\n'
                    f'رقم الهاتف: {withdrawal.phone_number}\n'
                    f'رقم المحفظة: {withdrawal.wallet_number}\n'
                    f'المبلغ: {withdrawal.amount} جنيه\n'
                    f'الحالة الجديدة: {withdrawal.get_status_display()}',
                    settings.EMAIL_HOST_USER,
                    [withdrawal.user.email],
                    fail_silently=True,
                )
            except Exception as e:
                messages.warning(request, f'خطأ في إرسال إشعار للمستخدم: {str(e)}')
            
            messages.success(request, _("تم تحديث حالة طلب السحب بنجاح"))
        else:
            messages.error(request, _("حالة غير صالحة"))
        
        return redirect('dashboard:manage_withdrawals')
    
    withdrawals = WithdrawalRequest.objects.all()
    print(f"Manage Withdrawals - Withdrawal Requests: {withdrawals.count()}")
    return render(request, 'dashboard/manage_withdrawals.html', {'withdrawals': withdrawals})

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def update_bonus(request, bonus_id):
    bonus = get_object_or_404(BonusRequest, id=bonus_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        bonus_amount = request.POST.get('bonus_amount')
        
        new_status = new_status.strip().lower() if new_status else ''
        if new_status == 'completed':
            new_status = 'approved'
        
        valid_statuses = ['pending', 'approved', 'rejected']
        if new_status in valid_statuses:
            old_status = bonus.status
            bonus.status = new_status
            if new_status == 'approved' and bonus_amount and old_status != 'approved':
                try:
                    bonus_amount = Decimal(bonus_amount)
                    if bonus_amount <= 0:
                        messages.error(request, _("مبلغ المكافأة يجب أن يكون أكبر من صفر"))
                        return redirect('dashboard:manage_bonuses')
                    with transaction.atomic():
                        bonus.amount = bonus_amount
                        bonus.user.total_earnings = (bonus.user.total_earnings or Decimal('0.00')) + bonus_amount
                        bonus.user.save()
                        print(f"Updated total_earnings for {bonus.user.username}: {bonus.user.total_earnings} (Bonus: {bonus.amount})")
                except (ValueError, TypeError):
                    messages.error(request, _("مبلغ المكافأة غير صالح"))
                    return redirect('dashboard:manage_bonuses')
            bonus.save()
            
            try:
                completed_orders = OrderItem.objects.filter(
                    marketer=bonus.user,
                    order__status='completed',
                    order__created_at__gte=timezone.now() - timedelta(days=30)
                ).count() if bonus.user.user_type == 'marketer' else OrderItem.objects.filter(
                    product__design__designer=bonus.user,
                    product__design__status='approved',
                    order__status='completed',
                    order__created_at__gte=timezone.now() - timedelta(days=30)
                ).count()
                send_mail(
                    'تحديث حالة طلب المكافأة',
                    f'تفاصيل طلب المكافأة:\n'
                    f'رقم الطلب: {bonus.id}\n'
                    f'اسم المستخدم: {bonus.user.username}\n'
                    f'الاسم الكامل: {bonus.full_name}\n'
                    f'عدد الطلبات المكتملة (آخر 30 يوم): {completed_orders}\n'
                    f'مبلغ المكافأة: {bonus.amount if bonus.amount else "غير محدد"} جنيه\n'
                    f'الحالة الجديدة: {bonus.get_status_display()}',
                    settings.EMAIL_HOST_USER,
                    [bonus.user.email],
                    fail_silently=True,
                )
            except Exception as e:
                messages.warning(request, f'خطأ في إرسال إشعار للمستخدم: {str(e)}')
            
            messages.success(request, _("تم تحديث حالة طلب المكافأة بنجاح"))
        else:
            messages.error(request, _("حالة غير صالحة: ") + f"{new_status}")
            print(f"Invalid status received: {new_status}")
            return redirect('dashboard:manage_bonuses')
    
    return redirect('dashboard:manage_bonuses')

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def manage_bonuses(request):
    if request.method == 'POST':
        bonus_id = request.POST.get('bonus_id')
        new_status = request.POST.get('status')
        bonus_amount = request.POST.get('bonus_amount')
        bonus = get_object_or_404(BonusRequest, id=bonus_id)
        
        new_status = new_status.strip().lower() if new_status else ''
        if new_status == 'completed':
            new_status = 'approved'
        
        valid_statuses = ['pending', 'approved', 'rejected']
        if new_status in valid_statuses:
            old_status = bonus.status
            bonus.status = new_status
            if new_status == 'approved' and bonus_amount and old_status != 'approved':
                try:
                    bonus_amount = Decimal(bonus_amount)
                    if bonus_amount <= 0:
                        messages.error(request, _("مبلغ المكافأة يجب أن يكون أكبر من صفر"))
                        return redirect('dashboard:manage_bonuses')
                    with transaction.atomic():
                        bonus.amount = bonus_amount
                        bonus.user.total_earnings = (bonus.user.total_earnings or Decimal('0.00')) + bonus.amount
                        bonus.user.save()
                        print(f"Updated total_earnings for {bonus.user.username}: {bonus.user.total_earnings} (Bonus: {bonus.amount})")
                except (ValueError, TypeError):
                    messages.error(request, _("مبلغ المكافأة غير صالح"))
                    return redirect('dashboard:manage_bonuses')
            bonus.save()
            
            try:
                completed_orders = OrderItem.objects.filter(
                    marketer=bonus.user,
                    order__status='completed',
                    order__created_at__gte=timezone.now() - timedelta(days=30)
                ).count() if bonus.user.user_type == 'marketer' else OrderItem.objects.filter(
                    product__design__designer=bonus.user,
                    product__design__status='approved',
                    order__status='completed',
                    order__created_at__gte=timezone.now() - timedelta(days=30)
                ).count()
                send_mail(
                    'تحديث حالة طلب المكافأة',
                    f'تفاصيل طلب المكافأة:\n'
                    f'رقم الطلب: {bonus.id}\n'
                    f'اسم المستخدم: {bonus.user.username}\n'
                    f'الاسم الكامل: {bonus.full_name}\n'
                    f'عدد الطلبات المكتملة (آخر 30 يوم): {completed_orders}\n'
                    f'مبلغ المكافأة: {bonus.amount if bonus.amount else "غير محدد"} جنيه\n'
                    f'الحالة الجديدة: {bonus.get_status_display()}',
                    settings.EMAIL_HOST_USER,
                    [bonus.user.email],
                    fail_silently=True,
                )
            except Exception as e:
                messages.warning(request, f'خطأ في إرسال إشعار للمستخدم: {str(e)}')
            
            messages.success(request, _("تم تحديث حالة طلب المكافأة بنجاح"))
        else:
            messages.error(request, _("حالة غير صالحة: ") + f"{new_status}")
            print(f"Invalid status received: {new_status}")
            return redirect('dashboard:manage_bonuses')
        
        return redirect('dashboard:manage_bonuses')
    
    bonuses = BonusRequest.objects.all()
    for bonus in bonuses:
        bonus.completed_orders_last_30_days = OrderItem.objects.filter(
            marketer=bonus.user,
            order__status='completed',
            order__created_at__gte=timezone.now() - timedelta(days=30)
        ).count() if bonus.user.user_type == 'marketer' else OrderItem.objects.filter(
            product__design__designer=bonus.user,
            product__design__status='approved',
            order__status='completed',
            order__created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
    
    print(f"Manage Bonuses - Bonus Requests: {bonuses.count()}")
    return render(request, 'dashboard/manage_bonuses.html', {'bonuses': bonuses})

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def search_marketer(request):
    marketer = None
    orders = []
    withdrawals = []
    bonuses = []
    stats = {}
    total_earnings = Decimal('0.00')
    total_withdrawals = Decimal('0.00')
    remaining_balance = Decimal('0.00')
    profile = None
    
    period = request.POST.get('period', 'month')
    now = timezone.now()
    if period == '90days':
        start_date = now - timedelta(days=90)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            marketer = User.objects.get(username=username, user_type='marketer')
            profile = Profile.objects.get(user=marketer)
            orders = OrderItem.objects.filter(
                marketer=marketer,
                order__status__in=['pending', 'shipped', 'completed', 'cancelled'],
                order__created_at__gte=start_date
            )
            paginator = Paginator(orders, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            withdrawals = WithdrawalRequest.objects.filter(user=marketer, created_at__gte=start_date)
            bonuses = BonusRequest.objects.filter(user=marketer, created_at__gte=start_date)
            
            total_earnings = marketer.total_earnings or Decimal('0.00')
            total_withdrawals = WithdrawalRequest.objects.filter(
                user=marketer,
                status='approved'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            remaining_balance = total_earnings - total_withdrawals
            
            stats = {
                'pending': orders.filter(order__status='pending').count(),
                'shipped': orders.filter(order__status='shipped').count(),
                'completed': orders.filter(order__status='completed').count(),
                'cancelled': orders.filter(order__status='cancelled').count(),
                'total_orders': orders.count(),
            }
            
            logger.info(f"Search Marketer - Username: {username}, Total Orders: {orders.count()}, Total Earnings: {total_earnings}, Remaining Balance: {remaining_balance}")
            logger.debug(f"Marketer Orders: {[(order.order.id, order.order.created_at, order.order.status) for order in orders]}")
            
            return render(request, 'dashboard/search_marketer.html', {
                'marketer': marketer,
                'profile': profile,
                'orders': page_obj,
                'withdrawals': withdrawals if withdrawals.exists() else None,
                'bonuses': bonuses if bonuses.exists() else None,
                'stats': stats,
                'total_earnings': total_earnings,
                'total_withdrawals': total_withdrawals,
                'remaining_balance': remaining_balance,
                'period': period,
            })
        except User.DoesNotExist:
            messages.error(request, _("المسوق غير موجود"))
            logger.error(f"Search Marketer - Username: {username} not found")
        except Profile.DoesNotExist:
            messages.error(request, _("الملف الشخصي للمسوق غير موجود"))
            logger.error(f"Search Marketer - Profile for {username} not found")
        except Exception as e:
            messages.error(request, _("خطأ في البحث عن المسوق: ") + str(e))
            logger.error(f"Error searching marketer {username}: {str(e)}")
    
    return render(request, 'dashboard/search_marketer.html', {
        'marketer': marketer,
        'profile': profile,
        'orders': orders,
        'withdrawals': withdrawals,
        'bonuses': bonuses,
        'stats': stats,
        'total_earnings': total_earnings,
        'total_withdrawals': total_withdrawals,
        'remaining_balance': remaining_balance,
        'period': period,
    })

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def update_marketer(request, username):
    marketer = get_object_or_404(User, username=username, user_type='marketer')
    try:
        profile = Profile.objects.get(user=marketer)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=marketer)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # تحديث حقول User
                email = request.POST.get('email')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                phone_number = request.POST.get('phone_number')
                total_earnings = request.POST.get('total_earnings')
                is_active = request.POST.get('is_active') == 'true'
                
                # التحقق من أن البريد الإلكتروني فريد
                if email != marketer.email and User.objects.filter(email=email).exists():
                    messages.error(request, _("البريد الإلكتروني مستخدم بالفعل"))
                    logger.error(f"Update Marketer - Username: {username}, Email {email} already exists")
                    return redirect('dashboard:search_marketer')
                
                # التحقق من أن إجمالي الأرباح رقم موجب
                if total_earnings and Decimal(total_earnings) < 0:
                    messages.error(request, _("إجمالي الأرباح يجب أن يكون رقمًا موجبًا"))
                    logger.error(f"Update Marketer - Username: {username}, Invalid total_earnings: {total_earnings}")
                    return redirect('dashboard:search_marketer')
                
                marketer.email = email
                marketer.first_name = first_name
                marketer.last_name = last_name
                marketer.phone_number = phone_number
                if total_earnings:
                    marketer.total_earnings = Decimal(total_earnings)
                marketer.is_active = is_active
                marketer.save()
                
                # تحديث حقول Profile
                profile.full_name = request.POST.get('full_name')
                profile.date_of_birth = request.POST.get('date_of_birth') or None
                profile.profile_picture = request.POST.get('profile_picture')
                profile.wallet_number = request.POST.get('wallet_number')
                profile.save()
                
                # إرسال إشعار بريد إلكتروني
                try:
                    send_mail(
                        'تحديث بيانات المسوق',
                        f'عزيزي {marketer.username},\n'
                        f'تم تحديث بياناتك في النظام:\n'
                        f'البريد الإلكتروني: {marketer.email}\n'
                        f'الاسم الأول: {marketer.first_name or "غير محدد"}\n'
                        f'الاسم الأخير: {marketer.last_name or "غير محدد"}\n'
                        f'رقم الهاتف: {marketer.phone_number or "غير محدد"}\n'
                        f'الاسم الكامل: {profile.full_name or "غير محدد"}\n'
                        f'تاريخ الميلاد: {profile.date_of_birth or "غير محدد"}\n'
                        f'رابط صورة الملف الشخصي: {profile.profile_picture or "غير محدد"}\n'
                        f'رقم المحفظة: {profile.wallet_number or "غير محدد"}\n'
                        f'إجمالي الأرباح: {marketer.total_earnings or "0.00"} جنيه\n'
                        f'حالة الحساب: {"مفعل" if marketer.is_active else "غير مفعل"}\n'
                        f'يرجى التواصل مع الإدارة إذا كنت بحاجة إلى مزيد من المعلومات.',
                        settings.EMAIL_HOST_USER,
                        [marketer.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    messages.warning(request, f'خطأ في إرسال إشعار للمسوق: {str(e)}')
                    logger.error(f"Error sending email to marketer {marketer.email}: {str(e)}")
                
                messages.success(request, _("تم تحديث بيانات المسوق بنجاح"))
                logger.info(f"Updated Marketer - Username: {username}, Email: {email}, Total Earnings: {marketer.total_earnings}, Is Active: {marketer.is_active}")
                return redirect('dashboard:search_marketer')
        except Exception as e:
            messages.error(request, _("خطأ في تحديث بيانات المسوق: ") + str(e))
            logger.error(f"Error updating marketer {username}: {str(e)}")
    
    return redirect('dashboard:search_marketer')

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def delete_marketer(request, username):
    marketer = get_object_or_404(User, username=username, user_type='marketer')
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # إرسال إشعار بريد إلكتروني قبل الحذف
                try:
                    send_mail(
                        'حذف حساب المسوق',
                        f'عزيزي {marketer.username},\n'
                        f'تم حذف حسابك من النظام بنجاح.\n'
                        f'إذا كنت تعتقد أن هذا خطأ، يرجى التواصل مع الإدارة فوراً.',
                        settings.EMAIL_HOST_USER,
                        [marketer.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    messages.warning(request, f'خطأ في إرسال إشعار للمسوق: {str(e)}')
                    logger.error(f"Error sending email to marketer {marketer.email}: {str(e)}")
                
                # حذف البيانات المرتبطة
                OrderItem.objects.filter(marketer=marketer).delete()
                WithdrawalRequest.objects.filter(user=marketer).delete()
                BonusRequest.objects.filter(user=marketer).delete()
                Profile.objects.filter(user=marketer).delete()
                marketer.delete()
                
                messages.success(request, _("تم حذف المسوق وجميع بياناته بنجاح"))
                logger.info(f"Deleted Marketer - Username: {username}")
        except Exception as e:
            messages.error(request, _("خطأ في حذف المسوق: ") + str(e))
            logger.error(f"Error deleting marketer {username}: {str(e)}")
    
    return redirect('dashboard:search_marketer')


@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def search_designer(request):
    designer = None
    designs = []
    orders = []
    withdrawals = []
    bonuses = []
    stats = {}
    total_earnings = Decimal('0.00')
    remaining_balance = Decimal('0.00')
    profile = None
    
    period = request.POST.get('period', 'month')
    now = timezone.now()
    if period == '90days':
        start_date = now - timedelta(days=90)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            designer = User.objects.get(username=username, user_type='designer')
            profile = Profile.objects.get(user=designer)
            designs = Design.objects.filter(designer=designer, created_at__gte=start_date)
            orders = OrderItem.objects.filter(
                product__design__designer=designer,
                product__design__status='approved',
                order__created_at__gte=start_date
            )
            paginator = Paginator(orders, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            withdrawals = WithdrawalRequest.objects.filter(user=designer, created_at__gte=start_date)
            bonuses = BonusRequest.objects.filter(user=designer, created_at__gte=start_date)
            
            total_earnings = designer.total_earnings or Decimal('0.00')
            total_withdrawals = WithdrawalRequest.objects.filter(
                user=designer,
                status='approved'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            remaining_balance = total_earnings - total_withdrawals
            
            stats = {
                'total_designs': designs.count(),
                'pending': orders.filter(order__status='pending').count(),
                'shipped': orders.filter(order__status='shipped').count(),
                'completed': orders.filter(order__status='completed').count(),
                'cancelled': orders.filter(order__status='cancelled').count(),
                'total_orders': orders.count(),
            }
            
            logger.info(f"Search Designer - Username: {username}, Total Designs: {designs.count()}, Total Orders: {orders.count()}, Total Earnings: {total_earnings}, Remaining Balance: {remaining_balance}")
            logger.debug(f"Designer Orders: {[(order.order.id, order.order.created_at, order.order.status) for order in orders]}")
            
            return render(request, 'dashboard/search_designer.html', {
                'designer': designer,
                'profile': profile,
                'designs': designs,
                'orders': page_obj,
                'withdrawals': withdrawals if withdrawals.exists() else None,
                'bonuses': bonuses if bonuses.exists() else None,
                'stats': stats,
                'total_earnings': total_earnings,
                'remaining_balance': remaining_balance,
                'period': period,
            })
        except User.DoesNotExist:
            messages.error(request, _("المصمم غير موجود"))
            logger.error(f"Search Designer - Username: {username} not found")
        except Profile.DoesNotExist:
            messages.error(request, _("الملف الشخصي للمصمم غير موجود"))
            logger.error(f"Search Designer - Profile for {username} not found")
        except Exception as e:
            messages.error(request, _("خطأ في البحث عن المصمم: ") + str(e))
            logger.error(f"Error searching designer {username}: {str(e)}")
    
    return render(request, 'dashboard/search_designer.html', {
        'designer': designer,
        'profile': profile,
        'designs': designs,
        'orders': orders,
        'withdrawals': withdrawals,
        'bonuses': bonuses,
        'stats': stats,
        'total_earnings': total_earnings,
        'remaining_balance': remaining_balance,
        'period': period,
    })

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def update_designer(request, username):
    designer = get_object_or_404(User, username=username, user_type='designer')
    try:
        profile = Profile.objects.get(user=designer)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=designer)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # تحديث حقول User
                email = request.POST.get('email')
                phone_number = request.POST.get('phone_number')
                total_earnings = request.POST.get('total_earnings')
                
                # التحقق من أن البريد الإلكتروني فريد
                if email != designer.email and User.objects.filter(email=email).exists():
                    messages.error(request, _("البريد الإلكتروني مستخدم بالفعل"))
                    logger.error(f"Update Designer - Username: {username}, Email {email} already exists")
                    return redirect('dashboard:search_designer')
                
                designer.email = email
                designer.phone_number = phone_number
                if total_earnings:
                    designer.total_earnings = Decimal(total_earnings)
                designer.save()
                
                # تحديث حقول Profile
                profile.full_name = request.POST.get('full_name')
                profile.date_of_birth = request.POST.get('date_of_birth') or None
                profile.profile_picture = request.POST.get('profile_picture')
                profile.wallet_number = request.POST.get('wallet_number')
                profile.save()
                
                # إرسال إشعار بريد إلكتروني
                try:
                    send_mail(
                        'تحديث بيانات المصمم',
                        f'عزيزي {designer.username},\n'
                        f'تم تحديث بياناتك في النظام:\n'
                        f'البريد الإلكتروني: {designer.email}\n'
                        f'رقم الهاتف: {designer.phone_number or "غير محدد"}\n'
                        f'الاسم الكامل: {profile.full_name or "غير محدد"}\n'
                        f'تاريخ الميلاد: {profile.date_of_birth or "غير محدد"}\n'
                        f'رابط صورة الملف الشخصي: {profile.profile_picture or "غير محدد"}\n'
                        f'رقم المحفظة: {profile.wallet_number or "غير محدد"}\n'
                        f'إجمالي الأرباح: {designer.total_earnings or "0.00"} جنيه\n'
                        f'يرجى التواصل مع الإدارة إذا كنت بحاجة إلى مزيد من المعلومات.',
                        settings.EMAIL_HOST_USER,
                        [designer.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    messages.warning(request, f'خطأ في إرسال إشعار للمصمم: {str(e)}')
                    logger.error(f"Error sending email to designer {designer.email}: {str(e)}")
                
                messages.success(request, _("تم تحديث بيانات المصمم بنجاح"))
                logger.info(f"Updated Designer - Username: {username}, Email: {email}, Total Earnings: {designer.total_earnings}")
                return redirect('dashboard:search_designer')
        except Exception as e:
            messages.error(request, _("خطأ في تحديث بيانات المصمم: ") + str(e))
            logger.error(f"Error updating designer {username}: {str(e)}")
    
    return redirect('dashboard:search_designer')

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def delete_designer(request, username):
    designer = get_object_or_404(User, username=username, user_type='designer')
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # إرسال إشعار بريد إلكتروني قبل الحذف
                try:
                    send_mail(
                        'حذف حساب المصمم',
                        f'عزيزي {designer.username},\n'
                        f'تم حذف حسابك من النظام بنجاح.\n'
                        f'إذا كنت تعتقد أن هذا خطأ، يرجى التواصل مع الإدارة فوراً.',
                        settings.EMAIL_HOST_USER,
                        [designer.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    messages.warning(request, f'خطأ في إرسال إشعار للمصمم: {str(e)}')
                    logger.error(f"Error sending email to designer {designer.email}: {str(e)}")
                
                # حذف البيانات المرتبطة
                Design.objects.filter(designer=designer).delete()
                OrderItem.objects.filter(product__design__designer=designer).delete()
                WithdrawalRequest.objects.filter(user=designer).delete()
                BonusRequest.objects.filter(user=designer).delete()
                Profile.objects.filter(user=designer).delete()
                designer.delete()
                
                messages.success(request, _("تم حذف المصمم وجميع بياناته بنجاح"))
                logger.info(f"Deleted Designer - Username: {username}")
        except Exception as e:
            messages.error(request, _("خطأ في حذف المصمم: ") + str(e))
            logger.error(f"Error deleting designer {username}: {str(e)}")
    
    return redirect('dashboard:search_designer')

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def update_order_item(request, order_item_id):
    order_item = get_object_or_404(OrderItem, id=order_item_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['pending', 'shipped', 'completed', 'cancelled']:
            old_status = order_item.order.status
            order_item.order.status = new_status
            order_item.order.save()
            
            if new_status == 'completed' and old_status != 'completed':
                if order_item.marketer:
                    with transaction.atomic():
                        order_item.marketer.total_earnings += order_item.marketer_commission * Decimal(str(order_item.quantity))
                        order_item.marketer.save()
                        print(f"Updated total_earnings for marketer {order_item.marketer.username}: {order_item.marketer.total_earnings} (Commission: {order_item.marketer_commission * Decimal(str(order_item.quantity))})")
                if order_item.product.design_ownership == 'designer' and order_item.product.design and order_item.product.designer:
                    with transaction.atomic():
                        order_item.product.designer.total_earnings += order_item.designer_commission * Decimal(str(order_item.quantity))
                        order_item.product.designer.save()
                        print(f"Updated total_earnings for designer {order_item.product.designer.username}: {order_item.product.designer.total_earnings} (Commission: {order_item.designer_commission * Decimal(str(order_item.quantity))})")
            
            try:
                if order_item.marketer:
                    send_mail(
                        'تحديث حالة الطلب',
                        f'تفاصيل الطلب:\n'
                        f'رقم الطلب: {order_item.order.id}\n'
                        f'اسم العميل: {order_item.order.customer_name}\n'
                        f'الحالة الجديدة: {order_item.order.get_status_display()}',
                        settings.EMAIL_HOST_USER,
                        [order_item.marketer.email],
                        fail_silently=True,
                    )
                if order_item.product.design_ownership == 'designer' and order_item.product.design and order_item.product.designer:
                    send_mail(
                        'تحديث حالة الطلب',
                        f'تفاصيل الطلب:\n'
                        f'رقم الطلب: {order_item.order.id}\n'
                        f'اسم العميل: {order_item.order.customer_name}\n'
                        f'الحالة الجديدة: {order_item.order.get_status_display()}',
                        settings.EMAIL_HOST_USER,
                        [order_item.product.designer.email],
                        fail_silently=True,
                    )
            except Exception as e:
                messages.warning(request, f'خطأ في إرسال إشعار: {str(e)}')
            
            messages.success(request, _("تم تحديث حالة الطلب بنجاح"))
            print(f"Updated Order Item - Order ID: {order_item.order.id}, New Status: {new_status}")
        else:
            messages.error(request, _("حالة غير صالحة"))
        
        return redirect('dashboard:search_designer')
    
    return redirect('dashboard:search_designer')

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def delete_order_item(request, order_item_id):
    order_item = get_object_or_404(OrderItem, id=order_item_id)
    if request.method == 'POST':
        try:
            order_id = order_item.order.id
            order_item.delete()
            messages.success(request, _("تم حذف عنصر الطلب بنجاح"))
            print(f"Deleted Order Item - Order ID: {order_id}, Item ID: {order_item_id}")
        except Exception as e:
            messages.error(request, _("خطأ في حذف عنصر الطلب: ") + str(e))
            print(f"Error deleting order item {order_item_id}: {str(e)}")
        
        return redirect('dashboard:search_designer')
    
    return redirect('dashboard:search_designer')

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def delete_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    if request.method == 'POST':
        try:
            withdrawal.delete()
            messages.success(request, _("تم حذف طلب السحب بنجاح"))
            print(f"Deleted Withdrawal - ID: {withdrawal_id}")
        except Exception as e:
            messages.error(request, _("خطأ في حذف طلب السحب: ") + str(e))
            print(f"Error deleting withdrawal {withdrawal_id}: {str(e)}")
        
        return redirect('dashboard:search_designer')
    
    return redirect('dashboard:search_designer')

@login_required
@user_passes_test(user_is_superuser, login_url='/dashboard/')
def delete_bonus(request, bonus_id):
    bonus = get_object_or_404(BonusRequest, id=bonus_id)
    if request.method == 'POST':
        try:
            if bonus.status == 'approved' and bonus.amount:
                with transaction.atomic():
                    bonus.user.total_earnings -= bonus.amount
                    bonus.user.save()
                    print(f"Updated total_earnings for {bonus.user.username}: {bonus.user.total_earnings} (Removed Bonus: {bonus.amount})")
            bonus.delete()
            messages.success(request, _("تم حذف طلب المكافأة بنجاح"))
            print(f"Deleted Bonus - ID: {bonus_id}")
        except Exception as e:
            messages.error(request, _("خطأ في حذف طلب المكافأة: ") + str(e))
            print(f"Error deleting bonus {bonus_id}: {str(e)}")
        
        return redirect('dashboard:manage_bonuses')
    
    return redirect('dashboard:manage_bonuses')
@login_required
def set_theme(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        theme = data.get('theme', 'light-mode')
        request.session['theme'] = theme
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import translation
from django.conf import settings

@csrf_exempt
def set_language(request, lang_code):
    """
    View to handle language switching via POST request.
    """
    if request.method == 'POST':
        if lang_code in [code for code, _ in settings.LANGUAGES]:
            translation.activate(lang_code)
            request.session['_language'] = lang_code  # Use '_language' as the session key
            return JsonResponse({'status': 'success', 'language': lang_code})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid language code'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

from django.shortcuts import render
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

def about_us(request):
    """
    عرض صفحة "من نحن".
    """
    return render(request, 'dashboard/about_us.html')

def contact_us(request):
    """
    عرض صفحة "تواصل معنا" ومعالجة نموذج التواصل.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # هنا ممكن تضيف منطق معالجة البيانات (مثل إرسال بريد إلكتروني أو حفظ البيانات)
        # لكن حاليًا هنعرض بس رسالة نجاح
        messages.success(request, _('تم إرسال رسالتك بنجاح! سنتواصل معك قريبًا.'))
        return redirect('dashboard:contact_us')
    
    return render(request, 'dashboard/contact_us.html')

@login_required
def top_performers(request):
    period = request.GET.get('period', 'month')
    now = timezone.now()
    
    # تحديد الفترة الزمنية
    if period == '90days':
        start_date = now - timedelta(days=90)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:  # default to month
        start_date = now - timedelta(days=30)
    
    # أفضل 10 مسوقين بناءً على عدد الطلبات المكتملة
    top_marketers = OrderItem.objects.filter(
        marketer__isnull=False,
        order__status='completed',
        order__created_at__gte=start_date
    ).values('marketer__username').annotate(
        total_orders=Count('order', distinct=True),
        total_earnings=Sum(models.F('marketer_commission') * models.F('quantity'))
    ).order_by('-total_orders')[:10]
    
    # أفضل 10 مصممين بناءً على عدد المنتجات المباعة من تصميماتهم
    top_designers = OrderItem.objects.filter(
        product__design__designer__isnull=False,
        product__design__status='approved',
        order__status='completed',
        order__created_at__gte=start_date
    ).values('product__design__designer__username').annotate(
        total_products_sold=Sum('quantity'),
        total_earnings=Sum(models.F('designer_commission') * models.F('quantity'))
    ).order_by('-total_products_sold')[:10]
    
    # Logging
    logger.info(f"Top Performers - Period: {period}, Start Date: {start_date}, Top Marketers: {len(top_marketers)}, Top Designers: {len(top_designers)}")
    logger.debug(f"Top Marketers: {top_marketers}")
    logger.debug(f"Top Designers: {top_designers}")
    
    return render(request, 'dashboard/top_performers.html', {
        'top_marketers': top_marketers,
        'top_designers': top_designers,
        'period': period,
    })

