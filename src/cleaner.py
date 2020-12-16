# https://gist.github.com/74l35rUnn3r/f689bce5b6abb15d0185a4754e4e6da5 소스를 기반으로 여러가지 수정

import time
import re
import requests
import math
from pyquery import PyQuery as pq
import re

sessions = dict()

def make_session_if_not_exists(auth):
    global sessions
    id = auth['id']
    if id in sessions:
        return sessions[id]
    sess = requests.Session()
    sess.headers.update({ 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'})
    sessions[id] = sess
    return sess



def decode_service_code(_svc : str, _r : str) -> str:
    _r_key = 'yL/M=zNa0bcPQdReSfTgUhViWjXkYIZmnpo+qArOBs1Ct2D3uE4Fv5G6wHl78xJ9K'
    _r = re.sub('[^A-Za-z0-9+/=]', '', _r)

    tmp = ''
    i = 0
    for a in [_r[i * 4:(i + 1) * 4] for i in range((len(_r) + 3) // 4)]:
        t, f, d, h = [_r_key.find(x) for x in a]
        tmp += chr(t << 2 | f >> 4)
        if d != 64:
            tmp += chr((15 & f) << 4 | (d >> 2))
        if h != 64:
            tmp += chr((3 & d) << 6 | h)
    _r = str(int(tmp[0]) + 4) + tmp[1:]
    if int(tmp[0]) > 5:
        _r = str(int(tmp[0]) - 5) + tmp[1:]

    _r = [float(x) for x in _r.split(',')]
    t = ''
    for i in range(len(_r)):
        t += chr(int(2 * (_r[i] - i - 1) / (13 - i - 1)))
    return _svc[0:len(_svc) - 10] + t

def get_nickname(auth, _type: str = 'posting', _gall_no: str = '0'):
    sess = make_session_if_not_exists(auth)
    _id = auth['id']
    gallog_url = f'https://gallog.dcinside.com/{_id}/{_type}'
    _url = f"{gallog_url}/main?gno={_gall_no}"
    _d = pq(sess.get(_url).text)
    found = _d('.nick_name').text()
    return found

def get_num(auth, _type: str = 'posting', _gall_no: str = '0'):
    sess = make_session_if_not_exists(auth)
    login(sess, auth)
    _id = auth['id']
    gallog_url = f'https://gallog.dcinside.com/{_id}/{_type}'
    _url = f"{gallog_url}/main?gno={_gall_no}"
    _d = pq(sess.get(_url).text)
    raw_num = _d('.tit > .num').text()
    raw_num = raw_num.replace(',', '')
    print(raw_num)
    regex = re.compile('[\(](\d+)[\)]')
    matched = regex.match(raw_num)
    found = matched.group(1)
    return found


def login(sess, auth):
    if sess is None:
        sess = make_session_if_not_exists(auth)
    _id = auth['id']
    _pw = auth['pw']
    _d = pq(sess.get('https://www.dcinside.com/').text)
    _data = dict(_d('#login_process input').serialize_dict())
    _data['user_id'] = _id
    _data['pw'] = _pw
    # print(json.dumps(_data, indent=2, ensure_ascii=False))
    time.sleep(1)  # 차단먹지마
    sess.headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'dcid.dcinside.com',
        'Origin': 'https://www.dcinside.com',
        'Referer': 'https://www.dcinside.com/',
    })
    _r = sess.post('https://dcid.dcinside.com/join/member_check.php', data=_data)
    if 'history.back(-1)' in _r.text:
        raise Exception('login error')
    return sess


def solve_recaptcha(_url: str) -> str:
    input('captcha')
    # secret :D
    return ''


async def clean(bot, ctx, sess, _id: str, _type: str = 'posting', _gall_no: str = '0'):
    channel = ctx.message.channel

    if _type not in ['posting', 'comment']:
        print("Wrong type")
        return
    gallog_url = f'https://gallog.dcinside.com/{_id}/{_type}'
    _url = f"{gallog_url}/main?gno={_gall_no}"
    _d = pq(sess.get(_url).text)
    _last = _d('.cont_head.clear > .tit > .num').text()
    _last = math.ceil(int(_last[1:-1].replace(',', '')) / 20)
    print(_last, 'pages')
    time.sleep(1)   # 차단먹지마

    for _page in range(_last, 0, -1):
        _p_url = f"{_url}&p={str(_page)}"
        _d = pq(sess.get(_p_url).text)
        _r = _d('script[type="text/javascript"]').filter(lambda _, e: 'var _r =' in pq(e).text()).text()
        _r = _r[13:_r.find("');")]
        time.sleep(1)   # 차단먹지마
        for _li in _d('ul.cont_listbox > li').items():
            no = _li.attr('data-no')
            _data = {
                'ci_t': sess.cookies.get('ci_c'),
                'no': no,
                'service_code': decode_service_code(_d('input[name="service_code"]').val(), _r)
            }
            header = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Host': 'gallog.dcinside.com',
                'Origin': 'https://gallog.dcinside.com',
                'Referer': _p_url,
                'X-Requested-With': 'XMLHttpRequest'
            }
            sess.headers.update(header)
            time.sleep(1)   # 차단먹지마
            url = f'https://gallog.dcinside.com/{_id}/ajax/log_list_ajax/delete'
            _r_delete = sess.post(url, data=_data).json()
            print(f"{no}: {_r_delete}")
            if _r_delete['result'] in ['captcha', 'fail']:
                ask = await channel.send(f"""캡챠 발생!
{gallog_url} 주소로 가서 삭제를 클릭 후 캡챠를 풀어주세요.
캡챠를 푸신 다음, 이모지를 클릭 해주세요.""")
                await ask.add_reaction('🆗')
                
                def check(reaction, user):
                    return reaction.message == ask and user == ctx.author and str(reaction.emoji) ==  '🆗'

                await bot.wait_for('reaction_add', check=check)
                await channel.send("해제 완료!")

async def loginAndClean(bot, ctx, auth: dict, posting: bool = True, comment: bool = True):
    sess = login(None, auth)
    if posting:
        await clean(bot, ctx, sess, auth['id'], 'posting')
    if comment:
        await clean(bot, ctx, sess, auth['id'], 'comment')