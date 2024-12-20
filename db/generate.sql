DROP TABLE IF EXISTS "booking";
DROP TABLE IF EXISTS "flight";
DROP TABLE IF EXISTS "airport";
DROP TABLE IF EXISTS "city";
DROP TABLE IF EXISTS "country";
DROP TABLE IF EXISTS "plane";
DROP TABLE IF EXISTS "plane model";
DROP TABLE IF EXISTS "user";
DROP TABLE IF EXISTS "admin";

CREATE TABLE "country"
(
	"name" TEXT NOT NULL PRIMARY KEY,
	"visa" BOOL NOT NULL DEFAULT FALSE
);

CREATE TABLE "city"
(
	"name" TEXT NOT NULL PRIMARY KEY,
	"country" TEXT NOT NULL REFERENCES "country"("name")
);

CREATE TABLE "airport"
(
	"code" CHAR(3)NOT NULL PRIMARY KEY,
	"name" TEXT NOT NULL,
	"city" TEXT NOT NULL REFERENCES "city"("name"),
	CHECK ("code" ~ '^[A-Z]{3}$')
);

CREATE TABLE "plane model"
(
	"name" TEXT NOT NULL PRIMARY KEY,
	"economy class" INT NOT NULL DEFAULT 0,
	"business class" INT NOT NULL DEFAULT 0,
	"first class" INT NOT NULL DEFAULT 0,
	CHECK ("economy class" > 0 OR "business class" > 0 OR "first class" > 0)
);

CREATE TABLE "plane"
(
	"number" TEXT NOT NULL PRIMARY KEY,
	"model" TEXT NOT NULL REFERENCES "plane model"("name"),
	CHECK ("number" ~ '^RA-\d{5}$')
);

CREATE TABLE "user"
(
	"login" TEXT NOT NULL PRIMARY KEY,
	"password" TEXT NOT NULL,
	"name" TEXT NOT NULL,
	"surname" TEXT NOT NULL,
	"patronymic" TEXT,
	birthdate DATE NOT NULL,
	email TEXT UNIQUE,
	phone TEXT UNIQUE,
	CHECK (birthdate <= CURRENT_DATE - INTERVAL '12 years'),
	CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
	CHECK (phone ~ '^\+7\d{10}$')
);

CREATE TABLE "flight"
(
 	"number" TEXT NOT NULL PRIMARY KEY,
 	"plane number" TEXT NOT NULL REFERENCES "plane"("number"),
	"departure" TEXT NOT NULL REFERENCES "airport"("code"),
	"arrival" TEXT NOT NULL REFERENCES "airport"("code"),
	"departure datetime" TIMESTAMP NOT NULL,
	"arrival datetime" TIMESTAMP NOT NULL,
	"status" INT NOT NULL,
	"economy price" INT NOT NULL DEFAULT 0,
	"business price" INT NOT NULL DEFAULT 0,
	"first price" INT NOT NULL DEFAULT 0,
	CHECK ("number" ~ '^OBL\d{1,4}$'),
	CHECK ("economy price" >= 0 AND "business price" >= 0 AND "first price" >=0),
	CHECK ("arrival datetime" > "departure datetime"),
	CHECK ("arrival" <> "departure"),
	CHECK ("status" BETWEEN 0 AND 4)
);

CREATE TABLE "booking"
(
	"flight" TEXT NOT NULL REFERENCES "flight"("number"),
	"passenger" TEXT NOT NULL REFERENCES "user"("login"),
	"type" INT NOT NULL,
	"status" BOOL NOT NULL DEFAULT FALSE,
	-- 0 - эконом класс, 1 - бизнесс класс, 2 - первый класс
	CHECK ("type" BETWEEN 0 AND 2),
	PRIMARY KEY ("flight", "passenger")
);

CREATE TABLE "admin"
(	"username" TEXT NOT NULL,
	"password" TEXT NOT NULL UNIQUE,
	"id" SERIAL PRIMARY KEY
);
