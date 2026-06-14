"""
routes.py — All API routes for Blitz Movie API
Covers every feature across v1, v2, v3:
  - Search (movies, tv_series, anime, music, education, unknown)
  - Item details (movie, series, anime, music, education)
  - Downloadable file/subtitle links
  - Homepage featured content
  - Popular searches (v1)
  - Trending content (v1)
  - Hot movies & series (v1)
  - Search suggestions (v1, v2)
  - Mirror hosts (v1, v2)
  - v3 uses async context manager (MovieBoxHttpClient)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Literal

# ── v1 ────────────────────────────────────────────────────────────────────────
from moviebox_api.v1.core import (
    Search as V1Search, Session as V1Session, SubjectType as V1SubjectType,
    BaseItemDetails as V1BaseItemDetails,
)
from moviebox_api.v1 import (
    TVSeriesDetails,
    DownloadableMovieFilesDetail, DownloadableTVSeriesFilesDetail,
    Homepage as V1Homepage, PopularSearch,
    Trending, HotMoviesAndTVSeries,
    SearchSuggestion as V1SearchSuggestion,
    MIRROR_HOSTS as V1_MIRROR_HOSTS,
)

# ── v2 ────────────────────────────────────────────────────────────────────────
from moviebox_api.v2.core import Search as V2Search, Session as V2Session, SubjectType as V2SubjectType
from moviebox_api.v2 import (
    MovieDetails as V2MovieDetails,       # alias of SingleItemDetails
    TVSeriesDetails as V2TVSeriesDetails,
    DownloadableSingleFilesDetail,
    DownloadableTVSeriesFilesDetail as V2DownloadableTVSeriesFilesDetail,
    Homepage as V2Homepage,
    SearchSuggestion as V2SearchSuggestion,
)
from moviebox_api.v2.constants import MIRROR_HOSTS as V2_MIRROR_HOSTS

# ── v3 ────────────────────────────────────────────────────────────────────────
from moviebox_api.v3.core import (
    Search as V3Search, MovieBoxHttpClient,
    SubjectType as V3SubjectType,
    ItemDetails as V3ItemDetails,
    DownloadableVideoFilesDetail as V3DownloadableVideoFilesDetail,
    Homepage as V3Homepage,
    SeasonDetails,
    CustomResolutionType,
)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _serialize(obj):
    """Recursively convert Pydantic models / dataclasses to plain dicts."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    if hasattr(obj, "__dict__"):
        return {k: _serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj


_V1_SUBJECT = {
    "movies":    V1SubjectType.MOVIES,
    "tv_series": V1SubjectType.TV_SERIES,
    "anime":     V1SubjectType.ANIME,
    "education": V1SubjectType.EDUCATION,
    "music":     V1SubjectType.MUSIC,
    "all":       V1SubjectType.ALL,
}

_V2_SUBJECT = {
    "movies":    V2SubjectType.MOVIES,
    "tv_series": V2SubjectType.TV_SERIES,
    "anime":     V2SubjectType.ANIME,
    "education": V2SubjectType.EDUCATION,
    "music":     V2SubjectType.MUSIC,
    "all":       V2SubjectType.ALL,
}

_V3_SUBJECT = {
    "movies":    V3SubjectType.MOVIES,
    "tv_series": V3SubjectType.TV_SERIES,
    "anime":     V3SubjectType.ANIME,
    "education": V3SubjectType.EDUCATION,
    "music":     V3SubjectType.MUSIC,
    "unknown":   V3SubjectType.UNKNOWN,
    "all":       V3SubjectType.ALL,
}

# v3 quality -> CustomResolutionType (real member names use a leading underscore)
_V3_QUALITY = {
    "best":  CustomResolutionType.BEST,
    "worst": CustomResolutionType.WORST,
    "360p":  CustomResolutionType._360P,
    "480p":  CustomResolutionType._480P,
    "720p":  CustomResolutionType._720P,
    "1080p": CustomResolutionType._1080P,
}


# ═════════════════════════════════════════════════════════════════════════════
#  V1 ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/v1/search", tags=["V1 · Search"])
async def v1_search(
    query: str = Query(..., description="Title keyword"),
    subject: Literal["movies", "tv_series", "anime", "music", "education"] = Query("movies"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
):
    """Search for movies, TV series, anime, music, or educational content (v1)."""
    try:
        session = V1Session()
        search = V1Search(session, query, _V1_SUBJECT[subject], page=page, per_page=per_page)
        results = await search.get_content_model()
        return {
            "version": "v1", "query": query, "subject": subject, "page": page,
            "has_more": results.pager.hasMore if hasattr(results, "pager") else None,
            "total": len(results.items),
            "items": _serialize(results.items),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/search/suggest", tags=["V1 · Search"])
async def v1_search_suggest(
    query: str = Query(..., description="Partial title for suggestions"),
    per_page: int = Query(10, ge=1, le=20),
):
    """Get search suggestions as you type (v1)."""
    try:
        session = V1Session()
        ss = V1SearchSuggestion(session, per_page=per_page)
        results = await ss.get_content_model(reference=query)
        return {"version": "v1", "query": query, "suggestions": _serialize(results)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/details/movie", tags=["V1 · Details"])
async def v1_movie_details(
    query: str = Query(...),
    subject: Literal["movies", "anime", "music", "education"] = Query("movies"),
):
    """Get full details for a movie/anime/music/education title (v1)."""
    try:
        session = V1Session()
        search = V1Search(session, query, _V1_SUBJECT[subject])
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        target = results.first_item
        # Generic item-details fetcher works for any subjectType
        details_obj = V1BaseItemDetails(page_url=target.page_url, session=session)
        details = await details_obj.get_content_model()
        return {"version": "v1", "subject": subject, "details": _serialize(details)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/details/series", tags=["V1 · Details"])
async def v1_series_details(query: str = Query(...)):
    """Get full details for a TV series including seasons/episodes (v1)."""
    try:
        session = V1Session()
        search = V1Search(session, query, V1SubjectType.TV_SERIES)
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        sd = TVSeriesDetails(results.first_item, session=session)
        details = await sd.get_content_model()
        return {"version": "v1", "details": _serialize(details)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/links/movie", tags=["V1 · Download Links"])
async def v1_movie_links(
    query: str = Query(...),
    subject: Literal["movies", "anime", "music", "education"] = Query("movies"),
):
    """
    Get all download + subtitle links for a movie/anime/music/education title (v1).
    Returns video files at all available resolutions and subtitle files.
    """
    try:
        session = V1Session()
        search = V1Search(session, query, _V1_SUBJECT[subject])
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        # Use the search result item directly (avoids 403s from mismatched referer)
        target = results.first_item
        dl = DownloadableMovieFilesDetail(session, target)
        meta = await dl.get_content_model()
        return {
            "version": "v1", "subject": subject, "title": query,
            "videos": _serialize(meta.downloads),
            "subtitles": _serialize(meta.captions),
            "best_video": _serialize(meta.best_media_file),
            "english_subtitle": _serialize(meta.english_subtitle_file),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/links/series", tags=["V1 · Download Links"])
async def v1_series_links(
    query: str = Query(...),
    season: int = Query(1, ge=1),
    episode: int = Query(1, ge=1),
):
    """Get download + subtitle links for a specific TV series episode (v1)."""
    try:
        session = V1Session()
        search = V1Search(session, query, V1SubjectType.TV_SERIES)
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        target = results.first_item
        dl = DownloadableTVSeriesFilesDetail(session, target)
        meta = await dl.get_content_model(season=season, episode=episode)
        return {
            "version": "v1", "title": query, "season": season, "episode": episode,
            "videos": _serialize(meta.downloads),
            "subtitles": _serialize(meta.captions),
            "best_video": _serialize(meta.best_media_file),
            "english_subtitle": _serialize(meta.english_subtitle_file),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/homepage", tags=["V1 · Discovery"])
async def v1_homepage():
    """Get Moviebox v1 homepage featured content."""
    try:
        session = V1Session()
        content = await V1Homepage(session=session).get_content_model()
        return {"version": "v1", "homepage": _serialize(content)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/popular", tags=["V1 · Discovery"])
async def v1_popular():
    """Get currently trending popular searches on MovieBox (v1 exclusive)."""
    try:
        session = V1Session()
        content = await PopularSearch(session=session).get_content_model()
        return {"version": "v1", "popular": _serialize(content)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/trending", tags=["V1 · Discovery"])
async def v1_trending(
    page: int = Query(0, ge=0),
    per_page: int = Query(18, ge=1, le=50),
):
    """Get trending movies and series (v1 exclusive)."""
    try:
        session = V1Session()
        content = await Trending(session=session, page=page, per_page=per_page).get_content_model()
        return {"version": "v1", "page": page, "trending": _serialize(content)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/hot", tags=["V1 · Discovery"])
async def v1_hot():
    """Get hot (currently popular) movies and TV series (v1 exclusive)."""
    try:
        session = V1Session()
        content = await HotMoviesAndTVSeries(session=session).get_content_model()
        return {"version": "v1", "hot": _serialize(content)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/mirrors", tags=["V1 · Discovery"])
async def v1_mirrors():
    """Discover available MovieBox v1 mirror hosts."""
    try:
        return {"version": "v1", "mirrors": list(V1_MIRROR_HOSTS)}
    except Exception as e:
        raise HTTPException(500, str(e))


# ═════════════════════════════════════════════════════════════════════════════
#  V2 ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/v2/search", tags=["V2 · Search"])
async def v2_search(
    query: str = Query(...),
    subject: Literal["movies", "tv_series", "anime", "music", "education"] = Query("movies"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
):
    """Search for any content type including anime, music, education (v2)."""
    try:
        session = V2Session()
        search = V2Search(session, query, _V2_SUBJECT[subject], page=page, per_page=per_page)
        results = await search.get_content_model()
        return {
            "version": "v2", "query": query, "subject": subject, "page": page,
            "has_more": results.pager.hasMore if hasattr(results, "pager") else None,
            "total": len(results.items),
            "items": _serialize(results.items),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v2/search/suggest", tags=["V2 · Search"])
async def v2_search_suggest(
    query: str = Query(..., description="Partial title for suggestions"),
    per_page: int = Query(10, ge=1, le=20),
):
    """Get search suggestions (v2)."""
    try:
        session = V2Session()
        content = await V2SearchSuggestion(session=session, per_page=per_page).get_content_model(reference=query)
        return {"version": "v2", "query": query, "suggestions": _serialize(content)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v2/details/movie", tags=["V2 · Details"])
async def v2_movie_details(
    query: str = Query(...),
    subject: Literal["movies", "anime", "music", "education"] = Query("movies"),
):
    """Get full details for a movie/anime/music/education title (v2)."""
    try:
        session = V2Session()
        search = V2Search(session, query, _V2_SUBJECT[subject])
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        target = results.first_item
        # MovieDetails/AnimeDetails/MusicDetails/EducationDetails are all the
        # same class (SingleItemDetails) - constructor only takes `session`,
        # and the item is passed to get_content_model().
        details_obj = V2MovieDetails(session=session)
        details = await details_obj.get_content_model(target)
        return {"version": "v2", "subject": subject, "details": _serialize(details)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v2/details/series", tags=["V2 · Details"])
async def v2_series_details(query: str = Query(...)):
    """Get full TV series details including seasons/episodes (v2)."""
    try:
        session = V2Session()
        search = V2Search(session, query, V2SubjectType.TV_SERIES)
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        target = results.first_item
        sd = V2TVSeriesDetails(session=session)
        details = await sd.get_content_model(target)
        return {"version": "v2", "details": _serialize(details)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v2/links/movie", tags=["V2 · Download Links"])
async def v2_movie_links(
    query: str = Query(...),
    subject: Literal["movies", "anime", "music", "education"] = Query("movies"),
):
    """Get download + subtitle links for movie/anime/music/education (v2)."""
    try:
        session = V2Session()
        search = V2Search(session, query, _V2_SUBJECT[subject])
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        target = results.first_item
        dl = DownloadableSingleFilesDetail(session=session, item=target)
        meta = await dl.get_content_model()
        return {
            "version": "v2", "subject": subject, "title": query,
            "videos": _serialize(meta.downloads),
            "subtitles": _serialize(meta.captions),
            "best_video": _serialize(meta.best_media_file),
            "english_subtitle": _serialize(meta.english_subtitle_file),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v2/links/series", tags=["V2 · Download Links"])
async def v2_series_links(
    query: str = Query(...),
    season: int = Query(1, ge=1),
    episode: int = Query(1, ge=1),
):
    """Get download + subtitle links for a TV series episode (v2)."""
    try:
        session = V2Session()
        search = V2Search(session, query, V2SubjectType.TV_SERIES)
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        # Use the search result item directly
        target = results.first_item
        dl = V2DownloadableTVSeriesFilesDetail(session, target)
        meta = await dl.get_content_model(season=season, episode=episode)
        return {
            "version": "v2", "title": query, "season": season, "episode": episode,
            "videos": _serialize(meta.downloads),
            "subtitles": _serialize(meta.captions),
            "best_video": _serialize(meta.best_media_file),
            "english_subtitle": _serialize(meta.english_subtitle_file),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v2/homepage", tags=["V2 · Discovery"])
async def v2_homepage():
    """Get Moviebox v2 homepage featured content."""
    try:
        session = V2Session()
        content = await V2Homepage(session=session).get_content_model()
        return {"version": "v2", "homepage": _serialize(content)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v2/mirrors", tags=["V2 · Discovery"])
async def v2_mirrors():
    """Discover available MovieBox v2 mirror hosts."""
    try:
        return {"version": "v2", "mirrors": list(V2_MIRROR_HOSTS)}
    except Exception as e:
        raise HTTPException(500, str(e))


# ═════════════════════════════════════════════════════════════════════════════
#  V3 ROUTES  (uses async context manager for MovieBoxHttpClient)
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/v3/search", tags=["V3 · Search"])
async def v3_search(
    query: str = Query(...),
    subject: Literal["movies", "tv_series", "anime", "music", "education", "unknown"] = Query("movies"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    """Search all content types including 'unknown' category (v3)."""
    try:
        async with MovieBoxHttpClient() as client:
            search = V3Search(client, query, _V3_SUBJECT[subject], page=page, per_page=per_page)
            results = await search.get_content_model()
        return {
            "version": "v3", "query": query, "subject": subject, "page": page,
            "has_more": results.pager.has_more,
            "total": len(results.items),
            "items": _serialize(results.items),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v3/details/movie", tags=["V3 · Details"])
async def v3_movie_details(
    subject_id: str = Query(..., description="Subject ID from search results (item.subject_id)"),
    include_seasons: bool = Query(False, description="Include season info for series"),
):
    """
    Get full item details by subject_id (v3).
    Get the subject_id from /v3/search results → items[n].subject_id
    """
    try:
        async with MovieBoxHttpClient() as client:
            details = V3ItemDetails(client, include_seasons=include_seasons)
            result = await details.get_content_model(subject_id)
        return {"version": "v3", "details": _serialize(result)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v3/links/movie", tags=["V3 · Download Links"])
async def v3_movie_links(
    subject_id: str = Query(..., description="Subject ID from search results"),
    quality: Literal["best", "worst", "360p", "480p", "720p", "1080p"] = Query("best"),
):
    """
    Get download links for movies/anime/music/education (v3).
    ⚠️ Subtitles NOT supported in v3 (issue #85).
    Get subject_id from /v3/search results.
    """
    try:
        resolution = _V3_QUALITY.get(quality, CustomResolutionType.BEST)
        async with MovieBoxHttpClient() as client:
            dl = V3DownloadableVideoFilesDetail(client, resolution=resolution)
            meta = await dl.get_content_model(subject_id)
        return {
            "version": "v3", "subject_id": subject_id, "title": meta.title,
            "subtitle_support": False,
            "note": "v3 does not support subtitles yet (GitHub issue #85)",
            "videos": _serialize(meta.list),
            "best_video": _serialize(meta.best_media_file) if meta.list else None,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v3/links/series", tags=["V3 · Download Links"])
async def v3_series_links(
    subject_id: str = Query(..., description="Subject ID from search results"),
    season: int = Query(1, ge=1),
    episode: int = Query(1, ge=1),
    quality: Literal["best", "worst", "360p", "480p", "720p", "1080p"] = Query("best"),
):
    """
    Get download link for a specific TV series episode (v3).
    ⚠️ Subtitles NOT supported in v3 (issue #85).
    The v3 resource endpoint returns a paginated list of episodes - this
    endpoint pages through it (up to 10 pages / ~200 episodes) to find
    the requested season & episode.
    """
    try:
        resolution = _V3_QUALITY.get(quality, CustomResolutionType.BEST)
        found = None
        total_episode = None
        async with MovieBoxHttpClient() as client:
            dl = V3DownloadableVideoFilesDetail(client, resolution=resolution, per_page=20)
            meta = await dl.get_content_model(subject_id)
            total_episode = meta.total_episode

            for _ in range(10):
                for ep in meta.list:
                    if ep.season == season and ep.episode == episode:
                        found = ep
                        break
                if found or not meta.pager.has_more:
                    break
                dl = dl.next_page(meta)
                meta = await dl.get_content_model(subject_id)

        if found is None:
            raise HTTPException(
                404,
                f"Episode S{season}E{episode} not found "
                f"(series has {total_episode} total episodes)",
            )

        return {
            "version": "v3", "subject_id": subject_id,
            "season": season, "episode": episode,
            "total_episode": total_episode,
            "subtitle_support": False,
            "video": _serialize(found),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v3/seasons", tags=["V3 · Details"])
async def v3_seasons(subject_id: str = Query(..., description="Subject ID from search results")):
    """Get all season info for a TV series (v3)."""
    try:
        async with MovieBoxHttpClient() as client:
            sd = SeasonDetails(client)
            result = await sd.get_content_model(subject_id)
        return {"version": "v3", "subject_id": subject_id, "seasons": _serialize(result)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v3/homepage", tags=["V3 · Discovery"])
async def v3_homepage():
    """Get Moviebox v3 homepage featured content."""
    try:
        async with MovieBoxHttpClient() as client:
            content = await V3Homepage(client).get_content_model()
        return {"version": "v3", "homepage": _serialize(content)}
    except Exception as e:
        raise HTTPException(500, str(e))
