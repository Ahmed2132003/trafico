from django.db import migrations
from decimal import Decimal

def populate_governorates(apps, schema_editor):
    Governorate = apps.get_model('products', 'Governorate')
    governorates_data = [
        {'name': 'القاهرة', 'shipping_cost': Decimal('50.00')},
        {'name': 'الجيزة', 'shipping_cost': Decimal('50.00')},
        {'name': 'الإسكندرية', 'shipping_cost': Decimal('60.00')},
        {'name': 'الدقهلية', 'shipping_cost': Decimal('60.00')},
        {'name': 'الشرقية', 'shipping_cost': Decimal('60.00')},
        {'name': 'المنوفية', 'shipping_cost': Decimal('60.00')},
        {'name': 'القليوبية', 'shipping_cost': Decimal('50.00')},
        {'name': 'البحيرة', 'shipping_cost': Decimal('60.00')},
        {'name': 'الغربية', 'shipping_cost': Decimal('60.00')},
        {'name': 'بورسعيد', 'shipping_cost': Decimal('60.00')},
        {'name': 'دمياط', 'shipping_cost': Decimal('60.00')},
        {'name': 'الإسماعيلية', 'shipping_cost': Decimal('60.00')},
        {'name': 'السويس', 'shipping_cost': Decimal('60.00')},
        {'name': 'كفر الشيخ', 'shipping_cost': Decimal('60.00')},
        {'name': 'الفيوم', 'shipping_cost': Decimal('60.00')},
        {'name': 'بني سويف', 'shipping_cost': Decimal('60.00')},
        {'name': 'المنيا', 'shipping_cost': Decimal('70.00')},
        {'name': 'أسيوط', 'shipping_cost': Decimal('70.00')},
        {'name': 'سوهاج', 'shipping_cost': Decimal('70.00')},
        {'name': 'قنا', 'shipping_cost': Decimal('70.00')},
        {'name': 'أسوان', 'shipping_cost': Decimal('70.00')},
        {'name': 'الأقصر', 'shipping_cost': Decimal('70.00')},
        {'name': 'البحر الأحمر', 'shipping_cost': Decimal('70.00')},
        {'name': 'الوادي الجديد', 'shipping_cost': Decimal('70.00')},
        {'name': 'مطروح', 'shipping_cost': Decimal('70.00')},
        {'name': 'شمال سيناء', 'shipping_cost': Decimal('70.00')},
        {'name': 'جنوب سيناء', 'shipping_cost': Decimal('70.00')},
    ]
    for gov in governorates_data:
        Governorate.objects.get_or_create(name=gov['name'], defaults={'shipping_cost': gov['shipping_cost']})

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0001_initial'),  # تأكد إن اسم الميجريشن الأولي صحيح
    ]

    operations = [
        migrations.RunPython(populate_governorates),
    ]