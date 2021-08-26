from datetime import datetime

def test_get_week_num():
    from util.utils import get_week_num
    # 1号为周四
    assert get_week_num(2021, 7, 1) == 1
    assert get_week_num(2021, 7, 14) == 2
    # 1号为周日
    assert get_week_num(2021, 8, 1) == 0
    assert get_week_num(2021, 8, 4) == 1
    assert get_week_num(2021, 8, 11) == 2


def test_get_xmm_maxtry():
    from util.utils import get_xmm_maxtry
    # 周三
    assert get_xmm_maxtry(datetime(2021, 8, 4)) == 3
    # 周日
    assert get_xmm_maxtry(datetime(2021, 8, 1)) == -1
    # 周五
    assert get_xmm_maxtry(datetime(2021, 8, 6)) == 1