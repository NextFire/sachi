import aiohttp
import backoff
import tomlkit
from pydantic import BaseModel, TypeAdapter
from yarl import URL

from sachi.config import read_config, write_config
from sachi.sources.base import (
    MediaType,
    SachiEpisodeModel,
    SachiParentModel,
    SachiSource,
)


class ConfigModel(BaseModel):
    tvdb: "TVDBConfigModel"


class TVDBConfigModel(BaseModel):
    apiKey: str
    token: str | None = None


class LoginModel(BaseModel):
    token: str


class SearchModel(BaseModel):
    tvdb_id: int
    name: str
    translations: dict[str, str]
    year: int | None = None


class EpisodeModel(BaseModel):
    id: int
    seasonNumber: int
    number: int
    name: str | None = None


def giveup(e: Exception):
    assert isinstance(e, aiohttp.ClientResponseError)
    return e.status != 401


class TVDBSource(SachiSource[int], media_type=MediaType.SERIES, service="TheTVDB"):
    server = URL("https://api4.thetvdb.com/v4")

    def __init__(self):
        super().__init__()
        self.config: TVDBConfigModel = self._load_config()

    def _load_config(self) -> TVDBConfigModel:
        config_doc = read_config()
        model = ConfigModel(**config_doc.unwrap())
        return model.tvdb

    def _save_config(self):
        config_doc = read_config()
        table = tomlkit.table()
        table.update(self.config.model_dump())
        config_doc["tvdb"] = table
        write_config(config_doc)

    async def _login(self, *args, **kwargs):
        body = {"apiKey": self.config.apiKey}
        async with self.session.post(self.server / "login", json=body) as resp:
            json = await resp.json()
        model = LoginModel(**json["data"])
        self.config.token = model.token
        self._save_config()

    async def search(self, query: str) -> list[SachiParentModel[int]]:
        @backoff.on_exception(
            backoff.expo,
            aiohttp.ClientResponseError,
            giveup=giveup,
            on_backoff=self._login,
        )
        async def _search():
            async with self.session.get(
                self.server / "search",
                params={"query": query, "type": "series"},
                headers={"Authorization": f"Bearer {self.config.token}"},
            ) as resp:
                json = await resp.json()
            return TypeAdapter(list[SearchModel]).validate_python(json["data"])

        search_res = await _search()
        return [
            SachiParentModel(
                media_type=self.media_type,
                ref_id=sr.tvdb_id,
                title=sr.translations.get("eng", sr.name),
                year=sr.year,
            )
            for sr in search_res
        ]

    async def get_episodes(
        self, parent: SachiParentModel[int]
    ) -> list[SachiEpisodeModel[int]]:
        @backoff.on_exception(
            backoff.expo,
            aiohttp.ClientResponseError,
            giveup=giveup,
            on_backoff=lambda _: self._login(),
        )
        async def _fetch_page(page: int):
            async with self.session.get(
                self.server
                / "series"
                / str(parent.ref_id)
                / "episodes"
                / "default"
                / "eng",
                params={"page": page},
                headers={"Authorization": f"Bearer {self.config.token}"},
            ) as resp:
                json = await resp.json()
            data = json.get("data", {})
            episodes = data.get("episodes", [])
            has_next = bool(json.get("links", {}).get("next"))
            validated = TypeAdapter(list[EpisodeModel]).validate_python(episodes)
            return validated, has_next

        all_episodes: list[EpisodeModel] = []
        page = 0
        while True:
            episodes_res, has_next = await _fetch_page(page)
            all_episodes.extend(episodes_res)
            if not has_next or not episodes_res:
                break
            page += 1

        return [
            SachiEpisodeModel[int](
                ref_id=ep.id,
                season=ep.seasonNumber,
                episode=ep.number,
                name=ep.name,
            )
            for ep in all_episodes
        ]
