\getenv app_db_password DB_PASSWORD
\getenv test_db_password TEST_DB_PASSWORD

CREATE ROLE blog_app LOGIN PASSWORD :'app_db_password';
CREATE DATABASE blog_dev OWNER blog_app;

CREATE ROLE blog_test LOGIN PASSWORD :'test_db_password';
CREATE DATABASE blog_test OWNER blog_test;
