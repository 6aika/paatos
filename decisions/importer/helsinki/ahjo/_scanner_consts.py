# Paths to skip when scanning (path: reason)
PATHS_TO_SKIP = {
    '/files/' + '/'.join(parts).replace(' ', '%20'): reason
    for (parts, reason) in [
        (('Taloushallintopalvelu-liikelaitoksen jk_71900',
          'Talpa 2013-05-28 Talpajk 3 El Su.zip'), 'duplicate'),
        (('Kaupunginhallituksen konsernijaosto_02978',
          'Halke 2013-08-26 Koja 11 El Su.zip'),  'wrong meeting id'),
        (('Kaupunginhallituksen konsernijaosto_02978',
          'Halke 2013-08-26 Koja 11 Pk Su.zip'), 'wrong meeting id'),
        (('Kaupunginmuseon johtokunta_46113',
          'Museo 2013-08-27 Museojk 7 El Su.zip'), 'wrong meeting id'),
        (('Kaupunginmuseon johtokunta_46113',
          'Museo 2013-08-27 Museojk 7 Pk Su.zip'), 'wrong meeting id'),
        (('Suomenkielisen tyovaenopiston jk_45100',
          'Sto 2013-08-27 Stojk 12 El Su.zip'), 'wrong meeting id'),
        (('Suomenkielisen tyovaenopiston jk_45100',
          'Sto 2013-08-27 Stojk 12 Pk Su.zip'), 'wrong meeting id'),
        (('Taloushallintopalvelu-liikelaitoksen jk_71900'
          'Talpa 2013-11-26 Talpajk 5 El Su.zip'), 'wrong meeting id'),
        (('Keskusvaalilautakunta_11500',
          'Kanslia 2014-09-02 Kvlk 7 El Su.zip'), 'wrong date'),
        (('Liikuntalautakunta_47100',
          'Liv 2014-10-23 LILK 12 El Su.zip'), 'wrong meeting id'),
        (('Pelastuslautakunta_11100',
          'Pel 2014-06-10 PELK 7 El Su.zip'), 'corrupt'),
        (('Liikuntalautakunta_47100',
          'Liv 2014-10-23 LILK 11 El Su.zip'), 'wrong meeting id'),
        (('Liikuntalautakunta_47100',
          'Liv 2014-10-07 LILK 15 El Su.zip'), 'wrong meeting id'),
        (('Taidemuseo_46102', 'Museonjohtaja_46102VH1',
          'Taimu 2104-10-10 46102VH1 26 Pk Su.zip'), 'wrong date'),
        (('Rakennusvirasto_52000', 'Tulosryhman johtaja_521112VH1',
          'HKR 2014-12-16 521112VH1 12 Pk Su.zip'), 'wrong date'),
        (('Sosiaali- ja terveyslautakunta_81000',
          'Sote 2013-06-04 Sotelk 9 Pk Su.zip'), 'missing attachment'),
        (('Sosiaali- ja terveyslautakunta_81000',
          'Sote 2013-06-04 Sotelk 9 El Su.zip'), 'missing attachment'),
    ]
}

# Documents to skip when scanning (origin_id: reason)
DOCS_TO_SKIP = {
    'Opev_SKJ_2013-2_El': '',
    'HKR_Ytlk_2013-18_El': '',
    'Ymk_Ylk_2013-1_El': '',
    'Ork_Orkjk_2014-4_Pk': 'HEL 2014-011315 processed twice',
    'Rakpa_Tplk_2013-1_Pk': 'KuvailutiedotOpenDocument missing',
    'Halke_Khs_2012-27_Pk': 'attachment missing',
    'Halke_Khs_2012-26_Pk': 'attachment missing',
    'HKL_75001VH1_2016-44_Pk': '',
    'Opev_4009211VH1_2015-18_Pk': 'invalid attachment',
    'Rakpa_Tplk_2014-11_Pk': 'KuvailutiedotOpenDocument missing',
    'Kymp_U51105100VH1_2017-21_Pk': 'KuvailutiedotOpenDocument missing',
}
