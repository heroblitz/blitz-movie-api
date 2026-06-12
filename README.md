# 🎬 Blitz Movie API

An unofficial REST API for [MovieBox](https://moviebox.ph) — search, discover, and get download links for **movies, TV series, anime, music, and educational content** across three provider versions.

**Created by [Blitz](https://github.com/heroblitz)**  
Powered by [moviebox-api](https://github.com/Simatwa/moviebox-api)

---

## 🚀 Base URL

```
https://blitz-movie-api.onrender.com
```

> Interactive docs available at `/docs` after deployment.

---

## 📦 Setup & Deployment

### Local

```bash
git clone https://github.com/heroblitz/blitz-movie-api
cd blitz-movie-api
pip install -r requirements.txt
uvicorn main:app --reload
```

### Deploy on Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo `heroblitz/blitz-movie-api`
4. Set the following:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Hit **Deploy** — that's it ✅

---

## 📡 API Versions

| Version | Subject Types Supported | Subtitles | Notes |
|---------|------------------------|-----------|-------|
| **v1** | movies, tv_series, anime, music, education | ✅ | Most features; popular/trending/hot exclusive |
| **v2** | movies, tv_series, anime, music, education | ✅ | Dedicated anime/music/education detail classes |
| **v3** | movies, tv_series, anime, music, education, unknown | ❌ | Cross-season auto support; uses subject_id |

---

## 🔍 Endpoints

### General

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info & status |
| GET | `/docs` | Interactive Swagger UI |

---

### V1 — Search

#### Search Content
```
GET /v1/search
```
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | **required** | Title keyword |
| `subject` | string | `movies` | `movies` · `tv_series` · `anime` · `music` · `education` |
| `page` | int | `1` | Page number |
| `per_page` | int | `10` | Results per page (max 50) |

**Example:**
```
GET /v1/search?query=naruto&subject=anime
GET /v1/search?query=avatar&subject=movies&page=2
```

---

#### Search Suggestions
```
GET /v1/search/suggest
```
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | **required** | Partial title |
| `per_page` | int | `10` | Number of suggestions |

---

### V1 — Details

#### Movie / Anime / Music / Education Details
```
GET /v1/details/movie
```
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | **required** | Title |
| `subject` | string | `movies` | `movies` · `anime` · `music` · `education` |

**Example:**
```
GET /v1/details/movie?query=demon+slayer&subject=anime
GET /v1/details/movie?query=inception&subject=movies
```

---

#### TV Series Details
```
GET /v1/details/series
```
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | **required** | Series title |

**Example:**
```
GET /v1/details/series?query=breaking+bad
```

---

### V1 — Download Links

#### Movie Download Links
```
GET /v1/links/movie
```
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | **required** | Title |
| `subject` | string | `movies` | `movies` · `anime` · `music` · `education` |

Returns all available video resolutions + subtitle files.

**Example:**
```
GET /v1/links/movie?query=one+piece+film+red&subject=anime
GET /v1/links/movie?query=the+batman
```

**Response:**
```json
{
  "version": "v1",
  "subject": "anime",
  "title": "one piece film red",
  "videos": [...],
  "subtitles": [...],
  "best_video": { "url": "...", "resolution": "1080p", ... },
  "english_subtitle": { "url": "...", "language": "English", ... }
}
```

---

#### TV Series Episode Download Links
```
GET /v1/links/series
```
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | **required** | Series title |
| `season` | int | `1` | Season number |
| `episode` | int | `1` | Episode number |

**Example:**
```
GET /v1/links/series?query=attack+on+titan&season=4&episode=1
```

---

### V1 — Discovery

| Endpoint | Description |
|----------|-------------|
| `GET /v1/homepage` | Featured content on MovieBox homepage |
| `GET /v1/popular` | What users are currently searching for |
| `GET /v1/trending?page=0&per_page=18` | Trending movies & series |
| `GET /v1/hot` | Hot/popular movies & series right now |
| `GET /v1/mirrors` | Available MovieBox mirror hosts |

---

### V2 — Search

#### Search Content
```
GET /v2/search
```
Same params as v1/search. Supports `movies`, `tv_series`, `anime`, `music`, `education`.

**Example:**
```
GET /v2/search?query=jujutsu+kaisen&subject=anime
GET /v2/search?query=cosmos&subject=education
```

---

#### Search Suggestions
```
GET /v2/search/suggest?per_page=10
```

---

### V2 — Details

#### Movie / Anime / Music / Education Details
```
GET /v2/details/movie?query=fullmetal+alchemist&subject=anime
```

#### TV Series Details
```
GET /v2/details/series?query=one+piece
```

---

### V2 — Download Links

#### Movie / Anime / Music / Education Links
```
GET /v2/links/movie
```
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | **required** | Title |
| `subject` | string | `movies` | `movies` · `anime` · `music` · `education` |

**Example:**
```
GET /v2/links/movie?query=black+clover&subject=anime
GET /v2/links/movie?query=kendrick+lamar+concert&subject=music
```

---

#### TV Series Episode Links
```
GET /v2/links/series?query=naruto&season=1&episode=1
```

---

### V2 — Discovery

| Endpoint | Description |
|----------|-------------|
| `GET /v2/homepage` | V2 homepage featured content |
| `GET /v2/mirrors` | Available V2 mirror hosts |

---

### V3 — Search

> ⚠️ **V3 uses `subject_id`** (not title) for details and download links.  
> Always search first, grab `subject_id` from results, then call details/links.

#### Search Content
```
GET /v3/search
```
Supports an extra `unknown` subject type on top of v2.

**Example:**
```
GET /v3/search?query=fairy+tail&subject=anime
GET /v3/search?query=avatar&subject=movies
```

**Response items include:**
```json
{
  "items": [
    {
      "subject_id": "abc123xyz",
      "title": "Avatar",
      ...
    }
  ]
}
```
Copy `subject_id` and use it in the endpoints below.

---

### V3 — Details

#### Item Details
```
GET /v3/details/movie
```
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `subject_id` | string | **required** | From `/v3/search` results |
| `include_seasons` | bool | `false` | Include season info |

**Example:**
```
GET /v3/details/movie?subject_id=abc123xyz&include_seasons=true
```

---

#### Season Info
```
GET /v3/seasons?subject_id=abc123xyz
```

---

### V3 — Download Links

> ⚠️ **Subtitles are NOT supported in v3** (see [issue #85](https://github.com/Simatwa/moviebox-api/issues/85))

#### Movie / Anime Links
```
GET /v3/links/movie
```
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `subject_id` | string | **required** | From `/v3/search` |
| `quality` | string | `best` | `best` · `worst` · `360p` · `480p` · `720p` · `1080p` |

**Example:**
```
GET /v3/links/movie?subject_id=abc123xyz&quality=1080p
```

---

#### TV Series Episode Links
```
GET /v3/links/series
```
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `subject_id` | string | **required** | From `/v3/search` |
| `season` | int | `1` | Season number |
| `episode` | int | `1` | Episode number |
| `quality` | string | `best` | Quality |

---

### V3 — Discovery

| Endpoint | Description |
|----------|-------------|
| `GET /v3/homepage` | V3 homepage featured content |

---

## 💡 Quick Examples

### Get anime download link (full flow)

```bash
# Step 1 — search
GET /v1/search?query=demon+slayer&subject=anime

# Step 2 — get download links for first result
GET /v1/links/movie?query=demon+slayer&subject=anime
```

### Get a specific TV episode link

```bash
GET /v1/links/series?query=attack+on+titan&season=4&episode=28
```

### Get trending right now

```bash
GET /v1/trending
GET /v1/hot
GET /v1/popular
```

### V3 flow (subject_id based)

```bash
# Step 1 — search and grab subject_id from response
GET /v3/search?query=one+punch+man&subject=anime

# Step 2 — get details
GET /v3/details/movie?subject_id=<subject_id>

# Step 3 — get download links
GET /v3/links/movie?subject_id=<subject_id>&quality=1080p
```

---

## ⚙️ Quality Options

| Value | Description |
|-------|-------------|
| `best` | Highest available resolution (default) |
| `worst` | Lowest available resolution |
| `360p` | 360p |
| `480p` | 480p |
| `720p` | 720p HD |
| `1080p` | 1080p Full HD |

---

## 📝 Notes

- All endpoints return JSON
- CORS is fully open (`*`) — works from any browser or frontend
- v1 and v2 return subtitle links; v3 does not (yet)
- v3 requires `subject_id` instead of a title query for details/links
- The API wraps [moviebox.ph](https://moviebox.ph) — all content belongs to its original creators

---

## 📄 License

MIT © [Blitz](https://github.com/heroblitz)
