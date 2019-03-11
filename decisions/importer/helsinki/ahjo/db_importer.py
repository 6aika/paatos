import logging

from django.db import transaction

from ....models import (
    Action, Case, Content, DataSource, Event, Function, ImportedFile,
    Organization, Post, OrganizationClass, Person)
from .importer import ChangeImporter

LOG = logging.getLogger(__name__)


class DatabaseImporter(ChangeImporter):
    """
    Importer that imports from Ahjo to the database.
    """
    def __init__(self, data_source=None):
        if data_source is None:
            (data_source, _created) = DataSource.objects.get_or_create(
                identifier='helsinki', defaults={'name': 'Helsinki'})
        self.data_source = data_source
        self.orgs_by_id = {x.origin_id: x for x in Organization.objects.filter(data_source=data_source)}
        self.posts_by_id = {x.origin_id: x for x in Post.objects.filter(data_source=data_source)}

    def should_import(self, doc_info):
        # Currently only "minutes" are imported, "agenda" is not.
        should_import = (doc_info.doc_type == 'minutes') and 'VH' not in doc_info.policymaker_id
        if not should_import:
            LOG.debug("Skipping %s: %s", doc_info.doc_type, doc_info.origin_id)
        return should_import

    def _import_single(self, doc_info):
        with transaction.atomic():
            super(DatabaseImporter, self)._import_single(doc_info)

    def get_imported_version(self, doc_info):
        imported_file = ImportedFile.objects.filter(
            data_source=self.data_source, path=doc_info.path).first()
        return imported_file.imported_version if imported_file else None

    def set_imported_version(self, doc_info, version):
        ImportedFile.objects.update_or_create(
            data_source=self.data_source, path=doc_info.path, defaults={
                'imported_version': version})

    def handle_document_changed(self, doc_info):
        """
        Handle document change or a new document.

        Import or update the data from the document to the database.

        :type doc_info: .docinfo.DocumentInfo
        """
        LOG.info("Updating data from %s", doc_info.origin_id)
        doc = doc_info.get_document()
        self._import_document(doc_info, doc)

    def _import_document(self, doc_info, doc):
        # Skip office-holder documents for now
        event = self._import_event(doc_info, doc)
        self._import_attendees(doc, event)
        self._import_actions(doc, event)

    def _import_event(self, doc_info, doc):
        policymaker_id = doc_info.policymaker_id
        org = self.orgs_by_id[policymaker_id]
        defaults = {
            'name': doc.event.name,
            'start_date': doc.event.start_date,
            'end_date': doc.event.end_date,
            'organization_id': org.id,
        }
        (event, created) = Event.objects.update_or_create(
            data_source=self.data_source,
            origin_id=doc_info.origin_id,
            defaults=defaults)
        _log_update_or_create(event, created, logging.INFO)
        return event

    def _import_attendees(self, doc, event):
        imported_attendees = set()
        for attendee_data in (doc.event.attendees or []):
            defaults = {
                'role': attendee_data.role,
            }
            (attendee, created) = event.attendees.update_or_create(
                data_source=self.data_source,
                person=self._get_or_create_person(attendee_data),
                defaults=defaults)
            _log_update_or_create(attendee, created)
            imported_attendees.add(attendee.pk)

        # Delete all old non-updated attendees (if there is any)
        event.attendees.exclude(pk__in=imported_attendees).delete()

    def _get_or_create_person(self, data):
        names = data.name.split(None, 1) or ['']
        first_name = names[0] if len(names) >= 2 else ''
        last_name = names[-1]
        (person, created) = Person.objects.get_or_create(
            data_source=self.data_source,
            origin_id='{name}/{title}'.format(
                name=data.name, title=(data.title or '')),
            defaults={
                'name': data.name,
                'given_name': first_name,
                'family_name': last_name,
            })
        if created:
            _log_update_or_create(person, created)
        return person

    def _import_actions(self, doc, event):
        imported_actions = set()
        for (num, action_data) in enumerate(doc.event.actions or []):
            case = self._import_case(action_data, event, num)
            action = self._import_action(action_data, event, num, case)
            imported_actions.add(action.pk)
            self._import_contents(action_data, action)

        # Delete all old non-updated actions (if there is any)
        event.actions.exclude(pk__in=imported_actions).delete()

    def _import_case(self, action_data, event, num):
        if not action_data.register_id:
            return None
        defaults = {
            'title': action_data.title,
            'function': self._get_or_create_function(action_data),
        }
        (case, created) = Case.objects.update_or_create(
            data_source=self.data_source,
            register_id=action_data.register_id,
            defaults=defaults)
        _log_update_or_create(case, created)
        self._import_attachments(action_data, case)
        return case

    def _get_or_create_function(self, data):
        if not data.function_id:
            return None
        (function, created) = Function.objects.get_or_create(
            data_source=self.data_source,
            function_id=data.function_id,
            defaults={'name': data.function_name})
        if created:
            _log_update_or_create(function, created)
        return function

    def _import_attachments(self, action_data, case):
        for attachemnt_data in (action_data.attachments or []):
            pass  # TODO: Import attachments

    def _import_action(self, action_data, event, num, case):
        defaults = {
            'case': case,
            'title': action_data.title,
            'ordering': num,
            'resolution': action_data.resolution or '',
            'event': event,
            'article_number': str(action_data.article_number or ''),
        }
        (action, created) = Action.objects.update_or_create(
            data_source=self.data_source,
            origin_id='{event.origin_id}:{num}'.format(event=event, num=num),
            defaults=defaults)
        _log_update_or_create(action, created)
        return action

    def _import_contents(self, action_data, action):
        defaults = {
            'hypertext': action_data.content,
            'type': 'decision',  # XXX
            'ordering': 1,
        }
        (content, created) = Content.objects.update_or_create(
            data_source=self.data_source,
            action=action,
            origin_id=action.origin_id,
            defaults=defaults)
        _log_update_or_create(content, created)


def _log_update_or_create(obj, created, level=logging.DEBUG):
    if created:
        LOG.log(level, 'Created %s %s', type(obj).__name__, obj.pk)
    else:
        LOG.log(level, 'Updated %s %s', type(obj).__name__, obj.pk)
