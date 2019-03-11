# -*- coding: utf-8 -*-

import datetime
import logging
import re

import pytz
from lxml import etree

from .document import Document

RESOLUTION_MAP = {
    'hyväksytty': 'accepted'
}

ATTENDEE_MAP = {
    'jäsenet': 'participant',
    'ledamöter': 'participant',

    'asiantuntija': 'expert',
    'asiantuntijat': 'expert',

    'muut': 'other',
    'övriga': 'other'
}

LOCAL_TZ = pytz.timezone('Europe/Helsinki')

LOG = logging.getLogger(__name__)


def parse_xml(source, except_treshold=logging.CRITICAL):
    """
    Parse given XML file to a document.

    :type source: file|str
    :param source: The XML file as a file object or a filename
    :type except_treshold: int
    :param except_treshold:
      Logging message threshold level.  If a message with the given or
      any higher level is logged while parsing, then an exception is
      thrown.
    :raises ParseError: if there is an error in parsing
    :rtype: Document
    """
    return XmlParser().parse(source, except_treshold)


class ParseError(Exception):
    pass


DATE_RANGE_RX = re.compile(
    # Optional day prefix, e.g. 'Tiistai ' or ''
    r'(?:\w+ )?'
    # Date, e.g. '29.8.2017' = GROUP 1
    r'(\d{1,2}.\d{1,2}.\d{4})'
    # Optional clock word, e.g. 'kello ', 'klo ', 'klockan ', or ''
    r' (?:\w+ )?'
    # Start time, e.g. '7:25' = GROUP 2
    r'(\d{1,2}[:.]\d\d)'
    # Separator dash, e.g. ' - ' or '-'
    r' ?- ?'
    # End time, e.g. '9:40' = GROUP 3
    r'(\d{1,2}[:.]\d\d)')


