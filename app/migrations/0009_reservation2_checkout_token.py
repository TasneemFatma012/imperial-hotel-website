import uuid

from django.db import migrations, models


def populate_checkout_tokens(apps, schema_editor):
    Reservation = apps.get_model("app", "reservation2")
    database = schema_editor.connection.alias
    for reservation in Reservation.objects.using(database).filter(
        checkout_token__isnull=True
    ).iterator():
        reservation.checkout_token = uuid.uuid4()
        reservation.save(update_fields=("checkout_token",), using=database)


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0008_reservation2_amount_paise_reservation2_checkout_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation2",
            name="checkout_token",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.RunPython(populate_checkout_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="reservation2",
            name="checkout_token",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]
