CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS zones (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    source TEXT NOT NULL,
    geom GEOMETRY(MultiPolygon, 4326)
);

CREATE TABLE IF NOT EXISTS price_index (
    id SERIAL PRIMARY KEY,
    zone_id INT REFERENCES zones(id),
    period DATE NOT NULL,
    price_m2 NUMERIC NOT NULL,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS listings_agg (
    id SERIAL PRIMARY KEY,
    zone_id INT REFERENCES zones(id),
    period DATE NOT NULL,
    p25_m2 NUMERIC NOT NULL,
    p50_m2 NUMERIC NOT NULL,
    p75_m2 NUMERIC NOT NULL,
    sample_size INT NOT NULL,
    source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_listings_agg_zone_period ON listings_agg(zone_id, period);
CREATE INDEX IF NOT EXISTS idx_price_index_zone_period ON price_index(zone_id, period);
