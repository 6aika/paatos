# -*- coding: UTF-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .base import DataModel

# Popoloish models


# "An event is an occurrence that people may attend."
class Event(DataModel):
    name = models.CharField(max_length=255, help_text=_("The event's name"), blank=True)
    organization = models.ForeignKey('Organization', related_name='events',
                                     help_text=_('The organization organizing the event'), blank=True, null=True)
    start_date = models.DateTimeField(help_text=_('The time at which the event starts'))
    end_date = models.DateTimeField(help_text=_('The time at which the event ends'), blank=True, null=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return '%s %s' % (self.start_date, self.organization)


class EventAttendee(DataModel):
    event = models.ForeignKey(Event, related_name='attendees')
    person = models.ForeignKey('Person', related_name='attendances')
    role = models.CharField(max_length=255, help_text=_('The attendee\'s role in the event'), null=True)
