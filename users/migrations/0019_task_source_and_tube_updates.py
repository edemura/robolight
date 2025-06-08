from django.db import migrations, models
import django.db.models.deletion

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

def set_default_values(apps, schema_editor):
    Tube_qty = apps.get_model('users', 'Tube_qty')
    
    # Update any null values to their defaults
    Tube_qty.objects.filter(tube_qty__isnull=True).update(tube_qty=1)
    Tube_qty.objects.filter(order_id__isnull=True).delete()  # Remove orphaned records
    Tube_qty.objects.filter(tube_type_id__isnull=True).delete()  # Remove invalid records

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0018_post_data'),
    ]

    operations = [
        # Set up the ForeignKey relationships for Tube_qty
        migrations.AlterField(
            model_name='tube_qty',
            name='order_id',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='users.Orders',
                verbose_name='Номер заказа',
                related_name='tubes'
            ),
        ),
        migrations.AlterField(
            model_name='tube_qty',
            name='tube_type_id',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='users.TubeType',
                verbose_name='Вид пробирки'
            ),
        ),
        migrations.AlterField(
            model_name='tube_qty',
            name='tube_qty',
            field=models.IntegerField(default=1, verbose_name='Количество'),
        ),

        # Create Task_source model
        migrations.CreateModel(
            name='Task_source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_name', models.CharField(max_length=255, verbose_name='Наименование источника')),
            ],
            options={
                'verbose_name': 'Источник заданий',
                'verbose_name_plural': 'Источники заданий',
            },
        ),

        # Add task_source field to Robo7Task
        migrations.AddField(
            model_name='robo7task',
            name='task_source',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.task_source', verbose_name='Источник задания'),
        ),

        # Set default values and create initial task sources
        migrations.RunPython(set_default_values),
        migrations.RunPython(create_task_sources),
    ] 