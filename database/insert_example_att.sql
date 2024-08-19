-- SET search_path TO GROUP_PROJECT;
SET search_path TO travel_database;

-- TRUNCATE TABLE TouristAttraction, AttractionPrice CASCADE;

-- Insert tourist attractions in Hanoi
-- Insert for Quốc Tử Giám (Temple of Literature)
WITH qt_giam AS (
    INSERT INTO TouristAttraction (
        Name, Address, Location, AttractionType, Rating, Tour_Duration, Description, Img_URL, Comments
    ) VALUES (
        'Quốc Tử Giám',
        ROW('58 Quốc Tử Giám', 'Đống Đa', 'Hà Nội')::Address,
        ROW(21.028265, 105.835457)::Location,
        'Historical Landmark',
        4.5,
        '1.5 hours',
        'The Temple of Literature is a famous historical and cultural site in Hanoi. It is Vietnam''s first university and a place of reverence.',
        '[{"url": "https://example.com/temple_of_literature.jpg", "description": "Front view of the Temple of Literature."}]'::json,
        '[{"user": "Nguyen Van A", "comment": "A must-visit place for history lovers."}]'::json
    )
    RETURNING AttractionID
),
-- Insert for Bảo tàng Hà Nội (Hanoi Museum)
bt_hanoi AS (
    INSERT INTO TouristAttraction (
        Name, Address, Location, AttractionType, Rating, Tour_Duration, Description, Img_URL, Comments
    ) VALUES (
        'Bảo tàng Hà Nội',
        ROW('Phạm Hùng', 'Nam Từ Liêm', 'Hà Nội')::Address,
        ROW(21.017004, 105.778206)::Location,
        'Museum',
        4.3,
        '3 hours',
        'The Hanoi Museum showcases the rich cultural heritage and history of Hanoi through various exhibitions.',
        '[{"url": "https://example.com/hanoi_museum.jpg", "description": "The modern architecture of Hanoi Museum."}]'::json,
        '[{"user": "Tran Thi B", "comment": "An informative and well-organized museum."}]'::json
    )
    RETURNING AttractionID
),
-- Insert for Công viên nước Hồ Tây (West Lake Water Park)
cvnuoc_ho_tay AS (
    INSERT INTO TouristAttraction (
        Name, Address, Location, AttractionType, Rating, Tour_Duration, Description, Img_URL, Comments
    ) VALUES (
        'Công viên nước Hồ Tây',
        ROW('614 Lạc Long Quân', 'Tây Hồ', 'Hà Nội')::Address,
        ROW(21.063795, 105.814023)::Location,
        'Amusement Park',
        4.2,
        '4 hours',
        'West Lake Water Park offers a wide range of water-based activities and rides, perfect for families and tourists looking to cool off and have fun.',
        '[{"url": "https://example.com/west_lake_water_park.jpg", "description": "Water rides at West Lake Water Park."}]'::json,
        '[{"user": "Le Thi C", "comment": "Great place for a fun day with kids!"}]'::json
    )
    RETURNING AttractionID
)

-- Insert prices for all attractions
INSERT INTO AttractionPrice (
    AttractionID, TicketType, NumberPeople, Price
) VALUES 
-- Ticket prices for Quốc Tử Giám
((SELECT AttractionID FROM qt_giam), 'General Admission - Adult', 1, 30000),
((SELECT AttractionID FROM qt_giam), 'General Admission - Student', 1, 15000),
((SELECT AttractionID FROM qt_giam), 'General Admission - Child Under 15', 1, 0),

-- Ticket prices for Bảo tàng Hà Nội
((SELECT AttractionID FROM bt_hanoi), 'General Admission', 1, 0),

-- Ticket prices for Công viên nước Hồ Tây
((SELECT AttractionID FROM cvnuoc_ho_tay), 'Under 90cm (Free)', 1, 0),
((SELECT AttractionID FROM cvnuoc_ho_tay), '90cm to 135cm - Weekdays', 1, 130000),
((SELECT AttractionID FROM cvnuoc_ho_tay), '90cm to 135cm - Weekends/Public Holidays', 1, 150000),
((SELECT AttractionID FROM cvnuoc_ho_tay), 'Above 135cm - Weekdays', 1, 155000),
((SELECT AttractionID FROM cvnuoc_ho_tay), 'Above 135cm - Weekends/Public Holidays', 1, 180000);