# https://gist.github.com/74l35rUnn3r/f689bce5b6abb15d0185a4754e4e6da5 소스를 기반으로 여러가지 수정

import asyncio
import time
import re
import math
import aiohttp
from aiohttp.client import request
import discord
from discord import channel
from pyquery import PyQuery as pq
import json
from log import logger
from discord.ext import commands
from constants import ip_address, arca_proxy_port, dcinside_proxy_url
import random

sessions = dict()
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}


def make_session_if_not_exists(auth: dict) -> aiohttp.ClientSession:
    global sessions
    id = auth['id']
    if id in sessions:
        return sessions[id]
    sess = aiohttp.ClientSession(headers=header)
    sessions[id] = sess
    return sess


def set_session(sess: aiohttp.ClientSession, id: int) -> None:
    global sessions
    sessions[id] = sess


async def captcha_response(bot: commands.Bot, ctx: commands.context, link: str):
    channel = ctx.message.channel

    logger.info(f"Captcha generated")
    ask: discord.Message = await channel.send(f"""캡챠 발생!
{link} 주소로 가셔서 로그인 후 삭제를 클릭 후 캡챠를 풀어주세요.
캡챠를 푸신 다음, 이모지를 클릭 해주세요.""")
    await ask.add_reaction('🆗')
    def check(payload: discord.RawReactionActionEvent):
        return payload.message_id == ask.id and payload.user_id == ctx.author.id and str(payload.emoji) == '🆗'

    try:
        await bot.wait_for('raw_reaction_add', check=check, timeout=300.0)
    except asyncio.TimeoutError:
        logger.info("Timeout")
        return False
    logger.info(f"Reaction clicked")
    await channel.send("해제 완료!")
    return True

async def get_nickname(auth, _type: str = 'posting', _gall_no: str = '0') -> str:
    sess = make_session_if_not_exists(auth)
    _id = auth['id']
    gallog_url = f'https://gallog.dcinside.com/{_id}/{_type}'
    _url = f"{gallog_url}?gno={_gall_no}"
    res = await sess.get(_url)
    text = await res.text()
    _d = pq(text)
    found = _d('.nick_name').text()
    return found


async def get_num(auth, _type: str = 'posting', _gall_no: str = '0') -> str:
    sess = make_session_if_not_exists(auth)
    await login(sess, auth)
    _id = auth['id']
    gallog_url = f'https://gallog.dcinside.com/{_id}/{_type}'
    _url = f"{gallog_url}?gno={_gall_no}"
    res = await sess.get(_url)
    text = await res.content.read()
    _d = pq(text)
    raw_num = _d('.tit > .num').text()
    raw_num = raw_num.replace(',', '')
    regex = re.compile('[\(](\d+)[\)]')
    matched = regex.match(raw_num)
    found = matched.group(1)
    return found


async def login(sess: aiohttp.ClientSession, auth: dict) -> aiohttp.ClientSession:
    if sess is None:
        sess = make_session_if_not_exists(auth)
    _id = auth['id']
    _pw = auth['pw']
    _url = 'https://www.dcinside.com/'
    res = await sess.get(_url)
    text = await res.content.read()
    _d = pq(text)
    _data = dict(_d('#login_process input').serialize_dict())
    _data['user_id'] = _id
    _data['pw'] = _pw
    time.sleep(1)  # 차단먹지마
    res = await sess.get(_url)
    text = await res.content.read()
    _d = pq(text)
    login_header = {
        **header,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'dcid.dcinside.com',
        'Origin': 'https://www.dcinside.com',
        'Referer': 'https://www.dcinside.com/',
    }
    _r = await sess.post('https://dcid.dcinside.com/join/member_check.php', data=_data, headers=login_header)
    if 'history.back(-1)' in await _r.text():
        raise Exception('login error')
    return sess


