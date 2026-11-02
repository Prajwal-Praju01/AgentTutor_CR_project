-- AgentTutor database initialization script
-- Creates test database alongside dev database

CREATE DATABASE agenttutor_test;
GRANT ALL PRIVILEGES ON DATABASE agenttutor_test TO agenttutor;

-- Enable pgvector extension on both databases
\connect agenttutor_dev
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\connect agenttutor_test
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

