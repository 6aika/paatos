import datetime

import pytest

from decisions.importer.helsinki.ahjo.xmlparser import XmlParser


@pytest.mark.parametrize('raw,simplified', [
    ('02.02.2016 16:30 - 19:37', '2016-02-02 16:30 19:37'),
    ('05.09.2016 8:00 - 9:15', '2016-09-05 8:00 9:15'),
    ('22.11.2016 16:15 - 19:16, keskeytetty 16:24 - 16:26, 18:17 - 18:20',
     '2016-11-22 16:15 19:16'),
    ('Torstai 3.3.2016 kello 16:00 - 19:04', '2016-03-03 16:00 19:04'),
    ('14.08.2014 15:00 - 15:40', '2014-08-14 15:00 15:40'),
    ('15.11.2012 klo 16:00 - 17:22', '2012-11-15 16:00 17:22'),
    ('26.5.2015 klo 16.00 - 16.33', '2015-05-26 16:00 16:33'),
    ('26.05.2014 8:00 - 9:17', '2014-05-26 8:00 9:17'),
    ('27.10.2014 16:00 - 16:31', '2014-10-27 16:00 16:31'),
    ('Torstai 16.3.2017 kello 16:00 - 16:58', '2017-03-16 16:00 16:58'),
    ('04.04.2012 16:00 - 16:48', '2012-04-04 16:00 16:48'),
    ('Keskiviikko 06.02.2013 kello 8:00 - 11:07', '2013-02-06 8:00 11:07'),
    ('13.04.2016 18:00 - 20:15', '2016-04-13 18:00 20:15'),
    ('27.01.2015 klo 16.55 - 17.10', '2015-01-27 16:55 17:10'),
    ('13.06.2016 16:00 - 18:05, keskeytetty 16:04 - 17:41',
     '2016-06-13 16:00 18:05'),
 ])
def test_parse_datetime_range(raw, simplified):
    (dmy, start_t, end_t) = simplified.split()
    start = datetime.datetime.strptime(dmy + ' ' + start_t, '%Y-%m-%d %H:%M')
    end = datetime.datetime.strptime(dmy + ' ' + end_t, '%Y-%m-%d %H:%M')
    result = XmlParser.parse_datetime_range(raw)
    assert result == (start, end)


def test_parse_datetime_range_specials():
    p = XmlParser.parse_datetime_range
    assert p(None) is None
    assert p('') is None
    assert p('garbage') is None
    assert p('19.19.1999 99:99 - 99:99') is None
