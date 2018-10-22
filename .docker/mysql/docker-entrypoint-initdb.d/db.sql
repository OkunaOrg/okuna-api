CREATE DATABASE IF NOT EXISTS openbook_db_api;
CREATE USER 'openbookuser'@'localhost' IDENTIFIED BY 'changeme';
GRANT ALL PRIVILEGES ON openbook_db_api.* TO 'openbookuser'@'localhost';