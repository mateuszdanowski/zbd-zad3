DROP TABLE candies_in_stock;
DROP TABLE packages;
DROP TABLE candies_in_package;
DROP TABLE similar_candies;


CREATE TABLE candies_in_stock (
    name TEXT PRIMARY KEY,
    in_stock INT NOT NULL,
    CHECK(in_stock >= 0)
);

CREATE TABLE packages (
    id SERIAL PRIMARY KEY,
    country TEXT NOT NULL,
    recipient_desc TEXT NOT NULL
);

CREATE TABLE candies_in_package (
    package_id INT,
    candy_name TEXT,
    quantity INT NOT NULL
);

CREATE TABLE similar_candies (
    candy TEXT,
    similar_to TEXT,
    similarity_level NUMERIC(3, 2) NOT NULL,
    PRIMARY KEY (candy, similar_to)
);
