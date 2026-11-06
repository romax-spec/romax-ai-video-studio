CREATE TABLE projects (
  id VARCHAR(36) PRIMARY KEY,
  title VARCHAR(240) NOT NULL,
  source_path TEXT NOT NULL,
  output_path TEXT,
  status VARCHAR(40) NOT NULL DEFAULT 'uploaded',
  duration FLOAT NOT NULL DEFAULT 0,
  width INTEGER NOT NULL DEFAULT 0,
  height INTEGER NOT NULL DEFAULT 0,
  project_json TEXT NOT NULL DEFAULT '{}',
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
