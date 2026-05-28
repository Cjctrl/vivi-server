-- memory/zim_kb/schema.sql
-- Metadata database for the ZIM knowledge base.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- articles: one row per retrieved-and-cached ZIM article.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS articles (
  id              INTEGER PRIMARY KEY,
  title           TEXT    NOT NULL,
  source_zim      TEXT    NOT NULL,           -- filename of originating ZIM
  zim_namespace   TEXT,                       -- ZIM internal namespace/path
  conversion_ts   TEXT,                       -- ISO8601 timestamp
  markdown_path   TEXT,                       -- path on vivi-memdsk
  sha256          TEXT,                       -- checksum of Markdown content
  access_count    INTEGER NOT NULL DEFAULT 0,
  last_accessed   TEXT,
  embedded        INTEGER NOT NULL DEFAULT 0, -- 0 = not embedded, 1 = embedded
  zim_archived    INTEGER NOT NULL DEFAULT 0, -- 1 = safe to skip ZIM for this article
  chunk_count     INTEGER NOT NULL DEFAULT 0,
  tags            TEXT                        -- comma-separated topic tags
);

CREATE INDEX IF NOT EXISTS idx_articles_title         ON articles(title);
CREATE INDEX IF NOT EXISTS idx_articles_source_zim    ON articles(source_zim);
CREATE INDEX IF NOT EXISTS idx_articles_last_accessed ON articles(last_accessed);

-- ---------------------------------------------------------------------------
-- chunks: ~512-token slices of an article's Markdown, used for vector search.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chunks (
  id              INTEGER PRIMARY KEY,
  article_id      INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  chunk_index     INTEGER NOT NULL,
  chunk_text      TEXT    NOT NULL,
  embedding_id    TEXT,                       -- reference into embeddings DB
  sha256          TEXT
);

CREATE INDEX IF NOT EXISTS idx_chunks_article_id ON chunks(article_id);

-- ---------------------------------------------------------------------------
-- retrieval_log: audit trail of which articles served which query.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS retrieval_log (
  id              INTEGER PRIMARY KEY,
  query_text      TEXT,
  retrieved_from  TEXT,                       -- 'cache' | 'zim'
  article_ids     TEXT,                       -- JSON array
  ts              TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_retrieval_log_ts ON retrieval_log(ts);

-- ---------------------------------------------------------------------------
-- FTS5 virtuals: title/tag search on articles, full-text search on chunks.
-- External-content tables (content=...) avoid duplicating storage; triggers
-- below keep them synchronised with the source tables.
-- ---------------------------------------------------------------------------
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
  title, tags,
  content='articles',
  content_rowid='id',
  tokenize='porter unicode61'
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  chunk_text,
  content='chunks',
  content_rowid='id',
  tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
  INSERT INTO articles_fts(rowid, title, tags) VALUES (new.id, new.title, new.tags);
END;
CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
  INSERT INTO articles_fts(articles_fts, rowid, title, tags) VALUES ('delete', old.id, old.title, old.tags);
END;
CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
  INSERT INTO articles_fts(articles_fts, rowid, title, tags) VALUES ('delete', old.id, old.title, old.tags);
  INSERT INTO articles_fts(rowid, title, tags) VALUES (new.id, new.title, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
  INSERT INTO chunks_fts(rowid, chunk_text) VALUES (new.id, new.chunk_text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, chunk_text) VALUES ('delete', old.id, old.chunk_text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, chunk_text) VALUES ('delete', old.id, old.chunk_text);
  INSERT INTO chunks_fts(rowid, chunk_text) VALUES (new.id, new.chunk_text);
END;