async def clean(bot: discord.Client, ctx: commands.Context, sess, _id: str, _type: str = 'posting', _gall_no: str = '0'):
    channel = ctx.channel
    if _type not in ['posting', 'comment']:
        print("Wrong type")
        return
    gallog_url = f'https://gallog.dcinside.com/{_id}/{_type}'
    _url = f"{gallog_url}?gno={_gall_no}"
    res = await sess.get(_url)
    text = await res.content.read()
    _d = pq(text)
    _last = _d('.cont_head.clear > .choice_sect > button.on > .num').text()
    _last = math.ceil(int(_last[1:-1].replace(',', '')) / 20)
    print(_last, 'pages')
    time.sleep(1)

    for _page in range(_last, 0, -1):
        _p_url = f"{_url}&p={str(_page)}"
        res = await sess.get(_p_url)
        cookies = res.cookies
        text = await res.content.read()
        _d = pq(text)
        for _li in _d('ul.cont_listbox > li').items():
            no = _li.attr('data-no')
            _data = {
                'ci_t': cookies.get('ci_c'),
                'no': no,
                'service_code': 'undefined' # 갤로그 개편 fix
            }
            new_header = {
                **header,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Host': 'gallog.dcinside.com',
                'Origin': 'https://gallog.dcinside.com',
                'Referer': _p_url,
                'X-Requested-With': 'XMLHttpRequest'
            }
            time.sleep(random.uniform(0.8, 2.2))
            url = f'https://gallog.dcinside.com/{_id}/ajax/log_list_ajax/delete'
            res = await sess.post(url, data=_data, headers=new_header)
            text = await res.read()
            _r_delete = json.loads(text)
            print(f"{no}: {_r_delete}")
            if _r_delete['result'] in ['captcha', 'fail']:
                url = 'https://github.com/DPS0340/CLEANERBOT/releases/'
                await channel.send("캡챠를 해제하기 위해, hosts 파일 변경이 필요합니다. 로컬 DNS와 프록시 서버를 통해 캡챠를 우회하고 있습니다.")
                await channel.send(f"{url} 에서 실행 파일을 받고 관리자 권한으로 실행해주세요!")
                await asyncio.sleep(1)
                proxy_url = f"{dcinside_proxy_url}/{_id}/{_type}"
                captcha_status = await captcha_response(bot, ctx, proxy_url)
                if captcha_status == False:
                    return


async def loginAndClean(bot: discord.Client, ctx: commands.Context, auth: dict, posting: bool = True, comment: bool = True):
    logger.info(f"author: {ctx.author}")
    logger.info(f"message content: {ctx.message.content}")
    logger.info(f"posting: {posting}, comment: {comment}")
    sess = await login(None, auth)
    if posting:
        logger.info(f"cleaning posting...")
        await clean(bot, ctx, sess, auth['id'], 'posting')
    if comment:
        await clean(bot, ctx, sess, auth['id'], 'comment')


async def cleanArcaLive(bot: discord.Client, ctx: commands.Context, id: str, pw: str, nickname: str, posting: bool = True, comment: bool = True):
    channel = ctx.message.channel

    s = aiohttp.ClientSession(headers=header)

    await s.get('https://arca.live')
    loginPage = await s.get('https://arca.live/u/login?goto=/')

    text = await loginPage.content.read()
    _d = pq(text)

    csrf = _d('input[name$="_csrf"]').val()

    LOGIN_INFO = {
        "username": id,
        "password": pw
    }

    LOGIN_INFO = {'_csrf': csrf, 'goto': '/', **LOGIN_INFO}
    await s.post('https://arca.live/u/login', data=LOGIN_INFO)

    # 글 삭제 시작 인덱스
    # 0부터 시작해서 삭제되지 않는 글이 있을경우 1씩 증가함
    # 인덱스 전의 삭제 가능한 글들은 삭제되었음을 암시적으로 의미함
    idx = 0

    while True:
        links = []
        page = await s.get("https://arca.live/u/@%s" % nickname)

        text = await page.content.read()
        _d = pq(text)

        for parent in _d('div.col-title').items():
            parent.items()
            child = parent('a').items()
            for a in child:
                link = a.attr('href')
                links.append(link)
        if not posting:
            links = list(filter(lambda x: '#c_' in x, links))
        if not comment:
            links = list(filter(lambda x: '#c_' not in x, links))
        if not links or len(links) <= idx:
            break

        for i in range(idx, len(links)):
            try:
                link = links[i]
                link = link.replace('?showComments=all', '')
                if "#c_" in link:
                    link = link.replace("#c_", "/")
                original_link = link
                link = f'https://arca.live{link}/delete'
                proxy_link = f'http://{ip_address}:{arca_proxy_port}{original_link}/delete'
                delete_page = await s.get(link)

                captcha_status = await captcha_response(bot, ctx, proxy_link)
                if captcha_status == False:
                    return
                text = await delete_page.content.read()
                _d = pq(text)
                csrf = _d('input[name$="_csrf"]').val()
                csrfdict = {'_csrf': csrf}
                time.sleep(random.uniform(0.8, 2.2)) # 캡챠 방지용
                res = await s.post(link, data=csrfdict)
                if res.status == 429:

                    res = await s.post(link, data=csrfdict)
                elif not (res.status == 200 or res.status == 302):
                    # 삭제할 수 없는 글일시
                    # 삭제 인덱스 + 1 후 refresh
                    idx += 1
                    break
            except TypeError:
                continue

    await channel.send("삭제 완료!")
