DROP TABLE IF EXISTS "blocked_callers";
CREATE TABLE "blocked_callers" (
  "telephone_number" varchar(50) NOT NULL,
  "comment" varchar(100) NULL,
  "source" varchar(100) NULL,
  "created" datetime NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE UNIQUE INDEX "blocked_callers_number_unique" ON "blocked_callers" ("telephone_number");
CREATE INDEX "blocked_callers_number" ON "blocked_callers" ("telephone_number");
