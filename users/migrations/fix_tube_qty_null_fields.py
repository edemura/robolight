from django.db import migrations, models

def set_default_values(apps, schema_editor):
    Tube_qty = apps.get_model('users', 'Tube_qty')
    # Update any null values to their defaults
    Tube_qty.objects.filter(tube_qty__isnull=True).update(tube_qty=1)
    Tube_qty.objects.filter(order_id__isnull=True).delete()  # Remove orphaned records
    Tube_qty.objects.filter(tube_type_id__isnull=True).delete()  # Remove invalid records

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),  # Make sure to replace with your actual last migration
    ]

    operations = [
        # First run the function to set default values
        migrations.RunPython(set_default_values),

        # Then modify the fields to be non-nullable
        migrations.AlterField(
            model_name='tube_qty',
            name='order_id',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                to='users.Orders',
                verbose_name='Номер заказа',
                related_name='tubes'
            ),
        ),
        migrations.AlterField(
            model_name='tube_qty',
            name='tube_type_id',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                to='users.TubeType',
                verbose_name='Вид пробирки'
            ),
        ),
        migrations.AlterField(
            model_name='tube_qty',
            name='tube_qty',
            field=models.IntegerField(
                default=1,
                verbose_name='Количество'
            ),
        ),
    ] 