# -*- coding: UTF-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


class BaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False,
                                      help_text=_('The time at which the resource was created'))
    modified_at = models.DateTimeField(default=timezone.now, editable=False,
                                       help_text=_('The time at which the resource was updated'))

    class Meta:
        abstract = True


class DataSource(BaseModel):
    identifier = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255, help_text=_('Human-readable name'))

    def __str__(self):
        return self.identifier


class DataModel(BaseModel):
    data_source = models.ForeignKey(
        DataSource, blank=True, null=True, db_index=True, on_delete=models.PROTECT
    )
    origin_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    class Meta:
        abstract = True
        unique_together = ('data_source', 'origin_id')


class ImportedFile(BaseModel):
    data_source = models.ForeignKey(
        DataSource, blank=True, null=True, db_index=True, on_delete=models.PROTECT
    )
    path = models.CharField(max_length=2000, db_index=True)
    imported_version = models.CharField(max_length=100)

    class Meta:
        unique_together = [('data_source', 'path')]
