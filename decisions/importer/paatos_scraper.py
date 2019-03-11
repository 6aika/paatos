# -*- coding: utf-8 -*-
import json
import os
import os.path
import tempfile
import zipfile

import dateutil.parser
from django.utils.text import slugify

from decisions.models import (
    Action, Attachment, Case, CaseGeometry, Content, DataSource, Event,
    Function, Organization)

from .base import Importer


class PaatosScraperImporter(Importer):
    def __init__(self, identifier, defaults, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_source, created = DataSource.objects.get_or_create(
            identifier=identifier,
            defaults=defaults
        )
        if created:
            self.logger.debug('Created new data source "%s"' % identifier)

    def _import_organization(self, data):
        classification = data['classification'].title()
        org = dict(origin_id=data['sourceId'])
        org['classification'] = classification

        org['name'] = data['name']
        org['slug'] = slugify(org['origin_id'])

        org['founding_date'] = data['founding_date']
        org['dissolution_date'] = data['dissolution_date']

        org['parent'] = data['parent']

        self.save_organization(org)

    def _import_function(self, name, source_id):
        self.logger.info('Importing functions...')

        defaults = dict(
            name=name,
            function_id=source_id
        )

        function, created = Function.objects.update_or_create(
            origin_id=source_id,
            data_source=self.data_source,
            defaults=defaults
        )

        if created:
            self.logger.info('Created function %s' % function)

        return function

    def _import_event(self, data, organization_source_id):
        self.logger.info('Importing event...')

        defaults = dict(
            start_date=dateutil.parser.parse(data['startDate']).date(),
            end_date=dateutil.parser.parse(data['endDate']).date(),
            name=data['name']
        )

        try:
            organization = Organization.objects.get(origin_id=organization_source_id)
            defaults['organization'] = organization
        except Organization.DoesNotExist:
            self.logger.error('Organization %s does not exist' % organization_source_id)
            return

        event, created = Event.objects.update_or_create(
            data_source=self.data_source,
            origin_id=data['sourceId'],
            defaults=defaults
        )

        if created:
            self.logger.info('Created event %s' % event)

    def _import_cases(self, data):
        self.logger.info('Importing case...')

        for case_data in data:

            defaults = dict(
                title=case_data['title'],
                register_id=case_data['registerId'],
            )

            try:
                defaults['function'] = Function.objects.get(origin_id=case_data['functionId'])
            except Function.DoesNotExist:
                defaults['function'] = self._import_function(case_data['functionId'], case_data['functionId'])

            case, created = Case.objects.update_or_create(
                data_source=self.data_source,
                origin_id=case_data['sourceId'],
                defaults=defaults,
            )

            if created:
                self.logger.info('Created case %s' % case)

    def _import_action(self, data):
        self.logger.info('Importing action...')

        defaults = dict(
            title=data['title'],
            ordering=data['ordering'],
            article_number=data['articleNumber']
        )
        if data['caseId']:
            try:
                case = Case.objects.get(origin_id=data['caseId'])
                defaults['case'] = case
            except Case.DoesNotExist:
                self.logger.error('Case %s does not exist' % data['caseId'])
                return
        try:
            event = Event.objects.get(origin_id=data['eventId'])
            defaults['event'] = event
        except Event.DoesNotExist:
            self.logger.error('Event %s does not exist' % data['eventId'])
            return

        action, created = Action.objects.update_or_create(
            data_source=self.data_source,
            origin_id=data['sourceId'],
            defaults=defaults
        )

        if created:
            self.logger.info('Created action %s' % action)

    def _import_contents(self, data, action_source_id):
        self.logger.info('Importing action contents...')

        for content_data in data:

            content_title = content_data['title']
            if (len(content_data['title']) > 255):
                content_title = content_title[:255]
                self.logger.warning('Truncated conetent title %s' % content_data['title'])

            defaults = dict(
                title=content_title,
                hypertext=content_data['content'],
                type='',
                ordering=content_data['order']
            )

            try:
                action = Action.objects.get(origin_id=action_source_id)
                defaults['action'] = action
            except Action.DoesNotExist:
                self.logger.error('Action %s does not exist' % action_source_id)
                continue

            content, created = Content.objects.update_or_create(
                data_source=self.data_source,
                origin_id=str(content_data['order']) + '-' + action_source_id,
                defaults=defaults
            )

            if created:
                self.logger.info('Created content %s' % content)

    def _import_attachments(self, data):
        self.logger.info('Importing attachments...')

        for attachment_data in data:
            defaults = dict(
                name=attachment_data['name'] or '',
                url=attachment_data['url'],
                number=attachment_data['number'],
                public=attachment_data['public'],
                confidentiality_reason=attachment_data['confidentialityReason'] or '',
            )

            try:
                action = Action.objects.get(origin_id=attachment_data['actionId'])
                defaults['action'] = action
            except Action.DoesNotExist:
                self.logger.error('Action %s does not exist' % attachment_data['actionId'])
                continue

            attachment, created = Attachment.objects.update_or_create(
                data_source=self.data_source,
                origin_id=attachment_data['sourceId'],
                defaults=defaults
            )

            if created:
                self.logger.info('Created attachment %s' % attachment)

    def _handle_organization(self, organization_path):
        if os.path.isfile(organization_path):
            with open(organization_path, 'r') as org_file:
                self._import_organization(json.load(org_file))

    def _handle_organization_cases(self, cases_path):
        if os.path.isfile(cases_path):
            with open(cases_path, 'r') as cases_file:
                self._import_cases(json.load(cases_file))

    def _handle_organization_events(self, events_path, organization_source_id):
        if os.path.exists(events_path):
            for event_source_id in os.listdir(events_path):
                event_json_path = events_path + '/' + event_source_id + '/index.json'
                if os.path.isfile(event_json_path):
                    with open(event_json_path, 'r') as event_file:
                        self._import_event(json.load(event_file), organization_source_id)
                        action_folder = events_path + '/' + event_source_id + '/actions'
                        self._handle_organization_event_actions(
                            action_folder,
                            organization_source_id,
                            event_source_id)

    def _handle_organization_event_actions(self, actions_path, organization_source_id, event_source_id):
        if os.path.exists(actions_path):
            for action_source_id in os.listdir(actions_path):
                action_file_path = actions_path + '/' + action_source_id + '/index.json'
                contents_file_path = actions_path + '/' + action_source_id + '/contents.json'
                attachment_file_path = actions_path + '/' + action_source_id + '/attachments.json'
                if os.path.isfile(action_file_path):
                    with open(action_file_path, 'r') as action_file:
                        self._import_action(json.load(action_file))
                        self._handle_contents(contents_file_path, action_source_id)
                        self._handle_attachments(attachment_file_path)

    def _handle_contents(self, contents_path, action_id):
        if os.path.isfile(contents_path):
            with open(contents_path, 'r') as contents_file:
                self._import_contents(json.load(contents_file), action_id)

    def _handle_attachments(self, attachment_path):
        if os.path.isfile(attachment_path):
            with open(attachment_path, 'r') as attachment_file:
                self._import_attachments(json.load(attachment_file))

    def import_data(self):
        self.logger.info('Importing data...')

        if self.options['flush']:
            self.logger.info('Deleting all objects first...')
            Function.objects.all().delete()
            Event.objects.all().delete()
            CaseGeometry.objects.all().delete()
            Action.objects.all().delete()
            Content.objects.all().delete()
            Attachment.objects.all().delete()

        with tempfile.TemporaryDirectory() as temp_dirpath:
            zip_ref = zipfile.ZipFile(self.options['zipfile'], 'r')
            zip_ref.extractall(temp_dirpath)
            zip_ref.close()
            for organization_source_id in os.listdir(temp_dirpath + '/organizations'):
                current_path = temp_dirpath + '/organizations/' + organization_source_id
                self._handle_organization(current_path + '/index.json')
                self._handle_organization_cases(current_path + '/cases.json')
                self._handle_organization_events(current_path + '/events', organization_source_id)

            self.logger.info('Import done!')
