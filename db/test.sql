INSERT INTO "admin" VALUES ('Админ1','111');
INSERT INTO "admin" VALUES ('Админ2','222');

INSERT INTO "country" VALUES ('Россия');
INSERT INTO "country" VALUES ('Турция', FALSE);
INSERT INTO "country" VALUES ('Китай', TRUE);

INSERT INTO "city" VALUES ('Москва', 'Россия');
INSERT INTO "city" VALUES ('Санкт-Петербург', 'Россия');
INSERT INTO "city" VALUES ('Стамбул', 'Турция');
INSERT INTO "city" VALUES ('Шанхай', 'Китай');

INSERT INTO "airport" VALUES ('LED', 'Пулково', 'Санкт-Петербург');
INSERT INTO "airport" VALUES ('SVO', 'Шереметьево', 'Москва');
INSERT INTO "airport" VALUES ('DME', 'Домодедово', 'Москва');
INSERT INTO "airport" VALUES ('VKO', 'Внуково', 'Москва');
INSERT INTO "airport" VALUES ('IST', 'Аэропорт Стамбула', 'Стамбул');
INSERT INTO "airport" VALUES ('SAW', 'Сабиха Гёкчен', 'Стамбул');
INSERT INTO "airport" VALUES ('PVG', 'Пудун', 'Шанхай');
INSERT INTO "airport" VALUES ('SHA', 'Хунцяо', 'Шанхай');

INSERT INTO "plane model" VALUES ('Airbus A320', 160, 20, 0);
INSERT INTO "plane model" VALUES ('Boeing 737', 140, 30, 10);
INSERT INTO "plane model" VALUES ('Sukhoi Superjet 100', 90, 10, 0);

INSERT INTO "plane" VALUES ('RA-00001', 'Airbus A320');
INSERT INTO "plane" VALUES ('RA-00002', 'Boeing 737');
INSERT INTO "plane" VALUES ('RA-00003', 'Boeing 737');
INSERT INTO "plane" VALUES ('RA-00004', 'Sukhoi Superjet 100');
INSERT INTO "plane" VALUES ('RA-00005', 'Sukhoi Superjet 100');

INSERT INTO "user" VALUES ('normis', 'OSINT', 'Моисеев', 'Дмитрий', 'Алексеевич', '2004-03-03', 'barlikus.work@gmail.com', '+79525336870');
INSERT INTO "user" VALUES ('kobra', 'retrograd', 'Медведев', 'Ярослав', 'Алексеевич', '2004-08-17');
INSERT INTO "user" VALUES ('lait', 'chuma', 'Матюрин', 'Владислав', 'Кириллович', '1970-01-01');
INSERT INTO "user" VALUES ('BMW', 'pivo', 'Ермаков', 'Евгений', 'Андреевич', '2004-08-04', 'ermakov.evgenii.2004@gmail.com', '+79657625764');
INSERT INTO "user" VALUES ('dover', 'mat_pomosch', 'Краилин', 'Илья', 'Александрович', '2004-07-19');
INSERT INTO "user" VALUES ('ezj', 'Krim', 'Омельченко', 'Евгений', 'Юрьевич', '2004-08-13');

INSERT INTO "flight" VALUES ('OBL0001', 'RA-00001', 'SHA', 'SVO', '2024-06-17 12:30','2024-06-17 22:30', 'Прилетел',10000,20000);
INSERT INTO "flight" VALUES ('OBL0002', 'RA-00003', 'DME', 'LED', '2024-08-29 9:00','2024-08-29 11:30', 'Отменен',2000,5000,10000);
INSERT INTO "flight" VALUES ('OBL0003', 'RA-00005', 'IST', 'LED', '2024-10-03 23:30','2024-10-04 05:00', 'Прилетел',5000,10000);
INSERT INTO "flight" VALUES ('OBL0004', 'RA-00004', 'LED', 'PVG', '2024-11-30 15:30','2024-12-01 01:00', 'Прилетел',8000,15000);
INSERT INTO "flight" VALUES ('OBL0005', 'RA-00002', 'SVO', 'LED', '2025-01-20 12:00','2025-01-20 14:30', 'Запланирован',3000,6000,11000);
INSERT INTO "flight" VALUES ('OBL0006', 'RA-00002', 'LED', 'SVO', '2025-01-25 10:00','2025-01-25 12:30', 'Запланирован',3000,6000,11000);
INSERT INTO "flight" VALUES ('OBL0007', 'RA-00003', 'LED', 'SVO', '2025-01-26 12:00','2025-01-26 14:30', 'Запланирован',3000,6000,11000);


INSERT INTO "booking" VALUES ('OBL0001', 'normis', 0, TRUE);
INSERT INTO "booking" VALUES ('OBL0002', 'lait', 2, TRUE);
INSERT INTO "booking" VALUES ('OBL0003', 'ezj', 1, TRUE);
INSERT INTO "booking" VALUES ('OBL0004', 'normis', 0, TRUE);
INSERT INTO "booking" VALUES ('OBL0004', 'kobra', 1, FALSE);
INSERT INTO "booking" VALUES ('OBL0005', 'dover', 0, TRUE);
INSERT INTO "booking" VALUES ('OBL0005', 'BMW', 0, TRUE);
INSERT INTO "booking" VALUES ('OBL0006', 'dover', 0, TRUE);
INSERT INTO "booking" VALUES ('OBL0006', 'BMW', 0, FALSE);