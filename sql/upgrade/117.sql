ALTER TABLE billservice_ipinuse
   ADD COLUMN ack boolean DEFAULT False;

CREATE OR REPLACE FUNCTION get_free_ip_from_pool(ag_pool_id_ integer)
  RETURNS inet AS
$BODY$
BEGIN

RETURN (SELECT free_ip.ipaddress FROM (SELECT (SELECT start_ip FROM billservice_ippool WHERE id=ag_pool_id_) + ip_series.ip_inc FROM generate_series(0, (SELECT end_ip - start_ip FROM billservice_ippool WHERE id=ag_pool_id_))AS ip_series(ip_inc)) AS free_ip(ipaddress)
WHERE free_ip.ipaddress NOT IN (SELECT ip FROM billservice_ipinuse WHERE pool_id=ag_pool_id_ and ((ack=True and disabled is Null) or (disabled is NULL and ack=False and now()-datetime<interval '60 seconds' ) or (disabled is not null and now()-disabled<interval '5 minutes'))) ORDER BY RANDOM() LIMIT 1);

END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION get_free_ip_from_pool(integer)
  OWNER TO postgres;
