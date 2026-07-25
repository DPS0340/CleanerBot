# https://gist.github.com/74l35rUnn3r/f689bce5b6abb15d0185a4754e4e6da5 소스를 기반으로 여러가지 수정

import asyncio
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
from constants import ip_address, arca_proxy_port, dcinside_proxy_url, dcinside_gallog_proxy_port
import random
from urllib.parse import quote, quote_plus
from yarl import URL

sessions = dict()
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}

arca_url = 'https://arca.live'
# 아카라이브 로그인 단계 코드 (login.js의 Stage enum)
ARCA_STAGE_CAPTCHA = 3
# 세션 쿠키로 로그인할 때 쓰는 접두사 (clb arca session:<쿠키> <sig> <닉네임>)
ARCA_SESSION_PREFIX = 'session:'


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


def get_cookie_value(sess: aiohttp.ClientSession, name: str, url: str) -> str:
    """세션 쿠키 저장소에서 쿠키 값을 읽는다.

    응답의 res.cookies는 Set-Cookie가 내려오지 않은 요청에서는 비어 있고,
    Morsel 객체를 그대로 폼 데이터에 넣으면 'Set-Cookie: ci_c=...' 문자열이
    전송되어 요청이 실패한다. 따라서 항상 쿠키 저장소에서 값만 꺼내 쓴다.
    """
    cookies = sess.cookie_jar.filter_cookies(URL(url))
    morsel = cookies.get(name)
    return morsel.value if morsel else None


async def post_gallog_delete(sess: aiohttp.ClientSession, url: str, data: dict, headers: dict) -> dict:
    """갤로그 삭제 요청을 보내고 응답을 dict로 반환한다.

    응답이 JSON이 아니거나(점검/차단 페이지 등) 예상 밖의 형태여도
    루프 전체가 죽지 않도록 방어한다.
    """
    res = await sess.post(url, data=data, headers=headers)
    body = await res.read()
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        logger.info(f'delete: invalid response (status={res.status})')
        return {'result': 'error'}
    if not isinstance(parsed, dict):
        return {'result': 'error'}
    return parsed


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
    raw_num = _d('.choice_sect > button > .num').text()
    raw_num = raw_num.replace(',', '')
    matched = re.search(r'\((\d+)\)', raw_num)
    if not matched:
        # 비공개 갤로그이거나 로그인이 풀린 경우
        logger.info(f'get_num: count not found (raw={raw_num!r})')
        return '0'
    return matched.group(1)


async def login(sess: aiohttp.ClientSession, auth: dict) -> aiohttp.ClientSession:
    if sess is None:
        sess = make_session_if_not_exists(auth)
    _id = auth['id']
    _pw = auth['pw']

    redirect_url = f'https://gallog.dcinside.com/{_id}'
    redirect_url = quote_plus(redirect_url)

    _url = f'https://sign.dcinside.com/login?s_url={redirect_url}'
    res = await sess.get(_url)
    text = await res.content.read()
    _d = pq(text)
    _data = dict(_d('.inner form input').serialize_dict())
    _data['user_id'] = _id
    _data['pw'] = _pw
    # 재로그인 등으로 Set-Cookie가 내려오지 않을 수 있어 쿠키 저장소에서 읽는다.
    ci_t = get_cookie_value(sess, 'ci_c', 'https://sign.dcinside.com')
    if ci_t:
        _data['ci_t'] = ci_t
    await asyncio.sleep(1)  # 차단먹지마

    # 비밀번호가 로그에 남지 않도록 마스킹한다.
    logger.info({**_data, 'pw': '***'})

    login_header = {
        **header,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'sign.dcinside.com',
        'Origin': 'https://sign.dcinside.com',
        'Referer': _url,
    }
    _r = await sess.post('https://sign.dcinside.com/login/member_check', data=_data, headers=login_header)

    logger.info(_r.status)

    text = await _r.text()
    logger.info(text)

    if 'location.replace' in text:
        await sess.get('https://sign.dcinside.com/campaign/password_change')
        await sess.get('https://www.dcinside.com')

    return sess


