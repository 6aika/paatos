from django.core.management.base import BaseCommand

from decisions.importer.helsinki import ahjo


class Command(BaseCommand):
    help = 'Imports'

    def add_arguments(self, parser):
        parser.add_argument(
            'root', type=str, help=(
                "Root path of the import, "
                "e.g. /files or /files/Asuntolautakunta_60014"))

    def handle(self, root, *args, **options):
        db_importer = ahjo.DatabaseImporter()
        db_importer.import_changes(root)
