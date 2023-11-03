CREATE TABLE TRANSACTIONS (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    CODE VARCHAR(20),
    AMOUNT DECIMAL(10,2) NOT NULL,
    CURRENCY VARCHAR(3) NOT NULL DEFAULT 'CAD',
    DATE DATE NOT NULL,
    DESCRIPTION VARCHAR(255),
    CATEGORY VARCHAR(20) NOT NULL,
    INFERRED_CATEGORY INTEGER NOT NULL DEFAULT 0,
    FILE_ID VARCHAR(255),
    FOREIGN KEY (CATEGORY) REFERENCES CATEGORIES (CATEGORY),
    FOREIGN KEY (CURRENCY) REFERENCES CURRENCIES (CODE),
    FOREIGN KEY (FILE_ID) REFERENCES FILES (ID)
);

CREATE TABLE FILES (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    FILENAME VARCHAR(255) NOT NULL,
    DATE DATE NOT NULL
);

CREATE TABLE CATEGORIES (
    CATEGORY VARCHAR(20) PRIMARY KEY NOT NULL, -- Titleized
    INCOME INTEGER NOT NULL DEFAULT 0,
    DESCRIPTION VARCHAR(255)
);

CREATE TABLE CURRENCIES (
    CODE VARCHAR(3) PRIMARY KEY
);

CREATE TABLE BUDGETS (
    CATEGORY VARCHAR(20) NOT NULL,
    AMOUNT DECIMAL(10,2) NOT NULL,
    CURRENCY VARCHAR(3) NOT NULL DEFAULT 'CAD',
    -- date should be in the format YYYY-MM
    START_DATE TEXT NOT NULL CHECK (START_DATE LIKE '____-__'),
    PRIMARY KEY (CATEGORY,START_DATE),
    FOREIGN KEY (CATEGORY) REFERENCES CATEGORIES (CATEGORY),
    FOREIGN KEY (CURRENCY) REFERENCES CURRENCIES (CODE)
);

INSERT INTO CURRENCIES (CODE) VALUES ('CAD'), ('USD'), ('EUR');

INSERT INTO CATEGORIES (CATEGORY, INCOME, DESCRIPTION) VALUES 
    ('Salary', 1, 'Salary from work'),
    ('Reimbursment', 1, 'Taxes, or any other thing'),
    ('E-transfer', 1, ''),
    ('Home', 0, 'Items for home'),
    ('Utilities', 0, 'Utilities'),
    ('Fast Food', 0, 'Any food to go / fast food'),
    ('Food Delivery', 0, ''),
    ('Depanneur', 0, ''),
    ('Restaurants', 0, ''),
    ('Groceries', 0, 'Groceries'),
    ('Subscriptions', 0, ''),
    ('Fees', 0, 'Any fees or unexpected payments'),
    ('Transportation', 0, 'Transportation'),
    ('Entertainment', 0, 'Entertainment'),
    ('Clothing', 0, 'Clothing'),
    ('Education', 0, 'Education'),
    ('Style', 0, 'Haircuts, skin care, ...'),
    ('General Shopping', 0, 'Shopping other than clothes'),
    ('Gifts', 0, 'Gifts'),
    ('Health', 0, 'Health'),
    ('Travel', 0, 'Travel'),
    ('Investments', 0, 'Investments'),
    ('Savings', 0, 'Savings'),
    ('Rent', 0, 'Rent'),
    ('Other', 0, 'Other');