async def clean(bot: discord.Client, ctx: commands.Context, sess, _id: str, _type: str = 'posting', _gall_no: str = '0'):
    channel = ctx.channel
    if _type not in ['posting', 'comment']:
        logger.info("Wrong type")
        return
    gallog_url = f'https://gallog.dcinside.com/{_id}/{_type}'
    _url = f"{gallog_url}?cno={_gall_no}"
    res = await sess.get(_url)
    text = await res.content.read()
    _d = pq(text)
    # 삭제 요청에 쓰이는 service_code 토큰 (log_list.js 참고)
    service_code = _d('input[name="service_code"]').val() or 'undefined'
    _last = _d('.cont_head.clear > .choice_sect > button.on > .num').text()
    matched = re.search(r'\((\d[\d,]*)\)', _last)
    if not matched:
        logger.info(f'{_type}: count not found (raw={_last!r})')
        await channel.send("갤로그 정보를 불러오지 못했습니다. 로그인 상태를 확인해주세요.")
        return
    total = int(matched.group(1).replace(',', ''))
    if total == 0:
        logger.info(f'{_type}: nothing to delete')
        return
    _last = math.ceil(total / 20)
    logger.info(f'{_last} pages')
    await asyncio.sleep(1)

    deleted = 0
    for _page in range(_last, 0, -1):
        _p_url = f"{_url}&p={str(_page)}"
        res = await sess.get(_p_url)
        text = await res.content.read()
        _d = pq(text)
        page_service_code = _d('input[name="service_code"]').val() or service_code
        for _li in _d('ul.cont_listbox > li').items():
            no = _li.attr('data-no')
            if not no:
                continue
            _data = {
                # 쿠키 저장소에서 값만 꺼내야 한다. Morsel을 그대로 넣으면 실패한다.
                'ci_t': get_cookie_value(sess, 'ci_c', gallog_url),
                'no': no,
                'service_code': page_service_code,  # 갤로그 개편 fix
                'c_k_v': 'dzk',
            }
            new_header = {
                **header,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Host': 'gallog.dcinside.com',
                'Origin': 'https://gallog.dcinside.com',
                'Referer': _p_url,
                'X-Requested-With': 'XMLHttpRequest'
            }
            url = f'https://gallog.dcinside.com/{_id}/ajax/log_list_ajax/delete'

            await asyncio.sleep(random.uniform(0.8, 2.2))
            _r_delete = await post_gallog_delete(sess, url, _data, new_header)
            logger.info(f"{no}: {_r_delete}")

            if _r_delete.get('result') == 'captcha':
                release_url = 'https://github.com/DPS0340/CleanerBot/releases/'
                await channel.send("캡챠를 해제하기 위해, hosts 파일 변경이 필요합니다. 로컬 DNS를 수정해 프록시 서버와 연동하는 방법으로 세션을 일치시키고 있습니다.")
                await channel.send(f"{release_url} 에서 실행 파일을 받고 관리자 권한으로 실행해주세요!")
                await asyncio.sleep(1)
                proxy_url = f"{dcinside_proxy_url}:{dcinside_gallog_proxy_port}/{_id}/{_type}"
                captcha_status = await captcha_response(bot, ctx, proxy_url)
                if captcha_status == False:
                    return
                # 캡챠 해제 후에는 실패했던 항목을 다시 시도한다.
                _data['ci_t'] = get_cookie_value(sess, 'ci_c', gallog_url)
                _r_delete = await post_gallog_delete(sess, url, _data, new_header)
                logger.info(f"{no} (retry): {_r_delete}")

            # log_list.js 기준 성공 응답은 result == "success" 이다.
            if _r_delete.get('result') == 'success':
                deleted += 1

    logger.info(f'{_type}: {deleted} deleted')
    return deleted


async def loginAndClean(bot: discord.Client, ctx: commands.Context, auth: dict, posting: bool = True, comment: bool = True):
    logger.info(f"author: {ctx.author}")
    logger.info(f"message content: {ctx.message.content}")
    logger.info(f"posting: {posting}, comment: {comment}")
    sess = await login(None, auth)
    deleted = 0
    if posting:
        logger.info(f"cleaning posting...")
        deleted += await clean(bot, ctx, sess, auth['id'], 'posting') or 0
    if comment:
        deleted += await clean(bot, ctx, sess, auth['id'], 'comment') or 0

    if deleted:
        await ctx.channel.send(f"삭제 완료! {deleted}개를 삭제했습니다.")
    else:
        await ctx.channel.send("삭제된 항목이 없습니다. 로그인 상태와 갤로그를 확인해주세요.")


def normalize_arca_link(link: str) -> str:
    """유저 페이지의 링크를 삭제 페이지 경로로 정규화한다.

    - 글:   /b/{slug}/{articleId}
    - 댓글: /b/{slug}/{articleId}/{commentId}#c_{commentId}
      -> 프래그먼트(#c_...)만 제거하면 이미 댓글 경로가 완성되어 있다.
    """
    if not link:
        return None
    link = link.split('#')[0]
    link = link.split('?')[0]
    link = link.rstrip('/')
    # /b/{채널}/{글번호} 혹은 /b/{채널}/{글번호}/{댓글번호} 형태만 삭제 대상이다.
    if not re.match(r'^/b/[^/]+/\d+(/\d+)?$', link):
        return None
    return link


