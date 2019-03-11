# -*- coding: utf-8 -*-
import json

from django.conf import settings

from decisions.models import (
    Action, Attachment, Case, CaseGeometry, Content, DataSource, Event,
    Function, Organization, Post)

from .base import Importer


class OpenAhjoImporter(Importer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_source, created = DataSource.objects.get_or_create(
            identifier='open_ahjo',
            defaults={'name': 'Open Ahjo'}
        )
        if created:
            self.logger.debug('Created new data source "open_ahjo"')
        self.meeting_to_org = None

    def _import_functions(self, data):
        self.logger.info('Importing functions...')

        for function_data in data['categories']:
            defaults = dict(
                name=function_data['name'],
                function_id=function_data['origin_id'],
            )

            parent_id = function_data['parent']
            if parent_id:
                try:
                    defaults['parent'] = Function.objects.get(origin_id=parent_id)
                except Function.DoesNotExist:
                    self.logger('Function parent %s does not exist' % parent_id)
                    continue

            function, created = Function.objects.update_or_create(
                origin_id=function_data['id'],
                data_source=self.data_source,
                defaults=defaults
            )

            if created:
                self.logger.info('Created function %s' % function)

    def _import_events(self, data):
        self.logger.info('Importing events...')

        for meeting_data in data['meetings']:
            defaults = dict(
                start_date=meeting_data['date'],
                end_date=meeting_data['date'],
            )

            organization_data = self.meeting_to_org.get(meeting_data['id'])
            if organization_data:
                if organization_data['type'] == 'office_holder':
                    continue
                try:
                    organization = Organization.objects.get(origin_id=organization_data['origin_id'])
                    defaults['organization'] = organization
                except Organization.DoesNotExist:
                    self.logger.error('Organization %s does not exist' % organization_data['origin_id'])
                    continue

            event, created = Event.objects.update_or_create(
                data_source=self.data_source,
                origin_id=meeting_data['id'],
                defaults=defaults
            )

            if created:
                self.logger.info('Created event %s' % event)

    def _import_case_geometries(self, data):
        self.logger.info('Importing case geometries...')

        for geometry_data in data['issue_geometries']:
            defaults = dict(
                name=geometry_data['name'],
                type=geometry_data['type'],
                geometry=geometry_data['geometry'],
            )

            case_geometry, created = CaseGeometry.objects.update_or_create(
                data_source=self.data_source,
                origin_id=geometry_data['id'],
                defaults=defaults,
            )

            if created:
                self.logger.info('Created case geometry %s' % case_geometry)

    def _import_cases(self, data):
        self.logger.info('Importing cases...')

        for issue_data in data['issues']:
            defaults = dict(
                title=issue_data['subject'],
                register_id=issue_data['register_id'],
            )

            try:
                defaults['function'] = Function.objects.get(origin_id=issue_data['category'])
            except Function.DoesNotExist:
                self.logger.error('Function %s does not exist' % issue_data['category'])
                continue

            case, created = Case.objects.update_or_create(
                data_source=self.data_source,
                origin_id=issue_data['id'],
                defaults=defaults,
            )

            if created:
                self.logger.info('Created case %s' % case)

            case.geometries = CaseGeometry.objects.filter(origin_id__in=issue_data['geometries'])

    def _import_actions(self, data):
        self.logger.info('Importing actions...')

        for agenda_item_data in data['agenda_items']:
            org = self.meeting_to_org.get(agenda_item_data['meeting'])
            if not org:
                self.logger.error('Cannot find matching org for meeting %s' % agenda_item_data['meeting'])
                continue

            defaults = dict(
                title=agenda_item_data['subject'],
                ordering=agenda_item_data['index'],
                resolution=agenda_item_data['resolution'] or '',
            )
            if agenda_item_data['issue']:
                try:
                    case = Case.objects.get(origin_id=agenda_item_data['issue'])
                    defaults['case'] = case
                except Case.DoesNotExist:
                    self.logger.error('Case %s does not exist' % agenda_item_data['issue'])
                    continue
            if org['type'] == 'office_holder':
                try:
                    post = Post.objects.get(origin_id=org['origin_id'])
                    defaults['post'] = post
                except Post.DoesNotExist:
                    self.logger.error('Post %s does not exist' % org['origin_id'])
                    continue
            else:
                try:
                    event = Event.objects.get(origin_id=agenda_item_data['meeting'])
                    defaults['event'] = event
                except Event.DoesNotExist:
                    self.logger.error('Event %s does not exist' % agenda_item_data['meeting'])
                    continue

            action, created = Action.objects.update_or_create(
                data_source=self.data_source,
                origin_id=agenda_item_data['id'],
                defaults=defaults
            )

            if created:
                self.logger.info('Created action %s' % action)

    def _import_contents(self, data):
        self.logger.info('Importing contents...')

        for content_section_data in data['content_sections']:
            defaults = dict(
                hypertext=content_section_data['text'],
                type=content_section_data['type'],
                ordering=content_section_data['index'],
            )

            action_id = content_section_data.get('agenda_item')
            try:
                action = Action.objects.get(origin_id=action_id)
                defaults['action'] = action
            except Action.DoesNotExist:
                self.logger.error('Action %s does not exist' % action_id)
                continue

            content, created = Content.objects.update_or_create(
                data_source=self.data_source,
                origin_id=content_section_data['id'],
                defaults=defaults
            )

            if created:
                self.logger.info('Created content %s' % content)

    def _import_attachments(self, data):
        self.logger.info('Importing attachments...')

        url_base = getattr(settings, 'OPEN_AHJO_ATTACHMENT_URL_BASE', None)

        for attachment_data in data['attachments']:
            defaults = dict(
                name=attachment_data['name'] or '',
                url=url_base + attachment_data['url'] if attachment_data['url'] and url_base else '',
                number=attachment_data['number'],
                public=attachment_data['public'],
                confidentiality_reason=attachment_data['confidentiality_reason'] or '',
            )

            action_id = attachment_data.get('agenda_item')
            try:
                action = Action.objects.get(origin_id=action_id)
                defaults['action'] = action
            except Action.DoesNotExist:
                self.logger.error('Action %s does not exist' % action_id)
                continue

            attachment, created = Attachment.objects.update_or_create(
                data_source=self.data_source,
                origin_id=attachment_data['id'],
                defaults=defaults
            )

            if created:
                self.logger.info('Created attachment %s' % attachment)

    def import_data(self):
        self.logger.info('Importing open ahjo data...')

        with open(self.options['filename'], 'r') as data_file:
            data = json.load(data_file)

        # pre calc meeting to org mapping
        org_dict = {o['origin_id']: o for o in data['organizations']}
        policymaker_to_org = {p['id']: org_dict[p['origin_id']] for p in data['policymakers']}
        self.meeting_to_org = {m['id']: policymaker_to_org[m['policymaker']] for m in data['meetings']}

        if self.options['flush']:
            self.logger.info('Deleting all objects first...')
            Function.objects.all().delete()
            Event.objects.all().delete()
            CaseGeometry.objects.all().delete()
            Action.objects.all().delete()
            Content.objects.all().delete()
            Attachment.objects.all().delete()

        self._import_functions(data)
        self._import_events(data)
        self._import_case_geometries(data)
        self._import_cases(data)
        self._import_actions(data)
        self._import_contents(data)
        self._import_attachments(data)

        self.logger.info('Import done!')
