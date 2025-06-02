from django.db import migrations

def create_initial_task_sources(apps, schema_editor):
    # Get the historical version of the model
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

def remove_initial_task_sources(apps, schema_editor):
    # Get the historical version of the model
    Task_source = apps.get_model('users', 'Task_source')
    
    # Remove the initial sources
    Task_source.objects.filter(source_name__in=[
        "Ручной ввод",
        "JSON API",
        "Форма заказа",
        "Внешняя система"
    ]).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0019_fix_tube_qty_null_fields'),  # Adjust this to your last migration
    ]

    operations = [
        migrations.RunPython(
            create_initial_task_sources,
            remove_initial_task_sources
        )
    ] 