from django.db import migrations, models
import logging

logger = logging.getLogger(__name__)

def set_default_values(apps, schema_editor):
    try:
        Tube_qty = apps.get_model('users', 'Tube_qty')
        # Log initial counts
        initial_count = Tube_qty.objects.count()
        null_qty_count = Tube_qty.objects.filter(tube_qty__isnull=True).count()
        null_order_count = Tube_qty.objects.filter(order_id__isnull=True).count()
        null_type_count = Tube_qty.objects.filter(tube_type_id__isnull=True).count()

        logger.info(f"Starting migration with {initial_count} total records")
        logger.info(f"Found {null_qty_count} records with null tube_qty")
        logger.info(f"Found {null_order_count} records with null order_id")
        logger.info(f"Found {null_type_count} records with null tube_type_id")

        # Update any null values to their defaults
        Tube_qty.objects.filter(tube_qty__isnull=True).update(tube_qty=1)
        Tube_qty.objects.filter(order_id__isnull=True).delete()  # Remove orphaned records
        Tube_qty.objects.filter(tube_type_id__isnull=True).delete()  # Remove invalid records

        # Log final counts
        final_count = Tube_qty.objects.count()
        logger.info(f"Migration completed. {initial_count - final_count} records were removed")
        logger.info(f"Final record count: {final_count}")

    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise

def reverse_migration(apps, schema_editor):
    # No reverse migration needed as we're just cleaning up data
    pass

class Migration(migrations.Migration):
    atomic = True  # Ensures the migration runs in a transaction

    dependencies = [
        ('users', '0018_post_data'),
    ]

    operations = [
        migrations.RunPython(
            set_default_values,
            reverse_code=reverse_migration,
            elidable=False  # This migration cannot be optimized away
        ),

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