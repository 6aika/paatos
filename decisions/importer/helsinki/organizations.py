# -*- coding: utf-8 -*-
# Based heavily on https://github.com/City-of-Helsinki/openahjo/blob/4bcb003d5db932ca28ea6851d76a20a4ee6eef54/decisions/importer/helsinki.py  # noqa

import json
import datetime
import pytz
from enum import Enum

from dateutil.parser import parse as dateutil_parse
from django.db import transaction
from django.utils.text import slugify

from decisions.models import DataSource, OrganizationClass, Person, PostClass

from ..base import Importer

LOCAL_TZ = pytz.timezone('Europe/Helsinki')


class Org(Enum):
    COUNCIL = 1
    BOARD = 2
    EXECUTIVE_BOARD = 3
    BOARD_DIVISION = 4
    COMMITTEE = 5
    COMMON = 6
    FIELD = 7
    DEPARTMENT = 8
    DIVISION = 9
    INTRODUCER = 10
    INTRODUCER_FIELD = 11
    OFFICE_HOLDER = 12
    CITY = 13
    UNIT = 14
    WORKING_GROUP = 15
    SCHOOL_BOARDS = 16
    PACKAGED_SERVICE = 17
    PACKAGED_INTRODUCER_SERVICE = 18
    TRUSTEE = 19


NAME_MAP = {
    Org.COUNCIL: ('Valtuusto', None, 'Council'),
    Org.BOARD: ('Hallitus', None, 'Board'),
    Org.EXECUTIVE_BOARD: ('Johtajisto', None, 'Executive board'),
    Org.BOARD_DIVISION: ('Jaosto', None, 'Board division'),
    Org.COMMITTEE: ('Lautakunta', None, 'Committee'),
    Org.COMMON: ('Yleinen', None, 'Common'),
    Org.FIELD: ('Toimiala', None, 'Field'),
    Org.DEPARTMENT: ('Virasto', None, 'Department'),
    Org.DIVISION: ('Osasto', None, 'Division'),
    Org.INTRODUCER: ('Esittelijä', None, 'Introducer'),
    Org.INTRODUCER_FIELD: ('Esittelijä (toimiala)', None, 'Introducer field'),
    Org.OFFICE_HOLDER: ('Viranhaltija', None, 'Office holder'),
    Org.CITY: ('Kaupunki', None, 'City'),
    Org.UNIT: ('Yksikkö', None, 'Unit'),
    Org.WORKING_GROUP: ('Toimikunta', None, 'Working group'),
    Org.SCHOOL_BOARDS: ('Koulujen johtokunnat', None, 'School boards'),
    Org.PACKAGED_SERVICE: ('Palvelukokonaisuus', None, 'Packaged service'),
    Org.PACKAGED_INTRODUCER_SERVICE: ('Esittelijäpalvelukokonaisuus', None, 'Packaged introducer service'),
    Org.TRUSTEE: ('Luottamushenkilö', None, 'Trustee')
}


