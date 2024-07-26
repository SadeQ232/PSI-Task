import platform
import psutil
import logging
from prometheus_client import Gauge, CollectorRegistry
from .utils import sanitize_linux_metric_name, sanitize_windows_metric_name

registry = CollectorRegistry()

# Create Prometheus Gauges
cpu_gauges = [Gauge(f'cpu_usage_{i}', f'CPU usage for core {i}', registry=registry) for i in range(psutil.cpu_count())]
total_cpu_gauge = Gauge('total_cpu_usage', 'Total CPU usage percentage', registry=registry)
cpu_core_count_gauge = Gauge('cpu_core_count', 'Number of CPU cores', registry=registry)

memory_gauge = Gauge('memory_usage', 'Memory usage percentage', registry=registry)
total_memory_gauge = Gauge('total_memory_usage', 'Total memory usage percentage', registry=registry)
total_memory_installed_gauge = Gauge('total_memory_installed', 'Total installed memory in bytes', registry=registry)

swap_gauge = Gauge('swap_usage', 'Swap usage percentage', registry=registry)

if platform.system() == 'Windows':
    disk_gauges = {sanitize_windows_metric_name(p.mountpoint): Gauge(f'disk_usage_{sanitize_windows_metric_name(p.mountpoint)}', f'Disk usage for {p.mountpoint}', registry=registry) for p in psutil.disk_partitions()}
else:
    disk_gauges = {sanitize_linux_metric_name(p.mountpoint): Gauge(f'disk_usage_{sanitize_linux_metric_name(p.mountpoint)}', f'Disk usage for {p.mountpoint}', registry=registry) for p in psutil.disk_partitions()}

total_disk_gauge = Gauge('total_disk_usage', 'Total disk usage percentage', registry=registry)
total_disk_size_gauge = Gauge('total_disk_size', 'Total disk size in bytes', registry=registry)

disk_io_gauges = {
    'read_bytes': Gauge('disk_io_read_bytes', 'Disk I/O read bytes', registry=registry),
    'write_bytes': Gauge('disk_io_write_bytes', 'Disk I/O write bytes', registry=registry),
    'read_count': Gauge('disk_io_read_count', 'Disk I/O read count', registry=registry),
    'write_count': Gauge('disk_io_write_count', 'Disk I/O write count', registry=registry)
}

net_gauges = {
    'bytes_sent': Gauge('network_bytes_sent', 'Bytes sent over network', registry=registry),
    'bytes_recv': Gauge('network_bytes_recv', 'Bytes received over network', registry=registry),
    'packets_sent': Gauge('network_packets_sent', 'Packets sent over network', registry=registry),
    'packets_recv': Gauge('network_packets_recv', 'Packets received over network', registry=registry),
    'errin': Gauge('network_errin', 'Network input errors', registry=registry),
    'errout': Gauge('network_errout', 'Network output errors', registry=registry),
    'dropin': Gauge('network_dropin', 'Network input drops', registry=registry),
    'dropout': Gauge('network_dropout', 'Network output drops', registry=registry)
}

def collect_metrics():
    try:
        # Collect CPU metrics
        cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
        total_cpu_usage = psutil.cpu_percent(interval=1)
        for i, usage in enumerate(cpu_usage):
            cpu_gauges[i].set(usage)
        total_cpu_gauge.set(total_cpu_usage)
        cpu_core_count_gauge.set(len(cpu_usage))  # Set the number of CPU cores
        
        # Collect Memory metrics
        memory_info = psutil.virtual_memory()
        swap_info = psutil.swap_memory()
        memory_gauge.set(memory_info.percent)
        total_memory_gauge.set(memory_info.percent)
        total_memory_installed_gauge.set(memory_info.total)
        swap_gauge.set(swap_info.percent)

        # Collect Disk metrics
        total_disk_size = 0
        total_disk_usage = 0
        for p in psutil.disk_partitions():
            if p.mountpoint == '/':  # Focus only on the root mount point
                usage = psutil.disk_usage(p.mountpoint)
                total_disk_size = usage.total
                total_disk_usage = usage.percent
                if platform.system() == 'Windows':
                    disk_gauges[sanitize_windows_metric_name(p.mountpoint)].set(usage.percent)
                else:
                    disk_gauges[sanitize_linux_metric_name(p.mountpoint)].set(usage.percent)
        
        total_disk_size_gauge.set(total_disk_size)
        total_disk_usage_percentage = total_disk_usage
        total_disk_gauge.set(total_disk_usage_percentage)

        io_counters = psutil.disk_io_counters()
        disk_io_gauges['read_bytes'].set(io_counters.read_bytes)
        disk_io_gauges['write_bytes'].set(io_counters.write_bytes)
        disk_io_gauges['read_count'].set(io_counters.read_count)
        disk_io_gauges['write_count'].set(io_counters.write_count)

        # Collect Network metrics
        net_io = psutil.net_io_counters()
        net_gauges['bytes_sent'].set(net_io.bytes_sent)
        net_gauges['bytes_recv'].set(net_io.bytes_recv)
        net_gauges['packets_sent'].set(net_io.packets_sent)
        net_gauges['packets_recv'].set(net_io.packets_recv)
        net_gauges['errin'].set(net_io.errin)
        net_gauges['errout'].set(net_io.errout)
        net_gauges['dropin'].set(net_io.dropin)
        net_gauges['dropout'].set(net_io.dropout)

        # Log collected metrics
        logging.info(f'Collected CPU metrics: {cpu_usage}, Total CPU usage: {total_cpu_usage}%')
        logging.info(f'Collected Memory metrics: {memory_info.percent}% used, Total Memory usage: {memory_info.percent}%, Total Installed Memory: {memory_info.total} bytes')
        logging.info(f'Collected Swap metrics: {swap_info.percent}% used')
        logging.info(f'Collected Disk metrics for /: {total_disk_usage}% used')
        logging.info(f'Total Disk Size: {total_disk_size} bytes, Total Disk Usage: {total_disk_usage_percentage}% used')
        logging.info(f'Collected Disk I/O metrics: read {io_counters.read_bytes} bytes, wrote {io_counters.write_bytes} bytes')
        logging.info(f'Collected Network metrics: {net_io.bytes_sent} bytes sent, {net_io.bytes_recv} bytes received')
        
    except Exception as e:
        logging.error(f"Error collecting metrics: {e}")

def collect_windows_specific_metrics():
    if hasattr(psutil, "sensors_battery"):
        battery = psutil.sensors_battery()
        if battery:
            battery_percentage = battery.percent
            logging.info(f'Battery percentage: {battery_percentage}%')
    
    users = psutil.users()
    for user in users:
        logging.info(f'User session: {user.name}, Terminal: {user.terminal}, Host: {user.host}, Started: {user.started}')

if platform.system() == 'Windows':
    collect_windows_specific_metrics()