def is_arca_comment_link(link: str) -> bool:
    return bool(re.match(r'^/b/[^/]+/\d+/\d+$', link))


def is_arca_session_cookie(id: str, pw: str) -> bool:
    """id 인자가 세션 쿠키 로그인 형식인지 판별한다."""
    return bool(id) and id.startswith(ARCA_SESSION_PREFIX) and bool(pw)


async def isArcaLoggedIn(s: aiohttp.ClientSession) -> bool:
    """세션이 실제 로그인 상태인지 확인한다.

    비로그인 상태에서는 상단 네비게이션에 /u/login 링크가 노출된다.
    """
    res = await s.get(arca_url)
    if res.status != 200:
        return False
    text = await res.content.read()
    _d = pq(text)
    return not bool(_d('a[href^="/u/login"]'))


async def loginArcaLive(s: aiohttp.ClientSession, id: str, pw: str) -> dict:
    """아카라이브 로그인.

    2023년 개편 이후 로그인은 단계별 JSON API로 동작한다.
    1) GET /u/login 으로 _csrf 확보
    2) POST /u/login/has_external_sfa (JSON) 로 아이디 확인 및 _csrf 갱신
    3) POST /u/login (JSON) 으로 비밀번호 전송

    id 자리에 세션 쿠키(arca.session2 값)를 넣으면 캡챠 없이 로그인할 수 있다.

    반환값: {'ok': bool, 'reason': str, 'stage': int|None}
    """
    # 캡챠 우회용: 브라우저에서 복사한 세션 쿠키로 로그인
    if is_arca_session_cookie(id, pw):
        session_value = id[len(ARCA_SESSION_PREFIX):]
        s.cookie_jar.update_cookies(
            {'arca.session2': session_value, 'arca.session2.sig': pw},
            response_url=URL(arca_url))
        if await isArcaLoggedIn(s):
            return {'ok': True, 'reason': '', 'stage': None}
        return {'ok': False, 'reason': 'cookie', 'stage': None}

    await s.get(arca_url)
    login_page_url = f'{arca_url}/u/login?goto=/'
    login_page = await s.get(login_page_url)
    text = await login_page.content.read()
    _d = pq(text)
    csrf = _d('input[name$="_csrf"]').val()

    if not csrf:
        return {'ok': False, 'reason': 'csrf', 'stage': None}

    json_header = {
        **header,
        'Content-Type': 'application/json',
        'Origin': arca_url,
        'Referer': login_page_url,
        'X-Requested-With': 'XMLHttpRequest',
    }

    state = {'_csrf': csrf, 'goto': '/', 'username': id}

    res = await s.post(f'{arca_url}/u/login/has_external_sfa',
                       json=state, headers=json_header)
    body = await res.json(content_type=None)
    if body.get('csrf'):
        state['_csrf'] = body['csrf']

    state['password'] = pw
    res = await s.post(f'{arca_url}/u/login', json=state, headers=json_header)
    body = await res.json(content_type=None)
    logger.info(f'arca login status: {res.status}')

    if body.get('csrf'):
        state['_csrf'] = body['csrf']

    if res.status == 200 and body.get('result'):
        stage = body.get('nextstage')
        if stage:
            # 2단계 인증 등 추가 단계가 필요한 계정
            return {'ok': False, 'reason': 'mfa', 'stage': int(stage)}
        return {'ok': True, 'reason': '', 'stage': None}

    if res.status == 428 or body.get('nextstage') == ARCA_STAGE_CAPTCHA:
        return {'ok': False, 'reason': 'captcha', 'stage': ARCA_STAGE_CAPTCHA}

    return {'ok': False, 'reason': body.get('message') or 'invalid', 'stage': None}


async def fetchArcaLinks(s: aiohttp.ClientSession, nickname: str, posting: bool, comment: bool):
    """유저 페이지에서 삭제 대상 글/댓글 경로를 수집한다."""
    user_url = f'{arca_url}/u/@{quote(nickname)}'
    page = await s.get(user_url)
    if page.status != 200:
        logger.info(f'arca user page status: {page.status} ({user_url})')
        return None

    text = await page.content.read()
    _d = pq(text)

    links = []
    for a in _d('div.col-title a').items():
        link = normalize_arca_link(a.attr('href'))
        if link and link not in links:
            links.append(link)

    if not posting:
        links = [x for x in links if is_arca_comment_link(x)]
    if not comment:
        links = [x for x in links if not is_arca_comment_link(x)]

    return links