class HelsinkiImporter(Importer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_source, created = DataSource.objects.get_or_create(
            identifier='helsinki',
            defaults={'name': 'Helsinki'}
        )
        if created:
            self.logger.debug('Created new data source "helsinki"')

    @transaction.atomic()
    def _import_organization(self, info):
        org_type = Org(info['type'])
        org = dict(origin_id=info['id'])
        org['classification'] = str(org_type.value)

        if org_type in [Org.INTRODUCER, Org.INTRODUCER_FIELD, Org.PACKAGED_INTRODUCER_SERVICE]:
            self.skip_orgs.add(org['origin_id'])
            return

        # TODO change when model translations are in
        """
        org['name'] = {'fi': info['name_fin'], 'sv': info['name_swe']}
        """
        org['name'] = info['name_fin']

        if org['origin_id'] == '500':
            # Strange "Puheenjohtaja" organization
            assert org['name'] == 'Puheenjohtaja'
            self.skip_orgs.add(org['origin_id'])
            return

        if info['shortname']:
            org['abbreviation'] = info['shortname']

        if org_type in (Org.COUNCIL, Org.COMMITTEE, Org.BOARD_DIVISION, Org.BOARD):
            org['slug'] = slugify(org['abbreviation'])
        else:
            org['slug'] = slugify(org['origin_id'])

        org['founding_date'] = None
        if info['start_time']:
            d = dateutil_parse(info['start_time'])
            # 2009-01-01 means "no data"
            if not (d.year == 2009 and d.month == 1 and d.day == 1):
                org['founding_date'] = d.date().strftime('%Y-%m-%d')

        org['dissolution_date'] = None
        if info['end_time']:
            d = dateutil_parse(info['end_time'])
            org['dissolution_date'] = d.date().strftime('%Y-%m-%d')

        org['contact_details'] = []
        if info['visitaddress_street'] or info['visitaddress_zip']:
            cd = {'type': 'address'}
            cd['value'] = info.get('visitaddress_street', '')
            z = info.get('visitaddress_zip', '')
            if z and len(z) == 2:
                z = "00%s0" % z
            cd['postcode'] = z
            org['contact_details'].append(cd)

        org['modified_at'] = LOCAL_TZ.localize(dateutil_parse(info['modified_time']))

        # Remove orgs that are actually posts from the org hierarchy
        if org_type in [Org.OFFICE_HOLDER, Org.TRUSTEE]:
            for child in info.get('children', []):
                assert child['parent'] == info['id']
                child['parent'] = org.get('parent', None)
            info['children'] = []

        parent = info['parent']
        if parent:
            assert parent['id'] not in self.skip_orgs
            parent_type = Org(parent['type'])
            assert parent_type not in [Org.OFFICE_HOLDER, Org.TRUSTEE]
            parent_id = parent['id']
        else:
            parent_id = None

        org['parent_id'] = parent_id

        org['memberships'] = []
        if self.options['include_people']:
            for person_info in info['people']:
                person = dict(
                    origin_id=person_info['id'],
                    given_name=person_info['first_name'],
                    family_name=person_info['last_name'],
                    name='{} {}'.format(person_info['first_name'], person_info['last_name'])
                )
                org['memberships'].append(dict(
                    person=person,
                    start_date=person_info['start_time'],
                    end_date=person_info['end_time'],
                    role=person_info['role'],
                ))

        if org_type in [Org.OFFICE_HOLDER, Org.TRUSTEE]:
            org['entity_type'] = 'post'
            rename_fields = {
                'name': 'label',
                'founding_date': 'start_date',
                'dissolution_date': 'end_date',
                'parent_id': 'organization_id'
            }
            for a, b in rename_fields.items():
                org[b] = org.pop(a)
        else:
            org['entity_type'] = 'org'
        return org

    def _import_organization_classes(self):
        self.logger.info('Updating organization class definitions...')
        self.org_class_by_id = {}
        self.post_class_by_id = {}
        for enum, names in NAME_MAP.items():
            if enum in (Org.INTRODUCER, Org.INTRODUCER_FIELD, Org.TRUSTEE, Org.OFFICE_HOLDER):
                kls = PostClass
                by_id_dict = self.post_class_by_id
            else:
                kls = OrganizationClass
                by_id_dict = self.org_class_by_id

            try:
                obj = kls.objects.get(data_source=self.data_source, origin_id=str(enum.value))
            except kls.DoesNotExist:
                obj = kls(data_source=self.data_source, origin_id=str(enum.value))

            if obj.name != names[0]:
                obj.name = names[0]
                obj.save()
            by_id_dict[obj.origin_id] = obj

    def import_organizations(self, filename):
        self._import_organization_classes()

        self.logger.info('Importing organizations...')

        with open(filename, 'r') as org_file:
            org_list = json.load(org_file)

        date_now = datetime.datetime.now().strftime('%Y-%m-%d')
        for org in org_list:
            org['children'] = []
            if not org['parents']:
                org['parent'] = None
                del org['parents']
                continue
            parents = [p for p in org['parents'] if p['primary']]
            active_parent = None
            last_parent = parents[0]
            for p in parents:
                if p['end_time'] is None or p['end_time'] > date_now:
                    active_parent = p
                if last_parent['end_time'] and (p['end_time'] is None or p['end_time'] > last_parent['end_time']):
                    last_parent = p
            assert active_parent is None or last_parent == active_parent
            del org['parents']
            org['parent'] = last_parent['id']

        self.skip_orgs = set()

        self.org_dict = {org['id']: org for org in org_list}
        roots = []
        for org in org_list:
            if not org['parent']:
                roots.append(org)
                continue
            self.org_dict[org['parent']]['children'].append(org)

        output_org_list = []
        output_post_list = []

        def import_nested(parent, org):
            output_org = self._import_organization(org)
            if not output_org:
                return

            entity_type = output_org.pop('entity_type')
            if entity_type == 'post':
                output_post_list.append(output_org)
                return

            output_org_list.append(output_org)
            for child in org['children']:
                assert child['parent'] == org['id']
                child['parent'] = org
                import_nested(output_org, child)

        for root in roots:
            import_nested(None, root)

        self.update_organizations(output_org_list)
        self.update_posts(output_post_list)

        self.logger.info('Import done!')
