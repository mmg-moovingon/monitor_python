import socket
import subprocess
import json
import os
import time
from datetime import datetime
import sys

# Path to the log file
log_file_path = '/opt/monitor_python/check_status.log'
hostname = socket.gethostname()
if "win" in hostname or "rtb1-hq1" in hostname or "rtb2-hq1" in hostname or "rtb-hq1-aero3" in hostname:
    app_name = 'rtb-win'
    file_name = 'com.mars.rtb-notifications-1.0.0.jar'
    folder_name = 'rtb-notifications'
    server_type = 'win'
else:
    app_name = 'rtb-server'
    file_name = 'com.mars.rtb-server-2.0.0.jar'
    folder_name = 'rtb-server'
    server_type = 'worker'

# Python 2 and 3 compatibility for print function
try:
    input = raw_input  # Python 2 compatibility for input function
except NameError:
    pass

# Log errors to a file
def log_error(message):
    with open(log_file_path, 'w') as log_file:
        log_file.write("{}: {}\n".format(datetime.now(), message))


# Example metric functions (same as before)
def get_ssh_port():
    try:
        with open('/etc/ssh/sshd_config') as f:
            for line in f:
                if line.startswith('Port'):
                    return int(line.split()[-1])
        return -1
    except (OSError, ValueError) as e:
        log_error("Error in get_ssh_port: {}".format(e))
        return -1


