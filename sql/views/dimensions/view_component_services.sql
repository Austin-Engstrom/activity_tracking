drop view if exists view_component_services;
create view view_component_services as select service_id, component_id as component_key, service_date, service_type, notes from component_services;
