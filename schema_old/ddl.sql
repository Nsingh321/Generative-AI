CREATE TABLE album
(
    album_id INT NOT NULL PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    artist_id INT NOT NULL,

    FOREIGN KEY (artist_id) REFERENCES artist (artist_id) 
);


CREATE TABLE artist
(
    artist_id INT NOT NULL PRIMARY KEY,
    name VARCHAR(120)

);

CREATE TABLE customer
(
    customer_id INT NOT NULL PRIMARY KEY ,
    first_name VARCHAR(40) NOT NULL,
    last_name VARCHAR(20) NOT NULL,
    company VARCHAR(80),
    address VARCHAR(70),
    city VARCHAR(40),
    state VARCHAR(40),
    country VARCHAR(40),
    postal_code VARCHAR(10),
    phone VARCHAR(24),
    fax VARCHAR(24),
    email VARCHAR(60) NOT NULL,
    support_rep_id INT,
    
    FOREIGN KEY (support_rep_id) REFERENCES employee (employee_id) 
		
);

CREATE TABLE employee
(
    employee_id INT NOT NULL PRIMARY KEY,
    last_name VARCHAR(20) NOT NULL,
    first_name VARCHAR(20) NOT NULL,
    title VARCHAR(30),
    reports_to INT,
    birth_date TIMESTAMP,
    hire_date TIMESTAMP,
    address VARCHAR(70),
    city VARCHAR(40),
    state VARCHAR(40),
    country VARCHAR(40),
    postal_code VARCHAR(10),
    phone VARCHAR(24),
    fax VARCHAR(24),
    email VARCHAR(60),

    FOREIGN KEY (reports_to) REFERENCES employee (employee_id) 
		
);

CREATE TABLE genre
(
    genre_id INT NOT NULL PRIMARY KEY,
    name VARCHAR(120)
);

CREATE TABLE invoice
(
    invoice_id INT NOT NULL PRIMARY KEY,
    customer_id INT NOT NULL,
    invoice_date TIMESTAMP NOT NULL,
    billing_address VARCHAR(70),
    billing_city VARCHAR(40),
    billing_state VARCHAR(40),
    billing_country VARCHAR(40),
    billing_postal_code VARCHAR(10),
    total NUMERIC(10,2) NOT NULL,
    
    FOREIGN KEY (customer_id) REFERENCES customer (customer_id) 
		
);

CREATE TABLE invoice_line
(
    invoice_line_id INT NOT NULL PRIMARY KEY,
    invoice_id INT NOT NULL,
    track_id INT NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    quantity INT NOT NULL,
    
    FOREIGN KEY (invoice_id) REFERENCES invoice (invoice_id) ,
    FOREIGN KEY (track_id) REFERENCES track (track_id) 
		
);

CREATE TABLE media_type
(
    media_type_id INT NOT NULL PRIMARY KEY,
    name VARCHAR(120)
);

CREATE TABLE playlist
(
    playlist_id INT NOT NULL PRIMARY KEY,
    name VARCHAR(120)
);

CREATE TABLE playlist_track
(
    playlist_id INT NOT NULL PRIMARY KEY,
    track_id INT NOT NULL,

    FOREIGN KEY (playlist_id) REFERENCES playlist (playlist_id) ,
    FOREIGN KEY (track_id) REFERENCES track (track_id) 
);

CREATE TABLE track
(
    track_id INT NOT NULL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    album_id INT,
    media_type_id INT NOT NULL,
    genre_id INT,
    composer VARCHAR(220),
    milliseconds INT NOT NULL,
    bytes INT,
    unit_price NUMERIC(10,2) NOT NULL,
    
    FOREIGN KEY (album_id) REFERENCES album (album_id), 
		
    FOREIGN KEY (genre_id) REFERENCES genre (genre_id),
    FOREIGN KEY (media_type_id) REFERENCES media_type (media_type_id) 
);