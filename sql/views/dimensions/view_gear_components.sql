drop view if exists view_gear_components;
create view view_gear_components as select component_id as component_key, gear_id as gear_key, component_type, manufacturer, model, installed_at, removed_at, service_interval_type, service_interval_value, notes from gear_components;
