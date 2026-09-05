from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"
    # SQLAlchemy URL for PostgreSQL.  Override this through DATABASE_URL in
    # deployments (for example, with a managed PostgreSQL connection string).
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/wizape_presentation"
    AI_PROVIDER: str = "mock"
    AI_MODEL: str = ""
    AI_API_KEY: str = ""
    MAX_CONCURRENCY: int = 2
    MIN_QA_SCORE: int = 85
    # Daftar origin yang diizinkan (pisah dengan koma). Bisa juga berisi `*` untuk sembarang.
    # Contoh: "http://localhost:3000, http://localhost:3001, http://127.0.0.1:3000"
    # Khusus origin "http://localhost" atau "http://127.0.0.1" tanpa port akan mengizinkan SEMUA port.
    CORS_ORIGINS: str = "http://localhost, http://127.0.0.1, http://localhost:3000"
    API_BASE_URL: str = "http://localhost:8000"
    LOG_LEVEL: str = "INFO"

    # OAuth 2.0 Client credentials. Isi di .env jika ingin mengaktifkan login sosial.
    # Jika *_CLIENT_ID kosong, tombol sosial akan menampilkan pesan "provider belum dikonfigurasi".
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    FACEBOOK_CLIENT_ID: str = ""
    FACEBOOK_CLIENT_SECRET: str = ""
    YAHOO_CLIENT_ID: str = ""
    YAHOO_CLIENT_SECRET: str = ""
    # URL tempat user diarahkan setelah OAuth sukses/gagal (frontend page)
    OAUTH_REDIRECT_FRONTEND: str = "http://localhost:3000/profile"

    @property
    def cors_origins_list(self) -> List[str]:
        """List origin literal exact-match untuk dikasih ke CORSMiddleware.

        Selalu tambahkan "http://localhost" dan "http://127.0.0.1" sebagai bare-origin
        agar middleware dengan `allow_origin_regex` dapat menerimanya dengan port
        apa pun. Ini agar Next.js dev server di port acak (3000, 3001, 3007, …)
        tetap bisa akses API walau user tidak ubah CORS_ORIGINS di .env.
        """
        raw = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if "*" in raw:
            return ["*"]
        # Jadikan set agar tidak duplikat, tetap urut.
        merged: list[str] = []
        seen = set()
        for o in list(raw) + ["http://localhost", "http://127.0.0.1", "https://localhost", "https://127.0.0.1"]:
            if o not in seen:
                seen.add(o)
                merged.append(o)
        return merged

    def is_cors_origin_allowed(self, origin: Optional[str]) -> bool:
        """Return True bila origin diizinkan oleh list CORS_ORIGINS.

        - Jika ada `*` → terima semua
        - Origin exact match / case-insensitive match → terima
        - Jika origin list berisi bare "http://localhost" / "http://127.0.0.1" → terima
          localhost/127.0.0.1 port APAPUN (untuk dev Next.js port random 3000, 3001, 3007, dst.)
        """
        if not origin:
            return False
        allowed = self.cors_origins_list
        if allowed == ["*"]:
            return True
        origin_l = origin.rstrip("/").lower()
        for allow in allowed:
            a = allow.rstrip("/").lower()
            if a == origin_l:
                return True
            # localhost wildcard port: allow = http://localhost (no port), origin = http://localhost:3007
            if (a == "http://localhost" or a == "https://localhost") and origin_l.startswith(a + ":"):
                return True
            if (a == "http://127.0.0.1" or a == "https://127.0.0.1") and origin_l.startswith(a + ":"):
                return True
        return False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
