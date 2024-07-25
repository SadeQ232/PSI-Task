import re

def sanitize_linux_metric_name(name):
    return name.replace("/", "_").replace(".", "_").replace("-", "_")

def sanitize_windows_metric_name(name):
    # Replace backslashes and any other non-alphanumeric character with underscores
    return re.sub(r'[\\/:*?"<>|]', '_', name)
