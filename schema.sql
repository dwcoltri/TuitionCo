/** 
 Table structure to store expense data
 **/
DROP TABLE IF EXISTS expense_lines;
CREATE TABLE expense_lines (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(12, 2),
    description TEXT,
    date DATE,
    type VARCHAR(255),
    user_ssn INTEGER,
    partner_id INTEGER
);
CREATE INDEX idx_user_id ON expense_lines (user_ssn);
/** 
 Table structure to store user data
 **/
DROP TABLE IF EXISTS user_data;
CREATE TABLE user_data (
    ssn INTEGER PRIMARY KEY,
    firstname VARCHAR(255),
    lastname VARCHAR(255),
    email VARCHAR(255)
);
/** 
 Table structure to store user approval data
 **/
DROP TABLE IF EXISTS user_approval;
CREATE TABLE user_approval (
    id SERIAL PRIMARY KEY,
    user_ssn INTEGER,
    approved BOOLEAN,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
/**
 Table structure to store user to customer mapping
 **/
DROP TABLE IF EXISTS user_customer;
CREATE TABLE user_customer (
    id SERIAL PRIMARY KEY,
    user_ssn INTEGER,
    customer_id INTEGER
);