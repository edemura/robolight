from django.db import migrations

def create_task_sources(apps, schema_editor):
    Task_source = apps.get_model('users', 'Task_source')
    
    # Create initial sources
    sources = [
        "Ручной ввод",
        "JSON API",
        "Форма заказа",
        "Внешняя система"
    ]
    
    for source_name in sources:
        Task_source.objects.get_or_create(source_name=source_name)

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0019_fix_tube_qty_null_fields'),
    ]

    operations = [
        migrations.RunPython(create_task_sources),
    ] 