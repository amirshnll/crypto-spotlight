import os
import glob
import shutil
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.conf import settings


class Command(BaseCommand):
    help = "Initialize the project with a clean database and initial data"

    def handle(self, *args, **options):
        BASE_DIR = settings.BASE_DIR
        LOCAL_APPS = settings.LOCAL_APPS

        # 0. Install requirements
        self.stdout.write("Installing requirements...")
        try:
            os.system("pip install -r requirements.txt")
            self.stdout.write(self.style.SUCCESS("✓ Requirements installed"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error installing requirements: {str(e)}")
            )

        # 1. Remove database file
        if os.path.exists("db.sqlite3"):
            os.remove("db.sqlite3")
            self.stdout.write(self.style.SUCCESS("✓ Database file removed"))

        # 2. Delete all migrations files
        migration_dirs = glob.glob("*/migrations/*.py")
        for migration in migration_dirs:
            if "__init__.py" not in migration:
                try:
                    os.remove(migration)
                    print(f"Removed migration file: {migration}")
                except OSError as e:
                    print("Error: %s : %s" % (migration, e.strerror))

        # 3. Remove media directory
        media_path = os.path.join(BASE_DIR, "media")
        if os.path.exists(media_path):
            try:
                shutil.rmtree(media_path)
                print(f"Removed 'media' directory and all its contents: {media_path}")
            except OSError as e:
                print(f"Error removing 'media' directory: {e}")

        os.makedirs(media_path)
        self.stdout.write(self.style.SUCCESS("✓ 'media' directory created"))

        # 4. Delete all __pycache__ directories and .DS_Store files
        for root, dirs, files in os.walk(BASE_DIR, topdown=False):
            for dir in dirs:
                if dir == "__pycache__":
                    try:
                        shutil.rmtree(os.path.join(root, dir))
                        print(
                            f"Removed __pycache__ directory: {os.path.join(root, dir)}"
                        )
                    except OSError as e:
                        print(f"Error removing __pycache__: {e}")

            for file in files:
                if file == ".DS_Store":
                    try:
                        os.remove(os.path.join(root, file))
                        print(f"Removed .DS_Store file: {os.path.join(root, file)}")
                    except OSError as e:
                        print(f"Error removing .DS_Store: {e}")

        # 5. Run initial migrate
        self.stdout.write("Running initial migrate...")
        call_command("migrate")

        # 6. Make migrations
        self.stdout.write("Making migrations...")
        call_command("makemigrations")

        # 7. Run migrations
        self.stdout.write("Running migrations...")
        call_command("migrate")

        # 8. Load fixtures
        if not LOCAL_APPS:
            self.stdout.write(self.style.ERROR("No LOCAL_APPS found in settings.py."))
            return

        # Dictionary to store fixtures per app
        fixtures_map = {}

        for app_label in LOCAL_APPS:
            fixtures_dir = os.path.join(app_label.replace(".", "/"), "fixtures")
            if os.path.exists(fixtures_dir):
                fixtures = [
                    os.path.join(fixtures_dir, f)
                    for f in os.listdir(fixtures_dir)
                    if f.endswith(".json")
                ]
                fixtures_map[app_label] = fixtures

        if not fixtures_map:
            self.stdout.write(self.style.WARNING("No fixtures found in any app."))
            return

        # Load fixtures dynamically in order
        loaded_fixtures = set()

        def load_fixture(fixture_path):
            try:
                self.stdout.write(f"Loading {fixture_path}")
                call_command("loaddata", fixture_path)
                loaded_fixtures.add(fixture_path)
                return True
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Retrying later: {fixture_path} due to error: {e}"
                    )
                )
                return False

        # Attempt to load all fixtures, retry failed ones until no changes
        all_fixtures = [fp for fixtures in fixtures_map.values() for fp in fixtures]
        while all_fixtures:
            remaining_fixtures = []
            all_fixtures.sort()
            for fixture_path in all_fixtures:
                if not load_fixture(fixture_path):
                    remaining_fixtures.append(fixture_path)
            if len(remaining_fixtures) == len(all_fixtures):
                # No progress made, break to avoid infinite loop
                break
            all_fixtures = remaining_fixtures

        if all_fixtures:
            self.stdout.write(
                self.style.ERROR(
                    "The following fixtures could not be loaded due to errors:"
                )
            )
            for fixture_path in all_fixtures:
                self.stdout.write(self.style.ERROR(f" - {fixture_path}"))
        else:
            self.stdout.write(self.style.SUCCESS("All fixtures loaded successfully."))

        # 9. Create superuser
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@gmail.com", "admin")
            self.stdout.write(self.style.SUCCESS("✓ Superuser created"))

        # 9. Move crypto/icons to media/icons
        icons_dir = os.path.join(BASE_DIR, "crypto", "icons")
        media_icons_dir = os.path.join(BASE_DIR, "media", "crypto")
        if os.path.exists(icons_dir):
            shutil.copytree(icons_dir, media_icons_dir)
            self.stdout.write(self.style.SUCCESS("✓ Icons moved to media/crypto"))

        # 10. Read all Cryptocurrency and set icons
        from crypto.models import Cryptocurrency

        cryptocurrencies = Cryptocurrency.objects.all()
        for cryptocurrency in cryptocurrencies:
            icon_path = os.path.join(media_icons_dir, f"{cryptocurrency.symbol}.svg")
            if os.path.exists(icon_path):
                cryptocurrency.icon = f"crypto/{cryptocurrency.symbol}.svg"
                cryptocurrency.save()

        # 11. Collect static
        self.stdout.write("Collecting static...")
        call_command("collectstatic", "--noinput", "--clear")
        self.stdout.write(self.style.SUCCESS("✓ Project initialized"))
