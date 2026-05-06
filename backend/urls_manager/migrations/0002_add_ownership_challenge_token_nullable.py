"""Add ownership_challenge_token field and relax NOT NULL constraint."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("urls_manager", "0001_initial"),
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
                        "          AND column_name = 'ownership_challenge_token'\n"
                        "    ) THEN\n"
                        "        ALTER TABLE urls_manager_urlasset\n"
                        "            ALTER COLUMN ownership_challenge_token DROP NOT NULL;\n"
                        "    ELSE\n"
                        "        ALTER TABLE urls_manager_urlasset\n"
                        "            ADD COLUMN ownership_challenge_token varchar(255);\n"
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
                        "          AND column_name = 'ownership_challenge_token'\n"
                        "    ) THEN\n"
                        "        ALTER TABLE urls_manager_urlasset\n"
                        "            DROP COLUMN ownership_challenge_token;\n"
                        "    END IF;\n"
                        "END $$;\n"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="urlasset",
                    name="ownership_challenge_token",
                    field=models.CharField(
                        max_length=255,
                        null=True,
                        blank=True,
                    ),
                ),
            ],
        ),
    ]
