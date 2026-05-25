from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("urls_manager", "0004_add_ownership_status_nullable"),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE "urls_manager_urlasset" ALTER COLUMN "ownership_verification_method" DROP NOT NULL;',
            reverse_sql='ALTER TABLE "urls_manager_urlasset" ALTER COLUMN "ownership_verification_method" SET NOT NULL;',
        ),
    ]