class XmlParser:
    @classmethod
    def clean_html(cls, raw):
        # TODO
        return ''.join([str(etree.tostring(el)) for el in raw])

    @classmethod
    def parse_funcid(cls, raw):
        """
        Parse given function id to a sensible format.

        :type raw: str
        :param raw:
          The function id as it appears in Ahjo XMLs.
          Example: 00 00 03 Valtuuston aloitetoiminta
        :rtype: tuple(str, str)
        :return:
          A tuple with the number part and the text part.
          With the given example this would be ('00 00 03',
          'Valtuuston aloitetoiminta')
        """

        if raw is None:
            return (None, None)

        match = re.fullmatch(r'((?:\d\d ){0,}\d\d) (.*)', raw)
        return (match.group(1), match.group(2))

    @classmethod
    def parse_name(cls, name):
        """
        Parse human names

        :type raw: str
        :param raw: Name in the format 'last, first'
        :rtype: str
        :return: Name in the format 'first last'
        """

        if ', ' in name:
            name = name.split(', ')
            name = '{} {}'.format(name[1], name[0])

        return name

    @classmethod
    def parse_guid(cls, raw):
        """
        Parse and validate GUIDs.

        :type raw: str
        :param raw:
          GUID in the format {123E4567-E89B-12D3-A456-426655440000}
        :rtype: str
        :return: GUID in the format 123e4567-e89b-12d3-a456-426655440000
        :raises ParseError: if the guid isn't in the specified format
        """

        if raw is None:
            return None

        guid_match = re.fullmatch(r'\{([A-F0-9]{8}-(?:[A-F0-9]{4}-){3}[A-F0-9]{12})\}', raw)
        if guid_match is not None:
            return guid_match.group(1).lower()
        else:
            raise ParseError("Invalid GUID format")

    @classmethod
    def parse_datetime(cls, raw):
        """
        Parse timestamps appearing in the AHJO xml.

        :type raw: str
        :param raw: Timestamp in one of the specified formats
        :rtype: datetime
        :return: A localized datetime object
        :raises ParseError: if the date isn't in any of the specified formats
        """

        if raw is None:
            return None

        date = None

        formats = [
            '%m/%d/%Y %I:%M:%S %p',
            '%m/%d/%Y %H:%M:%S',

            '%d.%m.%Y %I:%M:%S %p',
            '%d.%m.%Y %H:%M:%S',
        ]

        for fmt in formats:
            try:
                date = datetime.datetime.strptime(raw, fmt)
                break
            except ValueError as r:
                pass

        if date is None:
            raise ParseError('Unknown timestamp')

        return LOCAL_TZ.localize(date)

    @classmethod
    def parse_datetime_range(cls, raw):
        """
        Parse datetime range string to a pair of datetimes.

        :type raw: str|None
        :rtype: (datetime.datetime, datetime.datetime)|None
        """
        m = DATE_RANGE_RX.match(raw or '')
        if not m:
            return None
        date_str = m.group(1)
        start_str = date_str + ' ' + m.group(2).replace('.', ':')
        end_str = date_str + ' ' + m.group(3).replace('.', ':')
        try:
            start = datetime.datetime.strptime(start_str, '%d.%m.%Y %H:%M')
            end = datetime.datetime.strptime(end_str, '%d.%m.%Y %H:%M')
        except ValueError:
            return None
        return (start, end)

    @classmethod
    def gt(cls, parent, el_name, log=lambda x: None, fmt=lambda x: x):
        """
        Get text of an element. If the element doesn't exist, we
        log something using the log parameter.

        :type parent: Element
        :param parent: Parent element where the element should be searched format

        :type el_name: str
        :param el_name: Name of the child element

        :type log: function
        :param log: Logger function to be called if the element isn't found

        :type fmt: function
        :param fmt: If present, will be called with the retrieved text

        :rtype: str or None
        :return: Text of an element if found. None otherwise.
        """

        el = parent.find(el_name)
        if el is None:
            log("Element {} not found".format(el_name))
            return None
        else:
            content = el.text
            if content is None:
                log("Element {} is empty".format(el_name))
                return content

            return fmt(content)

    def import_attendees(self, ctx, lasnaolotiedot):
        """
        Parse attendees of an event.

        Simplified example structure::
          <Lasnaolotiedot>
            <Osallistujaryhma>
                <OsallistujaryhmaOtsikko>Jäsenet</OsallistujaryhmaOtsikko>
                <Osallistujat>
                  <Nimi>Lastname, Firstname</Nimi>
                  <Titteli>some title</Titteli>
                  <OsallistujaOptiot>
                    <Rooli>puheenjohtaja</Rooli>
                  </OsallistujaOptiot>
                </Osallistujat>
          </Lasnaolotiedot>

        Returned list::
          [
            {
              'name': 'Firstname Lastname',
              'role': 'puheenjohtaja',
              'title': 'some title',
              'category': 'participant'
              }
          ]
        """

        ret = []

        attendee_group_els = lasnaolotiedot.findall('.//Osallistujaryhma')

        for attendee_group_el in attendee_group_els:
            group_name = self.gt(attendee_group_el, 'OsallistujaryhmaOtsikko', ctx.error)
            attendees = attendee_group_el.findall('Osallistujat')

            for attendee in attendees:
                a_attrs = {}

                name = attendee.find('Nimi')
                if name is not None and name.text:
                    a_attrs['name'] = self.parse_name(name.text)
                else:
                    ctx.warning("Attendee doesn't have a name")
                    continue

                opts = attendee.find('OsallistujaOptiot')
                if opts is not None:
                    _set_if_non_empty(a_attrs, 'role', self.gt(opts, 'Rooli'))

                _set_if_non_empty(a_attrs, 'title', self.gt(attendee, 'Titteli'))

                category = ATTENDEE_MAP.get((group_name or '').lower())
                a_attrs['category'] = (category or 'participant')

                ret.append(a_attrs)

        return ret

    def import_event(self, ctx, data1, data2):
        """
        Parse an event's metadata from the document.

        A single document only contains one event, so this function
        only exists to split the code around a little.
        """

        attrs = {}

        if data1 is not None:
            lasnaolotiedot = data1.find('Lasnaolotiedot')
            attrs['attendees'] = self.import_attendees(ctx, lasnaolotiedot)

            kokoustiedot = data1.find('Kokoustiedot')
            location = self.gt(kokoustiedot, 'Kokouspaikka')
            if location:
                attrs['location'] = location

            # format: dd.mm.yyyy hh:mm - hh:mm, possible extra stuff

            # This should be probably improved at some point but it's hard to Convert
            # all cases because it's not standard in any way. Sometimes there are breaks
            # or the event has been held in multiple sessions at different times. How
            # would this even be represented in the database?
            datetime_str = self.gt(kokoustiedot, 'Kokousaika')
            date_range = self.parse_datetime_range(datetime_str)
            if date_range:
                attrs['start_date'] = LOCAL_TZ.localize(date_range[0])
                attrs['end_date'] = LOCAL_TZ.localize(date_range[1])

        if data2 is not None:
            attrs['name'] = '{} {}'.format(self.gt(data2, 'Paattaja'), self.gt(data2, 'Asiakirjatunnus'))
        else:
            attrs['name'] = ''

        if not attrs.get('start_date') and data2 is not None:
            date_str = self.gt(data2, 'Paivays')
            if date_str:
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                attrs['start_date'] = LOCAL_TZ.localize(date)
                attrs['end_date'] = LOCAL_TZ.localize(date)

        if not attrs.get('start_date') or not attrs.get('end_date'):
            raise ParseError('No date information found')

        return attrs

    def import_content(self, ctx, content):
        """
        Parse the content section of a single action.
        """

        if content is None:
            return None

        s = ""

        for section in content:
            heading = self.gt(section, 'SisaltoOtsikko')
            if heading is not None:
                s += '<h2>{}</h2>\n'.format(heading)

            mystery = section.find('TekstiSektio/taso1')
            if mystery is not None:
                for el in mystery:
                    if el.tag == 'Kappale':
                        s += '<p>{}</p>\n'.format(self.gt(el, 'KappaleTeksti'))
                    elif el.tag == 'Otsikko':
                        s += '<h3>{}<h3>\n'.format(el.text)
                    elif el.tag == 'XHTML':
                        s += self.clean_html(el)

            return s

    def import_action(self, ctx, action):
        """
        Parse a single action.
        """

        attrs = {}

        metadata = action.find('KuvailutiedotOpenDocument')

        vakiopaatos = False
        asktieto = self.gt(metadata, 'AsiakirjallinenTieto')
        if asktieto is not None and 'vakiopäätös' in asktieto:
            vakiopaatos = True

        attrs['title'] = self.gt(metadata, 'Otsikko', ctx.warning)
        ctx.current_action = attrs['title']

        (function_id, function_name) = self.parse_funcid(
            self.gt(metadata, 'Tehtavaluokka', ctx.warning))
        _set_if_non_empty(attrs, 'function_id', function_id)
        _set_if_non_empty(attrs, 'function_name', function_name)

        case_guid = self.parse_guid(self.gt(metadata, 'AsiaGuid'))
        if case_guid is None and not vakiopaatos:
            ctx.error("Action doesn't have an associated case")
        _set_if_non_empty(attrs, 'case_guid', case_guid)

        _set_if_non_empty(
            attrs, 'date',
            self.parse_datetime(self.gt(metadata, 'Paatospaiva', ctx.error)))
        article_number = self.gt(metadata, 'Pykala', ctx.error, fmt=int)
        if article_number is not None:
            attrs['article_number'] = article_number

        register_id = self.gt(metadata, 'Dnro/DnroLyhyt')
        if register_id is None and not vakiopaatos:
            ctx.error("Action doesn't have a register id (diaarinumero)")
        _set_if_non_empty(attrs, 'register_id', register_id)

        resolution_el = metadata.find('Asiakirjantila')

        if resolution_el is not None:
            try:
                attrs['resolution'] = RESOLUTION_MAP[resolution_el.text.lower()]
            except KeyError:
                ctx.warning("Unknown resolution type: {}".format(resolution_el.text))
        else:
            ctx.warning("Action doesn't have a resolution")

        content = action.find('SisaltoSektioToisto')
        attrs['content'] = self.import_content(ctx, content)

        keywords = action.findall('Asiasana')
        attrs['keywords'] = [{'name': kw.text} for kw in keywords]

        attrs['attachments'] = []
        attachments = action.findall('LiitteetOptio/Liitteet/LiitteetToisto')
        for a in attachments:
            attrs['attachments'].append({
                'id': self.parse_guid(self.gt(a, 'LiitteetId')),
                'name': self.gt(a, 'Liiteteksti'),
                'ordering': self.gt(a, 'Liitenumero', fmt=int)
            })

        return attrs

    def import_document(self, ctx, root):
        """
        Parse a single 'pöytäkirja' or 'viranhaltijan päätös'.
        """

        attrs = {}

        event_metadata = root.find('PkKansilehtiSektio/KansilehtiToisto')
        event_metadata2 = root.find('YlatunnisteSektio')

        actions = root.find('Paatokset')

        attrs['type'] = 'minutes'
        attrs['event'] = self.import_event(ctx, event_metadata, event_metadata2)
        attrs['event']['actions'] = [self.import_action(ctx, ac) for ac in actions]

        # If this is a viranhaltijan päätös, we will add the
        # viranhaltija as the only person to the attendees.
        signatures = root.find('SahkoinenAllekirjoitusSektio')
        if signatures is None:
            signatures = root.find('AllekirjoitusSektio')
            chairman = signatures.find('PuheenjohtajaSektio').find('PuheenjohtajaToisto')
            name = chairman.find('Puheenjohtajanimi').text

            if name not in [a['name'] for a in attrs['event']['attendees']]:
                attrs['event']['attendees'].append({
                    'name': name,
                    'role': 'viranhaltija',
                })

        return attrs

    def import_esityslista(self, ctx, root):
        raise NotImplementedError("Parsing of agendas is not implemented")

    def parse(self, source, except_treshold=logging.CRITICAL):
        """
        Initiate parsing of a single document.
        """

        filename = source if isinstance(source, str) else source.name
        ctx = ParseContext(filename, except_treshold)

        xml = etree.parse(source)
        root = xml.getroot()

        if root.tag == 'Poytakirja':
            data = self.import_document(ctx, root)
        elif root.tag == 'Esityslista':
            data = self.import_esityslista(ctx, root)
        else:
            raise ValueError("Unknown root tag: {!r}".format(root.tag))

        return Document(data, ctx.errors)


def _set_if_non_empty(mapping, key, value):
    if value:
        mapping[key] = value


class ParseContext:
    """
    Helper class for easing the tracking of errors.
    """

    def __init__(self, filename, except_treshold=logging.CRITICAL):
        self.filename = filename
        self.errors = []
        self.except_treshold = except_treshold
        self.current_action = None

    def log(self, severity, msg):
        human_readable = '{} (File: {}, Action: {})'.format(msg, self.filename, self.current_action)
        LOG.log(severity, human_readable)

        attrs = ['current_action']

        state = {attr: getattr(self, attr) for attr in attrs}
        state['filename'] = self.filename

        self.errors.append({
            'msg': msg,
            'severity': severity,
            'state': state
        })

        if severity >= self.except_treshold:
            raise ParseError(msg)

    def critical(self, msg):
        self.log(logging.CRITICAL, msg)

    def error(self, msg):
        self.log(logging.ERROR, msg)

    def warning(self, msg):
        self.log(logging.WARNING, msg)

    def info(self, msg):
        self.log(logging.INFO, msg)

    def debug(self, msg):
        self.log(logging.DEBUG, msg)
