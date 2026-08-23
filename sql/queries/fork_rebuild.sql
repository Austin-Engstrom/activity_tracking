-- Fork rebuild query
select
    g.gear_name as bike_name,
    count(*) as ride_count,
	round(sum(a.moving_time_minutes)/60,2) as ride_time,
	round(sum(a.distance_miles),2) as distance_miles
from view_activity a
left join view_gear g
    on a.gear_key = g.gear_key
where g.gear_name = 'Meta' -- Insert the name of the bike you want to check
	and a.start_date >= '2026-08-20' -- Insert the date of the last fork rebuild
group by
    g.gear_name