async def deleteArcaLink(bot: discord.Client, ctx: commands.Context, s: aiohttp.ClientSession, link: str) -> str:
    """글/댓글 하나를 삭제한다. 'deleted' / 'skip' / 'abort' 를 반환한다."""
    delete_url = f'{arca_url}{link}/delete'
    proxy_link = f'{dcinside_proxy_url}:{arca_proxy_port}{link}/delete'

    delete_page = await s.get(delete_url)
    if delete_page.status != 200:
        logger.info(f'{link}: delete page status {delete_page.status}')
        return 'skip'

    text = await delete_page.content.read()
    _d = pq(text)
    csrf = _d(f'form[action="{link}/delete"] input[name$="_csrf"]').val()
    if not csrf:
        csrf = _d('input[name$="_csrf"]').val()
    if not csrf:
        # 로그인이 풀렸거나 삭제 권한이 없는 경우
        logger.info(f'{link}: csrf not found')
        return 'skip'

    post_header = {
        **header,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': arca_url,
        'Referer': delete_url,
    }
    csrfdict = {'_csrf': csrf}

    await asyncio.sleep(random.uniform(0.8, 2.2))  # 캡챠 방지용
    res = await s.post(delete_url, data=csrfdict, headers=post_header)

    if res.status == 429:
        captcha_status = await captcha_response(bot, ctx, proxy_link)
        if captcha_status == False:
            return 'abort'
        res = await s.post(delete_url, data=csrfdict, headers=post_header)

    if res.status in [200, 302]:
        # 삭제 후에도 삭제 페이지가 남아있으면 실제로는 지워지지 않은 것이다.
        check = await s.get(delete_url)
        if check.status == 200:
            logger.info(f'{link}: delete not applied')
            return 'skip'
        return 'deleted'

    logger.info(f'{link}: delete failed with status {res.status}')
    return 'skip'


async def cleanArcaLive(bot: discord.Client, ctx: commands.Context, id: str, pw: str, nickname: str, posting: bool = True, comment: bool = True):
    channel = ctx.message.channel

    s = aiohttp.ClientSession(headers=header)

    try:
        result = await loginArcaLive(s, id, pw)
        if not result['ok']:
            if result['reason'] == 'captcha':
                await channel.send(
                    "아카라이브가 로그인 시 캡챠(Cloudflare Turnstile)를 요구하고 있어 "
                    "아이디/비밀번호로는 로그인할 수 없습니다.")
                await channel.send(
                    "브라우저에서 아카라이브에 로그인한 뒤 쿠키의 `arca.session2`와 "
                    "`arca.session2.sig` 값을 복사해서 아래와 같이 사용해주세요.\n"
                    f"`clb arca {ARCA_SESSION_PREFIX}<arca.session2> <arca.session2.sig> <닉네임>`")
            elif result['reason'] == 'cookie':
                await channel.send(
                    "세션 쿠키가 만료되었거나 올바르지 않습니다. "
                    "브라우저에서 쿠키 값을 다시 복사해주세요.")
            elif result['reason'] == 'mfa':
                await channel.send("2단계 인증이 설정된 계정은 지원하지 않습니다. 아카라이브에서 2단계 인증을 해제한 뒤 다시 시도해주세요.")
            else:
                await channel.send("아카라이브 로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.")
            return

        deleted = 0
        failed = set()

        while True:
            links = await fetchArcaLinks(s, nickname, posting, comment)
            if links is None:
                await channel.send(f"'{nickname}' 유저 페이지를 찾을 수 없습니다. 닉네임을 확인해주세요.")
                return
            # 이미 삭제에 실패한 항목은 다시 시도하지 않는다.
            links = [x for x in links if x not in failed]
            if not links:
                break

            progressed = False
            for link in links:
                status = await deleteArcaLink(bot, ctx, s, link)
                if status == 'abort':
                    await channel.send(f"{deleted}개를 삭제한 뒤 중단되었습니다.")
                    return
                if status == 'deleted':
                    deleted += 1
                    progressed = True
                else:
                    failed.add(link)

            # 유저 페이지는 최근 항목만 보여주므로, 지운 만큼 다음 항목이 드러난다.
            # 이번 회차에 하나도 못 지웠다면 남은 항목은 삭제 불가이므로 종료한다.
            if not progressed:
                break

        if deleted:
            message = f"삭제 완료! {deleted}개를 삭제했습니다."
        else:
            message = "삭제할 수 있는 글/댓글이 없습니다."
        if failed:
            message += f" (삭제할 수 없는 항목 {len(failed)}개는 건너뛰었습니다.)"
        await channel.send(message)
    finally:
        await s.close()
