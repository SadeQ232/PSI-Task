def sanitize_metric_name(name):
    return name.replace("/", "_").replace(".", "_").replace("-", "_")
