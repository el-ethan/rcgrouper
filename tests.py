from mock import Mock

from rcgrouper import Page, ROOT_URL

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
    assert page.get_kw_matches()[0] == ROOT_URL + 'showthread.php?s=b361e21c350552894dd3b99351cb9cfe&t=2749775'

def test_case_insensitive():
    mock_config = Mock()
    mock_config.get.return_value = "cobra"
    page = Page(raw_page, config=mock_config)
    assert page.get_kw_matches()[0] == ROOT_URL + 'showthread.php?s=b361e21c350552894dd3b99351cb9cfe&t=2749775'

    mock_config.get.return_value = "COBRA"
    page = Page(raw_page, config=mock_config)
    assert page.get_kw_matches()[0] == ROOT_URL + 'showthread.php?s=b361e21c350552894dd3b99351cb9cfe&t=2749775'

def test_multi_match():
    mock_config = Mock()
    mock_config.get.return_value = "Cobra, Emax, Tiny Whoop"
    page = Page(raw_page, config=mock_config)
    matches = page.get_kw_matches()
    assert ROOT_URL + 'showthread.php?s=b361e21c350552894dd3b99351cb9cfe&t=2749775' in matches
    assert ROOT_URL + '123' in matches
    page.popup()
