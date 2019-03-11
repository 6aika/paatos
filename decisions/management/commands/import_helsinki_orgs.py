from django.core.management.base import BaseCommand

from decisions.importer.helsinki.organizations import HelsinkiImporter


class Command(BaseCommand):
    help = 'Imports Helsinki organizations'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)
        parser.add_argument('--include-people', action='store_true', dest='include_people', default=False)

    def handle(self, *args, **options):
        importer = HelsinkiImporter(options)
        importer.import_organizations(options['filename'])
