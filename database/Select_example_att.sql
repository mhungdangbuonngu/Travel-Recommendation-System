SET search_path TO travel_database;

-- SELECT * FROM TouristAttraction;
-- SELECT * FROM AttractionPrice;

SELECT
    ta.Name,
    (ta.Address).district,
	ap.TicketType AS Ticket,
    ap.Price AS Price
FROM
    TouristAttraction ta
LEFT JOIN
    AttractionPrice ap
ON
    ta.AttractionID = ap.AttractionID
WHERE
    ta.AttractionID = 1;