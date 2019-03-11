import re
import logging
import datetime
import base64
import struct

from django.db import transaction

from decisions.models import Membership, Organization, OrganizationClass, Person, Post, PostClass
from .sync import ModelSyncher


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


class Importer(object):
    @staticmethod
    def clean_text(text):
        text = text.replace('\n', ' ')
        # remove consecutive whitespaces
        return re.sub(r'\s\s+', ' ', text, re.U).strip()

    def _set_field(self, obj, field_name, val):
        field = obj._meta.get_field(field_name)
        if not hasattr(obj, field_name):
            raise Exception("Object %s doesn't have '%s' field" % (type(obj), field_name))

        obj_val = getattr(obj, field_name)
        if isinstance(obj_val, datetime.datetime) and isinstance(val, str):
            obj_val = obj_val.isoformat()
            if obj_val.endswith('000+00:00'):
                obj_val = obj_val.replace('000+00:00', 'Z')
        elif isinstance(obj_val, datetime.datetime) and isinstance(val, datetime.datetime):
            val = val.astimezone(obj_val.tzinfo)
        elif isinstance(obj_val, datetime.date) and isinstance(val, str):
            obj_val = obj_val.isoformat()
        elif isinstance(obj_val, float) and isinstance(val, float):
            # If floats are close enough, treat them as the same
            if isclose(obj_val, val):
                val = obj_val
        if obj_val == val:
            return

        if field.get_internal_type() == 'CharField' and val is not None:
            if len(val) > field.max_length:
                raise Exception("field '%s' too long (max. %d): %s" % field_name, field.max_length, val)

        setattr(obj, field_name, val)
        obj._changed = True
        obj._changed_fields.append(field_name)

    def _update_fields(self, obj, data, skip_fields=[]):
        data = data.copy()

        if not hasattr(obj, '_changed_fields'):
            obj._changed_fields = []
        obj_fields = list(obj._meta.fields)
        for d in skip_fields:
            for f in obj_fields:
                if f.name == d:
                    obj_fields.remove(f)
                    break

        # Make sure object supports all incoming fields
        field_names = []
        for field in obj_fields:
            field_name = field.name
            if field.is_relation:
                field_name = field_name + '_id'
            if field_name not in data:
                continue
            self._set_field(obj, field_name, data.pop(field_name))

        if data:
            raise Exception("%s doesn't support fields %s" % (type(obj), ', '.join(data.keys())))

    def _generate_id(self):
        t = datetime.time.time() * 1000000
        b = base64.b32encode(struct.pack(">Q", int(t)).lstrip(b'\x00')).strip(b'=').lower()
        return b.decode('utf8')

    def __init__(self, options):
        super(Importer, self).__init__()
        self.options = options
        self.verbosity = options['verbosity']
        self.logger = logging.getLogger(__name__)

    def _get_or_create_person(self, info):
        person, created = Person.objects.get_or_create(
            data_source=self.data_source,
            origin_id=info['origin_id'],
            defaults=info
        )
        if created:
            self.logger.info('Created person {}'.format(person))

        return person

    def _save_membership(self, info, organization):
        person_info = info.pop('person')
        person = self._get_or_create_person(person_info)

        membership = Membership.objects.create(
            data_source=self.data_source,
            person=person,
            organization=organization,
            role=info['role'],
            start_date=info['start_date'],
            end_date=info['end_date'],
        )
        self.logger.info('Created membership {}'.format(membership))

        return membership

    def save_organization(self, obj, info):
        info.pop('memberships', None)
        info.pop('contact_details', None)
        info['data_source_id'] = self.data_source.id

        classification = info.pop('classification', None)
        if classification:
            if hasattr(self, 'org_class_by_id'):
                classification_id = self.org_class_by_id[classification].id
            else:
                classification_id = OrganizationClass.objects.get(
                    data_source=self.data_source, origin_id=classification
                ).id
            info['classification_id'] = classification_id

        self._update_fields(obj, info)

        if obj._changed_fields:
            self.logger.info('{}: {} (changed: {})'.format(
                obj.origin_id, obj.name, ', '.join(obj._changed_fields)
            ))
            obj.save()

    def save_post(self, obj, info):
        info.pop('memberships', None)
        info.pop('contact_details', None)

        info['data_source_id'] = self.data_source.id

        classification = info.pop('classification', None)
        if classification:
            if hasattr(self, 'post_class_by_id'):
                classification_id = self.post_class_by_id[classification].id
            else:
                classification_id = PostClass.objects.get(
                    data_source=self.data_source, origin_id=classification
                ).id
            info['classification_id'] = classification_id

        self._update_fields(obj, info)

        if obj._changed_fields:
            self.logger.info('{}: {} (changed: {})'.format(
                obj.origin_id, obj.label, ', '.join(obj._changed_fields)
            ))
            obj.save()

    @transaction.atomic
    def update_organizations(self, orgs):
        org_qs = Organization.objects.filter(data_source=self.data_source).prefetch_related('posts')
        syncher = ModelSyncher(queryset=org_qs, generate_obj_id=lambda x: x.origin_id, delete_limit=0.1)

        for org_info in orgs:
            org_info = org_info.copy()
            origin_id = org_info.pop('origin_id')
            org_obj = syncher.get(origin_id)
            if not org_obj:
                org_obj = Organization(data_source=self.data_source, origin_id=origin_id)
            syncher.mark(org_obj)

            parent_id = org_info.get('parent_id')
            if parent_id:
                parent_obj = syncher.get(parent_id)
                assert parent_obj is not None
                org_info['parent_id'] = parent_obj.id

            self.save_organization(org_obj, org_info)

        syncher.finish()

    @transaction.atomic
    def update_posts(self, posts):
        post_qs = Post.objects.filter(data_source=self.data_source)
        syncher = ModelSyncher(queryset=post_qs, generate_obj_id=lambda x: x.origin_id, delete_limit=0.1)
        org_qs = Organization.objects.filter(data_source=self.data_source)
        orgs_by_id = {x.origin_id: x for x in org_qs}

        for post in posts:
            post = post.copy()
            origin_id = post.pop('origin_id')
            obj = syncher.get(origin_id)
            if not obj:
                obj = Post(data_source=self.data_source, origin_id=origin_id)
            syncher.mark(obj)

            organization_id = post['organization_id']
            if organization_id:
                org_obj = orgs_by_id[organization_id]
                post['organization_id'] = org_obj.id

            self.save_post(obj, post)

        syncher.finish()
