from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("urls_manager", "0004_add_ownership_status_nullable"),
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
                        "          AND column_name = 'ownership_verification_method'\n"
                        "    ) THEN\n"
                        "        ALTER TABLE urls_manager_urlasset\n"
                        "            ALTER COLUMN ownership_verification_method DROP NOT NULL;\n"
                        "    ELSE\n"
                        "        ALTER TABLE urls_manager_urlasset\n"
                        "            ADD COLUMN ownership_verification_method varchar(255);\n"
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
                        "          AND column_name = 'ownership_verification_method'\n"
                        "    ) THEN\n"
                        "        ALTER TABLE urls_manager_urlasset\n"
                        "            DROP COLUMN ownership_verification_method;\n"
                        "    END IF;\n"
                        "END $$;\n"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="urlasset",
                    name="ownership_verification_method",
                    field=models.CharField(
                        max_length=255,
                        null=True,
                        blank=True,
                    ),
                ),
            ],
        ),
    ]