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

from contextlib import asynccontextmanager
from fastapi import APIRouter, HTTPException, Query
from typing import Literal

# ── v1 ────────────────────────────────────────────────────────────────────────
from moviebox_api.v1.core import Search as V1Search, Session as V1Session, SubjectType as V1SubjectType
from moviebox_api.v1 import (
    MovieDetails, TVSeriesDetails,
    DownloadableMovieFilesDetail, DownloadableTVSeriesFilesDetail,
    Homepage as V1Homepage, PopularSearch,
    Trending, HotMoviesAndTVSeries,
    SearchSuggestion as V1SearchSuggestion,
)

# ── v2 ────────────────────────────────────────────────────────────────────────
from moviebox_api.v2.core import Search as V2Search, Session as V2Session, SubjectType as V2SubjectType
from moviebox_api.v2 import (
    MovieDetails as V2MovieDetails, TVSeriesDetails as V2TVSeriesDetails,
    AnimeDetails, EducationDetails, MusicDetails,
    DownloadableSingleFilesDetail,
    DownloadableTVSeriesFilesDetail as V2DownloadableTVSeriesFilesDetail,
    Homepage as V2Homepage,
    SearchSuggestion as V2SearchSuggestion,
)

# ── v3 ────────────────────────────────────────────────────────────────────────
from moviebox_api.v3.core import (
    Search as V3Search, MovieBoxHttpClient,
    SubjectType as V3SubjectType,
    ItemDetails as V3ItemDetails,
    DownloadableVideoFilesDetail as V3DownloadableVideoFilesDetail,
    Homepage as V3Homepage,
    SeasonDetails,
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


# ═════════════════════════════════════════════════════════════════════════════
#  V1 ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/v1/search", tags=["V1 · Search"])
async def v1_search(
    query: str = Query(...),
    subject: Literal["movies", "tv_series", "anime", "music", "education", "all"] = Query("movies"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
):
    """Search for movies, series, anime, etc. (v1)."""
    try:
        session = V1Session()
        search = V1Search(session, query, _V1_SUBJECT[subject], page=page, per_page=per_page)
        results = await search.get_content_model()
        return {
            "version": "v1", "query": query, "subject": subject, "page": page,
            "has_more": results.hasMore, "total": results.total,
            "items": _serialize(results.items),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/search/suggest", tags=["V1 · Search"])
async def v1_search_suggest(query: str = Query(...), per_page: int = Query(10, ge=1)):
    """Get search suggestions based on partial title (v1)."""
    try:
        session = V1Session()
        suggest = V1SearchSuggestion(session, query, per_page=per_page)
        results = await suggest.get_content_model()
        return {"version": "v1", "query": query, "suggestions": _serialize(results)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/details/movie", tags=["V1 · Details"])
async def v1_movie_details(
    query: str = Query(...),
    subject: Literal["movies", "anime", "music", "education"] = Query("movies"),
):
    """Get full details for a movie/anime/music/education item (v1)."""
    try:
        session = V1Session()
        search = V1Search(session, query, _V1_SUBJECT[subject])
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        target = results.items[0]
        details_obj = MovieDetails(target, session=session)
        details = await details_obj.get_content_model()
        return {"version": "v1", "subject": subject, "details": _serialize(details)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/details/series", tags=["V1 · Details"])
async def v1_series_details(query: str = Query(...)):
    """Get full TV series details including seasons/episodes (v1)."""
    try:
        session = V1Session()
        search = V1Search(session, query, V1SubjectType.TV_SERIES)
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        target = results.items[0]
        sd = TVSeriesDetails(target, session=session)
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
    """Get download + subtitle links for movie/anime/music/education (v1)."""
    try:
        # Fallback to V2 logic due to V1 403 Forbidden errors
        session = V2Session()
        search = V2Search(session, query, _V2_SUBJECT[subject])
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        target = results.first_item
        dl = DownloadableSingleFilesDetail(session=session, item=target)
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
        # Fallback to V2 logic due to V1 403 Forbidden errors
        session = V2Session()
        search = V2Search(session, query, V2SubjectType.TV_SERIES)
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        sd = V2TVSeriesDetails(results.first_item, session=session)
        details_model = await sd.get_content_model()
        dl = V2DownloadableTVSeriesFilesDetail(session, details_model)
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
async def v1_popular_searches():
    """Get popular content searches (v1)."""
    try:
        session = V1Session()
        content = await PopularSearch(session=session).get_content_model()
        return {"version": "v1", "popular": _serialize(content)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/trending", tags=["V1 · Discovery"])
async def v1_trending(page: int = Query(0, ge=0), per_page: int = Query(18, ge=1)):
    """Get trending movies and series (v1)."""
    try:
        session = V1Session()
        content = await Trending(session=session, page=page, per_page=per_page).get_content_model()
        return {"version": "v1", "page": page, "trending": _serialize(content)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v1/hot", tags=["V1 · Discovery"])
async def v1_hot():
    """Get hot movies and series (v1)."""
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
        from moviebox_api.v1 import constants as v1c
        mirrors = getattr(v1c, "MIRROR_HOSTS", getattr(v1c, "HOST_POOL", []))
        return {"version": "v1", "mirrors": list(mirrors)}
    except Exception as e:
        raise HTTPException(500, str(e))


# ═════════════════════════════════════════════════════════════════════════════
#  V2 ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/v2/search", tags=["V2 · Search"])
async def v2_search(
    query: str = Query(...),
    subject: Literal["movies", "tv_series", "anime", "music", "education", "all"] = Query("movies"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
):
    """Search for content (v2)."""
    try:
        session = V2Session()
        search = V2Search(session, query, _V2_SUBJECT[subject], page=page, per_page=per_page)
        results = await search.get_content_model()
        return {
            "version": "v2", "query": query, "subject": subject, "page": page,
            "has_more": results.hasMore, "total": results.total,
            "items": _serialize(results.items),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v2/search/suggest", tags=["V2 · Search"])
async def v2_search_suggest(query: str = Query(...), per_page: int = Query(10, ge=1)):
    """Get search suggestions based on partial title (v2)."""
    try:
        session = V2Session()
        suggest = V2SearchSuggestion(session, query, per_page=per_page)
        results = await suggest.get_content_model()
        return {"version": "v2", "query": query, "suggestions": _serialize(results)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/v2/details/movie", tags=["V2 · Details"])
async def v2_movie_details(
    query: str = Query(...),
    subject: Literal["movies", "anime", "music", "education"] = Query("movies"),
):
    """Get full item details (v2). Automatically picks specific class for anime/music/edu."""
    try:
        session = V2Session()
        search = V2Search(session, query, _V2_SUBJECT[subject])
        results = await search.get_content_model()
        if not results.items:
            raise HTTPException(404, "No results found")
        target = results.first_item

        details_map = {
            "anime":     AnimeDetails(target, session=session),
            "music":     MusicDetails(target, session=session),
            "education": EducationDetails(target, session=session),
        }
        if subject in details_map:
            details_obj = details_map[subject]
        else:
            details_obj = V2MovieDetails(target, session=session)

        details = await details_obj.get_content_model()
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
        sd = V2TVSeriesDetails(results.first_item, session=session)
        details = await sd.get_content_model()
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
        sd = V2TVSeriesDetails(results.first_item, session=session)
        details_model = await sd.get_content_model()
        dl = V2DownloadableTVSeriesFilesDetail(session, details_model)
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
        from moviebox_api.v2 import constants as v2c
        mirrors = getattr(v2c, "MIRROR_HOSTS", getattr(v2c, "HOST_POOL", []))
        return {"version": "v2", "mirrors": list(mirrors)}
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
    per_page: int = Query(10, ge=1, le=50),
):
    """Search all content types including 'unknown' category (v3)."""
    try:
        async with MovieBoxHttpClient() as client:
            search = V3Search(client, query, _V3_SUBJECT[subject], page=page, per_page=per_page)
            results = await search.get_content_model()
        return {
            "version": "v3", "query": query, "subject": subject, "page": page,
            "has_more": results.pager.has_more if hasattr(results, "pager") else None,
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
    page: int = Query(1, ge=1),
):
    """
    Get download links for any content (v3).
    ⚠️ Subtitles NOT supported in v3 (issue #85).
    Get subject_id from /v3/search results.
    """
    try:
        from moviebox_api.v3.core import CustomResolutionType, ResolutionType
        res_map = {
            "best": CustomResolutionType.BEST,
            "worst": CustomResolutionType.WORST,
            "360p": ResolutionType._360P,
            "480p": ResolutionType._480P,
            "720p": ResolutionType._720P,
            "1080p": ResolutionType._1080P,
        }
        resolution = res_map.get(quality, CustomResolutionType.BEST)
        async with MovieBoxHttpClient() as client:
            dl = V3DownloadableVideoFilesDetail(client, resolution=resolution, page=page)
            meta = await dl.get_content_model(subject_id)
        return {
            "version": "v3", "subject_id": subject_id,
            "subtitle_support": False,
            "note": "v3 does not support subtitles yet (GitHub issue #85)",
            "videos": _serialize(meta.list) if hasattr(meta, "list") else _serialize(meta),
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
    Get download links for a TV series episode (v3).
    ⚠️ Subtitles NOT supported in v3 (issue #85).
    """
    try:
        from moviebox_api.v3.core import CustomResolutionType, ResolutionType
        res_map = {
            "best": CustomResolutionType.BEST,
            "worst": CustomResolutionType.WORST,
            "360p": ResolutionType._360P,
            "480p": ResolutionType._480P,
            "720p": ResolutionType._720P,
            "1080p": ResolutionType._1080P,
        }
        resolution = res_map.get(quality, CustomResolutionType.BEST)
        async with MovieBoxHttpClient() as client:
            dl = V3DownloadableVideoFilesDetail(client, resolution=resolution)
            meta = await dl.get_content_model(subject_id, season=season, episode=episode)
        return {
            "version": "v3", "subject_id": subject_id,
            "season": season, "episode": episode,
            "subtitle_support": False,
            "videos": _serialize(meta.list) if hasattr(meta, "list") else _serialize(meta),
        }
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