def get_app_status():
    try:
        result = subprocess.Popen(["/etc/init.d/{}".format(app_name), "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = result.communicate()
        return 1 if b"Running" in output or "Running" in output.decode('utf-8') else 0
    except Exception as e:
        log_error("Error in get_app_status: {}".format(e))
        return 0


def check_port_status(port):
    """Checks if a port is open and in use."""
    try:
        result = subprocess.Popen(["ss", "-tuln"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = result.communicate()
        return 1 if ":{}".format(port) in output.decode('utf-8') else 0
    except Exception as e:
        log_error("Error in check_port_status: {}".format(e))
        return 0


def count_iptables_rows():
    """Counts the number of iptables rows."""
    try:
        # Execute the iptables command and count the lines
        result = subprocess.Popen("/usr/sbin/iptables -L | wc -l", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = result.communicate()

        return int(output.strip())
    except Exception as e:
        log_error("Error in count_iptables_rows: {}".format(e))
        return -1

def check_iptables_content():
    """Checks the content of iptables rules."""
    try:
        with open('/etc/iptables/rules.v4') as f:
            content = f.read()
            return 1 if "inner DO" in content else 0
    except Exception as e:
        log_error("Error in check_iptables_content: {}".format(e))
        return -1


def file_age(filepath):
    """Returns the age of a file in the specified unit (minutes, hours, or days)."""
    real_filepath = os.path.realpath(filepath)
    current_time = time.time()
    try:
        file_mod_time = os.path.getmtime(real_filepath)
    except (OSError, Exception) as e:
        log_error("Error in file_age: {}".format(e))
        return -1

    age_seconds = current_time - file_mod_time
    return round(age_seconds)


def check_service_status(service_name):
    """Checks if a service is active."""
    try:
        result = subprocess.check_output(['systemctl', 'is-active', service_name], stderr=subprocess.STDOUT)
        if hasattr(result, 'decode'):
            status = result.decode('utf-8').strip()  # Python 3 decode
        else:
            status = result.strip()  # Python 2 strip directly
        return 1 if status == 'active' else 0
    except subprocess.CalledProcessError:
        return 0
    except Exception as e:
        log_error("Error in check_service_status: {}".format(e))
        return 0

def check_test_bidder():
    """Runs test_bidder.py and captures its output."""
    try:
        # Run test_bidder.py with a timeout of 5 seconds
        result = subprocess.Popen(
            ['python', './opt/monitor_python/test_bidder.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Set the timeout to 5 seconds
        try:
            # For Python 3.3 and above, communicate() supports timeout
            output, error = result.communicate(timeout=5)
        except TypeError:
            # For Python 2 and earlier Python 3 versions
            import threading

            def kill_process():
                try:
                    result.kill()
                except OSError:
                    pass

            timer = threading.Timer(5, kill_process)
            try:
                timer.start()
                output, error = result.communicate()
            finally:
                timer.cancel()

        # Decode the output and error
        if hasattr(output, 'decode'):
            output = output.decode('utf-8').strip()
        else:
            output = output.strip()
        if hasattr(error, 'decode'):
            error = error.decode('utf-8').strip()
        else:
            error = error.strip()

        # Check if process was terminated due to timeout
        if result.returncode == -9 or result.returncode is None:
            log_error("test_bidder.py timed out after 5 seconds.")
            return 0  # Return 0 on timeout

        # Check the return code
        if result.returncode != 0:
            log_error("test_bidder.py failed with error: {}".format(error))
            return 0  # Return 0 on error

        # Convert output to integer
        try:
            value = int(output)
            if value == 1:
                return 1
            else:
                return 0
        except ValueError:
            log_error("test_bidder.py returned non-integer output: {}".format(output))
            return 0  # Return 0 if output is not an integer

    except Exception as e:
        log_error("Error running test_bidder.py: {}".format(e))
        return 0  # Return 0 on exception


def check_win_healthcheck():
    """Performs a health check by accessing the specified URL."""
    try:
        url = "http://localhost:80/notification/rtb/healthcheck?key=1"

        # Handle imports for Python 2 and 3
        try:
            # For Python 3
            from urllib.request import urlopen
            from urllib.error import URLError, HTTPError
        except ImportError:
            # For Python 2
            from urllib2 import urlopen, URLError, HTTPError

        # Set a timeout for the request (e.g., 5 seconds)
        timeout = 5

        # Make the GET request
        response = urlopen(url, timeout=timeout)
        status_code = response.getcode()

        if status_code == 200:
            # Read the response data
            response_data = response.read()
            # Decode response_data if necessary
            if hasattr(response_data, 'decode'):
                response_data = response_data.decode('utf-8')

            # Check if the response is '1'
            if response_data.strip() == '1':
                return 1
            else:
                return 0
        else:
            # Non-200 status code
            return 0
    except Exception as e:
        log_error("Healthcheck failed: {}".format(e))
        return 0

def check_connectivity(host, port, timeout=5):
    """Checks if a connection can be established to a host on a given port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)

    try:
        s.connect((host, port))
        s.shutdown(socket.SHUT_RDWR)
        return 1
    except socket.timeout:
        log_error("Timeout on port {} at {}".format(port, host))
    except socket.error as e:
        log_error("Timeout on port {} at {}".format(port, host))
    finally:
        s.close()
    return 0

# Load the configuration from the selected *-monitor.json
def load_configuration(config_file_path):
    try:
        with open(config_file_path, 'r') as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        log_error("Error loading configuration: {}".format(e))
        return {}


# Generate the JSON metrics dynamically based on config
def generate_json_metrics(config):
    data = {}

    # Gather any input fields (like server names) from the config
    input_values = {}
    for key, settings in config.items():
        if settings.get('input', False):
            input_values[key] = settings.get('value')
    # Dynamically add other metrics based on config
    metric_functions = {
        'ssh_port': get_ssh_port,
        'app_status': get_app_status,
        'port_80_status': lambda: check_port_status(80),
        'port_8080_status': lambda: check_port_status(8080),
        'rsync_jsons_last_update': lambda: file_age('/var/www/html/load3.srv-analytics.info/crons/input/rtb_scala/rsync_monitor.txt'),
        'iptables_line_count': count_iptables_rows,
        'iptables_content_status': check_iptables_content,
        'td_agent_port_status': lambda: check_port_status(24224),
        'geo_ip_last_update': lambda: file_age('/usr/share/GeoIP/GeoIP2-City.mmdb'),
        'udger_last_update': lambda: file_age('/usr/local/share/udger/udgerdb_v3.dat'),
        'app_last_update': lambda: file_age("/usr/share/scala/{}/lib/{}".format(folder_name, file_name)),
        'dao_log_last_update': lambda: file_age("/usr/share/scala/{}/lib/{}".format(folder_name, file_name)),
        'counters_log_last_update': lambda: file_age("/usr/share/scala/{}/log/counters.dat".format(folder_name)),
        'pm_status': lambda: check_port_status(9898),
        'aerospike_port_status': lambda: check_port_status(3000),
        'aerospike_service_status': lambda: check_service_status('aerospike'),
        'sentinel_service_status': lambda: check_service_status('sentinelone'),
        'win_healthcheck': check_win_healthcheck,
        'test_bidder': check_test_bidder,
        'connection_to_win1_status': lambda: check_connectivity(input_values.get('win1-server'), 3000),
        'connection_to_win2_status': lambda: check_connectivity(input_values.get('win2-server'), 3000),
        'connection_to_win3_status': lambda: check_connectivity(input_values.get('win3-server'), 3000),
        'connection_to_marsai_status': lambda: check_connectivity(input_values.get('mars-ai-server'), 3000),
        'connection_to_dmp1hq_status': lambda: check_connectivity(input_values.get('dmp1hq-server'), 80),
        'connection_to_rtb-data1_status': lambda: check_connectivity(input_values.get('rtb-data1-server'), 9092),
        'connection_to_rtb-data2_status': lambda: check_connectivity(input_values.get('rtb-data2-server'), 9092),
    }

    for key, settings in config.items():
        # Only collect if the key has a corresponding function
        if key in metric_functions:
            # Get the metric value from the function
            value = metric_functions[key]()

            # If the key is not marked as 'input', include it in the output
            if not settings.get('input', False):
                data[key] = value

    return data


if __name__ == "__main__":

    config = load_configuration('/opt/monitor_python/conf.json')
    # Generate the metrics based on the config
    data = generate_json_metrics(config)

    # Print the JSON data for Telegraf
    print(json.dumps(data))

    # Write the output to status.json
    try:
        with open('/opt/monitor_python/status.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)
    except Exception as file_error:
        log_error("Error writing JSON to file: {}".format(file_error))