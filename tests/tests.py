import pytest
import ConfigParser
from datetime import datetime, timedelta
from mock import Mock, patch

from ..rcgrouper import Page, set_expiration_date, DATE_FORMAT, cleanup_matches, MATCH_FILE

CONFIG_OBJ = ConfigParser.RawConfigParser()

def setup_module():
    test_config_path = 'test.grouper.cfg'
    open(test_config_path, 'w').close()
    with open('matches.txt', 'w+') as f:
        f.write('123')
    CONFIG_OBJ.read(test_config_path)
    CONFIG_OBJ.add_section('rcgrouper')
    with open(test_config_path, 'wb') as config:
        CONFIG_OBJ.write(config)

def teardown_module():
    open('matches.txt', 'w').close()

raw_page = """
    <html>
    <body>
    <a class="fsw-title" data-tip="I am selling (5) Cobra 2204/28 2300kv motors. (4) of them have been used since February of this year and (1) is brand new and never used. Purchased all five at the same time so they are from the same..." href="showthread.php?s=b361e21c350552894dd3b99351cb9cfe&amp;t=2749775" id="thread_title_2749775" rel="tooltip">Five Cobra 2204/28 2300kv Motors - with FREE shipping!</a>
    <a href='123'>Emax motors for sale</a>
    </body>
    </html>
    """

def test_single_match():
    mock_config = Mock()
    mock_config.get.return_value = "Cobra"
    page = Page(raw_page, config=mock_config)
    assert page.get_kw_matches()[0].attrs['href'] == 'showthread.php?s=b361e21c350552894dd3b99351cb9cfe&t=2749775'

def test_case_insensitive():
    mock_config = Mock()
    mock_config.get.return_value = "cobra"
    page = Page(raw_page, config=mock_config)
    assert page.get_kw_matches()[0].attrs['href'] == 'showthread.php?s=b361e21c350552894dd3b99351cb9cfe&t=2749775'

    mock_config.get.return_value = "COBRA"
    page = Page(raw_page, config=mock_config)
    assert page.get_kw_matches()[0].attrs['href'] == 'showthread.php?s=b361e21c350552894dd3b99351cb9cfe&t=2749775'

def test_multi_match():
    mock_config = Mock()
    mock_config.get.return_value = "Cobra, Emax, Tiny Whoop"
    page = Page(raw_page, config=mock_config)
    matches = [m.attrs['href'] for m in page.get_kw_matches()]
    assert 'showthread.php?s=b361e21c350552894dd3b99351cb9cfe&t=2749775' in matches
    assert '123' in matches

def test_set_expiration_date():
    exp = '1985-03-31'
    CONFIG_OBJ.set('rcgrouper', 'match_expiration', exp)
    assert CONFIG_OBJ.get('rcgrouper', 'match_expiration') == exp

    set_expiration_date(CONFIG_OBJ)
    new_exp = CONFIG_OBJ.get('rcgrouper', 'match_expiration')

    expected_new_exp = datetime.now() + timedelta(weeks=1)
    assert expected_new_exp.strftime(DATE_FORMAT) == new_exp

def test_cleanup_matches_no_exp():
    '''Test that expiration is set during cleanup if not set'''
    CONFIG_OBJ.set('rcgrouper', 'match_expiration', '')
    with patch('rcgrouper.rcgrouper.set_expiration_date') as mock_set_exp:
        cleanup_matches(CONFIG_OBJ)
        assert mock_set_exp.called


@pytest.mark.skip(reason='Patching needs to be sorted out')
@patch('__main__.MATCH_FILE')
def test_cleanup_matches(mock_mf):
    CONFIG_OBJ.set('rcgrouper', 'match_expiration', '1985-03-31')
    now_str = datetime.now().strftime(DATE_FORMAT)
    mock_mf = 'matches.txt'
    cleanup_matches(CONFIG_OBJ)
    assert CONFIG_OBJ.get('rcgrouper', 'match_expiration') ==  now_str
