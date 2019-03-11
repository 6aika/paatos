# -*- coding: UTF-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _

from .base import DataModel


class OrganizationClass(DataModel):
    name = models.CharField(max_length=255, null=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class Organization(DataModel):
    classification = models.ForeignKey(
        OrganizationClass,
        help_text=_('An organization classification, e.g. committee'),
        on_delete=models.PROTECT,
        null=True, blank=True
    )
    name = models.CharField(max_length=255, help_text=_('A primary name, e.g. a legally recognized name'))
    slug = models.CharField(max_length=255, help_text=_('Slug for the organization'), db_index=True)
    abbreviation = models.CharField(max_length=50, help_text=_('An abbreviation for the organization'), null=True, blank=True)
    founding_date = models.DateField(help_text=_('A date of founding'), blank=True, null=True)
    dissolution_date = models.DateField(help_text=_('A date of dissolution'), blank=True, null=True, db_index=True)
    parent = models.ForeignKey('self', help_text=_('The organizations that contain this organization'), null=True,
                               blank=True)
    # FIXME: Add contact details

    class Meta:
        ordering = ['id']

    def __str__(self):
        if self.parent:
            return '%s / %s' % (self.parent, self.name)  # TODO cache
        else:
            return self.name


class PostClass(DataModel):
    name = models.CharField(max_length=255, null=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class Post(DataModel):
    classification = models.ForeignKey(
        PostClass,
        help_text=_('A post classification, e.g. committee'),
        on_delete=models.PROTECT,
        null=True, blank=True
    )
    label = models.CharField(max_length=255, help_text=_('A label describing the post'))
    slug = models.CharField(max_length=255, help_text=_('Slug for the post'), db_index=True)
    abbreviation = models.CharField(max_length=50, help_text=_('An abbreviation for the post'), null=True, blank=True)
    organization = models.ForeignKey(Organization, related_name='posts',
                                     help_text=_('The organization in which the post is held'))
    start_date = models.DateField(help_text=_('The date on which the post was created'), null=True, blank=True)
    end_date = models.DateField(help_text=_('The date on which the post was eliminated'), null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return '%s / %s' % (self.organization, self.label)  # TODO cache
