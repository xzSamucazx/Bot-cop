from __future__ import annotations

import io
import random
import re

import aiohttp
import discord


BAD_APPLE_TRIGGER = re.compile(r"(?<!\w)bad[\s._-]*apple(?!\w)", re.IGNORECASE)
SPOTIFY_URL = "https://open.spotify.com/track/57JRZbE80MLsYbmb24cPee"

BAD_APPLE_BASE_URL = "https://pub-c7c3ded857ab4f55b3b3448c0f9c8c20.r2.dev"

BAD_APPLE_URLS = [
    f"{BAD_APPLE_BASE_URL}/{n}.mp4" for n in range(1, 13)
]

_bad_apple_queue: list[str] = []
_http_session: aiohttp.ClientSession | None = None


async def _get_session() -> aiohttp.ClientSession:
    global _http_session
    if _http_session is None or _http_session.closed:
        _http_session = aiohttp.ClientSession()
    return _http_session


class BadAppleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="🎵 Ouvir no Spotify",
                style=discord.ButtonStyle.link,
                url=SPOTIFY_URL,
            )
        )


def _next_video_url() -> str | None:
    global _bad_apple_queue
    if not BAD_APPLE_URLS:
        return None

    _bad_apple_queue = [url for url in _bad_apple_queue if url in BAD_APPLE_URLS]

    # Embaralha uma nova rodada somente depois de todos os vídeos disponíveis
    # terem sido usados, evitando repetição até completar a biblioteca.
    if not _bad_apple_queue:
        _bad_apple_queue = list(BAD_APPLE_URLS)
        random.shuffle(_bad_apple_queue)

    return _bad_apple_queue.pop(0)


async def _download_video(url: str) -> io.BytesIO | None:
    try:
        session = await _get_session()
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"⚠️ Bad Apple: falha ao baixar {url} (HTTP {resp.status})")
                return None
            data = await resp.read()
            return io.BytesIO(data)
    except aiohttp.ClientError as exc:
        print(f"⚠️ Bad Apple: erro de conexão ao baixar {url}: {exc}")
        return None


def _make_embed(video_url: str) -> discord.Embed:
    return discord.Embed(
        title="🍎 Bad Apple!! — Touhou Project",
        description=(
            "╭・───・☾・୨୧・☽・───・╮\n"
            "        **Bad Apple!!**\n"
            f"╰・───・☾・୨୧・☽・───・[╯]({video_url})"
        ),
        color=discord.Color.dark_gray(),
    )


async def handle_bad_apple(message: discord.Message) -> bool:
    if message.author.bot or not BAD_APPLE_TRIGGER.search(message.content or ""):
        return False

    url = _next_video_url()
    if url is None:
        return False

    buffer = await _download_video(url)
    if buffer is None:
        return False

    try:
        await message.reply(
            embed=_make_embed(url),
            file=discord.File(buffer, filename="Bad Apple!!.mp4"),
            view=BadAppleView(),
            mention_author=False,
        )
        return True
    except (discord.Forbidden, discord.HTTPException) as exc:
        print(f"⚠️ Bad Apple: não foi possível enviar o vídeo: {exc}")
        return False
