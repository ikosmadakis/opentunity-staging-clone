from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0011_remove_inverterspecs_current_dc_nom_and_more'),
    ]

    operations = [
        # AC voltages
        migrations.RenameField(
            model_name='inverterspecs',
            old_name='voltage_ac_l1_nom',
            new_name='nominal_ac_voltage_l1',
        ),
        migrations.RenameField(
            model_name='inverterspecs',
            old_name='voltage_ac_l2_nom',
            new_name='nominal_ac_voltage_l2',
        ),
        migrations.RenameField(
            model_name='inverterspecs',
            old_name='voltage_ac_l3_nom',
            new_name='nominal_ac_voltage_l3',
        ),
        # AC currents
        migrations.RenameField(
            model_name='inverterspecs',
            old_name='current_ac_l1_nom',
            new_name='nominal_ac_current_l1',
        ),
        migrations.RenameField(
            model_name='inverterspecs',
            old_name='current_ac_l2_nom',
            new_name='nominal_ac_current_l2',
        ),
        migrations.RenameField(
            model_name='inverterspecs',
            old_name='current_ac_l3_nom',
            new_name='nominal_ac_current_l3',
        ),
    ]
