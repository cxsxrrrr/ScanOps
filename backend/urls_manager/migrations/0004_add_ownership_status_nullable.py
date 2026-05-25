"""Add ownership_status field and relax NOT NULL constraint."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("urls_manager", "0003_add_ownership_failure_reason_nullable"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "DO $$\n"
                        "BEGIN\n"
                        "    IF EXISTS (\n"
                        "        SELECT 1\n"
                        "        FROM information_schema.columns\n"
                        "        WHERE table_name = 'urls_manager_urlasset'\n"
                        "          AND column_name = 'ownership_status'\n"
                        "    ) THEN\n"
                        "        ALTER TABLE urls_manager_urlasset\n"
                        "            ALTER COLUMN ownership_status DROP NOT NULL;\n"
                        "    ELSE\n"
                        "        ALTER TABLE urls_manager_urlasset\n"
                        "            ADD COLUMN ownership_status varchar(50);\n"
                        "    END IF;\n"
                        "END $$;\n"
                    ),
                    reverse_sql=(
                        "DO $$\n"
                        "BEGIN\n"
                        "    IF EXISTS (\n"
                        "        SELECT 1\n"
                        "        FROM information_schema.columns\n"
                        "        WHERE table_name = 'urls_manager_urlasset'\n"
                        "          AND column_name = 'ownership_status'\n"
                        "    ) THEN\n"
                        "        ALTER TABLE urls_manager_urlasset\n"
                        "            DROP COLUMN ownership_status;\n"
                        "    END IF;\n"
                        "END $$;\n"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="urlasset",
                    name="ownership_status",
                    field=models.CharField(
                        max_length=50,
                        null=True,
                        blank=True,
                    ),
                ),
            ],
        ),
    ]
