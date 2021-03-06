import os, requests, logging

def send_metric(measurement, tags, values, num_retries=0, must_succeed=False):
    url = os.environ.get("DPP_INFLUXDB_URL")
    db = os.environ.get("DPP_INFLUXDB_DB")
    if tags and url and db:
        line_tags = ",".join(["{}={}".format(k, v) for k, v in tags.items()])
        line_values = ",".join(["{}={}".format(k, v) for k, v in values.items()])
        old_logging_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.ERROR)
        res = requests.post("{url}/write?db={db}".format(url=url, db=db),
                            '{measurement},{tags} {values}'.format(measurement=measurement,
                                                                   tags=line_tags, values=line_values))
        logging.getLogger().setLevel(old_logging_level)
        if res.status_code == 404 and res.json()["error"].startswith("database not found:"):
            if num_retries > 0:
                raise Exception("Failed to create InfluxDB database")
            logging.getLogger().setLevel(logging.ERROR)
            res = requests.post("{url}/query".format(url=url), {"q": "CREATE DATABASE {db}".format(db=db)})
            logging.getLogger().setLevel(old_logging_level)
            res.raise_for_status()
            return send_metric(measurement, tags, values, num_retries+1)
        elif res.status_code == 200:
            return True
        else:
            res.raise_for_status()
    elif must_succeed:
        raise Exception("missing required environment variables")

def send_metric_parameters(measurement, tags, values, parameters):
    metric_tags = parameters.get("metric-tags", {})
    if len(metric_tags) > 0:
        tags.update(metric_tags)
        return send_metric(measurement, tags, values)
