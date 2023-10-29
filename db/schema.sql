CREATE TABLE TRANSACTIONS (
    CODE VARCHAR(20) NOT NULL,
    AMOUNT DECIMAL(10,2) NOT NULL,
    CURRENCY VARCHAR(3) NOT NULL DEFAULT 'CAD',
    DATE DATE NOT NULL,
    DESCRIPTION VARCHAR(255) NOT NULL,
    FOREIGN KEY (CURRENCY) REFERENCES CURRENCIES (CODE)
)

-- Path: db/schema.sql