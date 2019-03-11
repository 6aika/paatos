# -*- coding: utf-8 -*-

import datetime

from decisions.importer.helsinki.ahjo.parse_dirlist import (
    parse_dir_listing, parse_file_path)

EXAMPLE_ROOT_LISTING = r"""
<html><head><title>openhelsinki.hel.fi - /files/</title></head>
<body><H1>openhelsinki.hel.fi - /files/</H1><hr>\r\n\r\n
<pre>
<A HREF="/">[To Parent Directory]</A><br><br>

 5/23/2017 10:04 AM        &lt;dir&gt;
 <A HREF="/files/Asuntolautakunta_60014/">
Asuntolautakunta_60014</A><br>

 5/29/2017 10:04 AM        &lt;dir&gt;
 <A HREF="/files/Asuntotuotantotoimikunta_60011/">
Asuntotuotantotoimikunta_60011</A><br>

11/22/2014 11:02 AM        &lt;dir&gt;
 <A HREF="/files/Henkiloston%20kehittamispalvelut-liikelaitos_01900/">
Henkiloston kehittamispalvelut-liikelaitos_01900</A><br>

 6/21/2017  1:00 PM        &lt;dir&gt;
 <A HREF="/files/Kaupunkiymparistolautakunta_U540/">
Kaupunkiymparistolautakunta_U540</A><br>

 5/24/2017 10:04 AM        &lt;dir&gt;
 <A HREF="/files/Ymparistolautakunta_12800/">
Ymparistolautakunta_12800</A><br>

</pre><hr></body></html>
""".replace('\n', '').replace(r'\r\n', '\r\n').encode('utf-8')

EXAMPLE_ROOT_LISTING_PARSED = [
    dict(
        href='/files/Asuntolautakunta_60014/',
        mtime=datetime.datetime(2017, 5, 23, 10, 4), size=None, type='dir'),
    dict(
        href='/files/Asuntotuotantotoimikunta_60011/',
        mtime=datetime.datetime(2017, 5, 29, 10, 4), size=None, type='dir'),
    dict(
        href='/files/Henkiloston%20kehittamispalvelut-liikelaitos_01900/',
        mtime=datetime.datetime(2014, 11, 22, 11, 2), size=None, type='dir'),
    dict(
        href='/files/Kaupunkiymparistolautakunta_U540/',
        mtime=datetime.datetime(2017, 6, 21, 13, 0), size=None, type='dir'),
    dict(
        href='/files/Ymparistolautakunta_12800/',
        mtime=datetime.datetime(2017, 5, 24, 10, 4), size=None, type='dir'),
]

EXAMPLE_SUBDIR_LISTING = r"""
<html><head><title>openhelsinki.hel.fi - /files/Tietokeskus_02300
/Tilasto- ja tietopalvelupaallikko_023400VH1/
</title></head><body>
<H1>openhelsinki.hel.fi - /files/Tietokeskus_02300
/Tilasto- ja tietopalvelupaallikko_023400VH1/
</H1>
<hr>\r\n\r\n
<pre>
<A HREF="/files/Tietokeskus_02300/">[To Parent Directory]</A><br><br>

  1/5/2016 11:06 AM       129710
 <A HREF="/files/Tietokeskus_02300/
Tilasto-%20ja%20tietopalvelupaallikko_023400VH1/
Tieke%202016-01-04%20023400VH1%201%20Pk%20Su.zip">
Tieke 2016-01-04 023400VH1 1 Pk Su.zip</A><br>

 4/29/2016 10:00 AM       147886
 <A HREF="/files/Tietokeskus_02300/
Tilasto-%20ja%20tietopalvelupaallikko_023400VH1/
Tieke%202016-04-28%20023400VH1%202%20Pk%20Su.zip">
Tieke 2016-04-28 023400VH1 2 Pk Su.zip</A><br>

10/27/2016 10:03 AM       179324
 <A HREF="/files/Tietokeskus_02300/
Tilasto-%20ja%20tietopalvelupaallikko_023400VH1/
Tieke%202016-10-26%20023400VH1%203%20Pk%20Su.zip">
Tieke 2016-10-26 023400VH1 3 Pk Su.zip</A><br>

  1/5/2017 11:03 AM       137011
 <A HREF="/files/Tietokeskus_02300/
Tilasto-%20ja%20tietopalvelupaallikko_023400VH1/
Tieke%202017-01-03%20023400VH1%201%20Pk%20Su.zip">
Tieke 2017-01-03 023400VH1 1 Pk Su.zip</A><br>

</pre><hr></body></html>
""".replace('\n', '').replace(r'\r\n', '\r\n').encode('utf-8')

prefix = (
    '/files/Tietokeskus_02300/'
    'Tilasto-%20ja%20tietopalvelupaallikko_023400VH1/')

EXAMPLE_SUBDIR_LISTING_PARSED = [
    dict(
        href=prefix + 'Tieke%202016-01-04%20023400VH1%201%20Pk%20Su.zip',
        mtime=datetime.datetime(2016, 1, 5, 11, 6), size=129710, type='file'),
    dict(
        href=prefix + 'Tieke%202016-04-28%20023400VH1%202%20Pk%20Su.zip',
        mtime=datetime.datetime(2016, 4, 29, 10, 0), size=147886, type='file'),
    dict(
        href=prefix + 'Tieke%202016-10-26%20023400VH1%203%20Pk%20Su.zip',
        mtime=datetime.datetime(2016, 10, 27, 10, 3), size=179324, type='file'),
    dict(
        href=prefix + 'Tieke%202017-01-03%20023400VH1%201%20Pk%20Su.zip',
        mtime=datetime.datetime(2017, 1, 5, 11, 3), size=137011, type='file'),
]


def test_root_listing():
    result = parse_dir_listing(EXAMPLE_ROOT_LISTING)
    result_data = expand_dir_entries(result)
    assert result_data == EXAMPLE_ROOT_LISTING_PARSED


def test_subdir_listing():
    result = parse_dir_listing(EXAMPLE_SUBDIR_LISTING)
    result_data = expand_dir_entries(result)
    assert result_data == EXAMPLE_SUBDIR_LISTING_PARSED


def expand_dir_entries(dir_entries):
    return [
        dict(href=x.href, mtime=x.mtime, size=x.size, type=x.type)
        for x in dir_entries]


def test_parse_file_path():
    info = parse_file_path(EXAMPLE_SUBDIR_LISTING_PARSED[0]['href'])
    assert info == {
        'org': 'Tieke',
        'date': '2016-01-04',
        'policymaker': '023400VH1',
        'meeting_nr': 1,
        'doc_type_id': 'Pk',
        'doc_type': 'minutes',
        'language': 'fi',
        'language_id': 'Su',
        'policymaker_abbr': '023400VH1',
        'policymaker_id': '023400VH1',
        'year': 2016,
        'origin_id': 'Tieke_023400VH1_2016-1_Pk',
    }
