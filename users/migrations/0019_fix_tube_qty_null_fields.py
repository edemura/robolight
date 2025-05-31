from django.db import migrations, models
import logging
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def backup_m2m_data(apps, schema_editor):
    try:
        Orders = apps.get_model('users', 'Orders')
        backup_data = []
        
        # Create backup directory if it doesn't exist
        backup_dir = Path('migrations_backup')
        backup_dir.mkdir(exist_ok=True)
        
        # Backup each order's M2M relationships
        for order in Orders.objects.all():
            order_data = {
                'order_id': order.id,
                'sequence_id': order.sequence_id_id if order.sequence_id else None,
                'create_datetime': order.create_datetime.isoformat() if order.create_datetime else None,
                'total_tubes_qty': order.total_tubes_qty,
                'tubes': [
                    {
                        'tube_id': tube.id,
                        'tube_type_id': tube.tube_type_id_id,
                        'tube_qty': tube.tube_qty
                    }
                    for tube in order.tubes.all()
                ]
            }
            backup_data.append(order_data)
        
        # Save backup to file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'orders_tubes_backup_{timestamp}.json'
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"M2M relationship backup created at {backup_file}")
        logger.info(f"Backed up {len(backup_data)} orders with their tube relationships")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create M2M backup: {str(e)}")
        raise

def validate_m2m_data(apps, schema_editor):
    try:
        Orders = apps.get_model('users', 'Orders')
        Tube_qty = apps.get_model('users', 'Tube_qty')
        
        # Validation statistics
        stats = {
            'total_orders': Orders.objects.count(),
            'orders_with_tubes': 0,
            'total_tube_relations': 0,
            'orders_without_tubes': 0,
            'invalid_tube_refs': 0,
            'inconsistent_quantities': 0
        }
        
        # Validate each order
        for order in Orders.objects.all():
            tubes = order.tubes.all()
            tube_count = tubes.count()
            stats['total_tube_relations'] += tube_count
            
            if tube_count > 0:
                stats['orders_with_tubes'] += 1
                
                # Validate tube quantities match total
                total_qty = sum(tube.tube_qty for tube in tubes if tube.tube_qty is not None)
                if total_qty != order.total_tubes_qty:
                    stats['inconsistent_quantities'] += 1
                    logger.warning(
                        f"Order {order.id} has inconsistent quantities: "
                        f"sum of tubes ({total_qty}) != total_tubes_qty ({order.total_tubes_qty})"
                    )
            else:
                stats['orders_without_tubes'] += 1
                logger.warning(f"Order {order.id} has no associated tubes")
        
        # Check for orphaned Tube_qty records
        orphaned_tubes = Tube_qty.objects.filter(order_id__isnull=True).count()
        if orphaned_tubes > 0:
            stats['invalid_tube_refs'] = orphaned_tubes
            logger.warning(f"Found {orphaned_tubes} orphaned Tube_qty records")
        
        # Log validation results
        logger.info("M2M Relationship Validation Results:")
        logger.info(f"Total Orders: {stats['total_orders']}")
        logger.info(f"Orders with tubes: {stats['orders_with_tubes']}")
        logger.info(f"Orders without tubes: {stats['orders_without_tubes']}")
        logger.info(f"Total tube relations: {stats['total_tube_relations']}")
        logger.info(f"Invalid tube references: {stats['invalid_tube_refs']}")
        logger.info(f"Orders with inconsistent quantities: {stats['inconsistent_quantities']}")
        
        # Determine if validation passed
        has_errors = (
            stats['invalid_tube_refs'] > 0 or
            stats['inconsistent_quantities'] > 0
        )
        
        if has_errors:
            logger.error("Validation failed! Please check the logs and fix data inconsistencies.")
            raise Exception("Data validation failed")
        
        return True
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise

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
        # First validate and backup M2M data
        migrations.RunPython(
            validate_m2m_data,
            reverse_code=reverse_migration,
            elidable=False
        ),
        migrations.RunPython(
            backup_m2m_data,
            reverse_code=reverse_migration,
            elidable=False
        ),
        
        # Then remove the M2M field from Orders
        migrations.RemoveField(
            model_name='orders',
            name='tubes',
        ),

        migrations.RunPython(
            set_default_values,
            reverse_code=reverse_migration,
            elidable=False
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