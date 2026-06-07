CREATE OR REPLACE FUNCTION uuid_generate_v7() RETURNS UUID AS
$$
BEGIN
    return encode(set_bit(set_bit(overlay(
        uuid_send(gen_random_uuid())
        placing substring(int8send(floor(extract(epoch from clock_timestamp()) * 1000)::bigint) from 3)
        from 1 for 6
    ), 52, 1), 53, 1), 'hex')::uuid;
END
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';


CREATE SCHEMA IF NOT EXISTS public;

/*
    Table: dreamers 
*/
CREATE TABLE dreamers (
    dreamer_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id INTEGER,
    login_id TEXT NOT NULL,
    name_family TEXT NOT NULL,
    name_given TEXT NOT NULL,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER update_dreamer_timestamp
BEFORE UPDATE ON dreamers
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

/*
    Table: dreamer_groups 
*/
CREATE TABLE dreamer_groups (
    group_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER update_dreamer_group_timestamp
BEFORE UPDATE ON dreamer_groups
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

/*
    Table: dreamer_group_members  
*/
CREATE TABLE dreamer_group_members (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES dreamer_groups(group_id) ON DELETE RESTRICT,
    dreamer_id UUID NOT NULL REFERENCES dreamers(dreamer_id) ON DELETE RESTRICT,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
