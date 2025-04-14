import socket
import os
import time
import datetime
import requests
import logging
import threading
import sys
import subprocess

def send_data(client_socket, image_path):
    size = os.path.getsize(image_path)
    client_socket.sendall(size.to_bytes(8, 'big'))
    with open(image_path, 'rb') as f:
        start_time = time.perf_counter_ns()
        while chunk := f.read(1024):
            client_socket.sendall(chunk)
        end_time = time.perf_counter_ns()
    bandwidth = size * 1e9 / 1e6 / (end_time - start_time)
    return size

def receive_string(client_socket):
    size = int.from_bytes(client_socket.recv(8), 'big')
    data = client_socket.recv(size).decode()
    print("Received string data from server.")  # Print statement added
    return data

def receive_data(client_socket, save_path):
    size = int.from_bytes(client_socket.recv(8), 'big')
    print(f"Receiving {size} bytes of data from server...")  # Print statement added
    with open(save_path, 'wb') as f:
        received = 0
        while received < size:
            data = client_socket.recv(4096)
            if not data:
                break
            f.write(data)
            received += len(data)
    print(f"Data received and saved to {save_path}")  # Print statement added

def setup_logger(path, handler_name):
    logger_name = f"Thread-{threading.get_ident()}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    if not any(handler.get_name() == handler_name for handler in logger.handlers):
        handler = logging.FileHandler(path)
        handler.set_name(handler_name)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        logger.addHandler(handler)
    return logger

def log_measurement(path, handler_name, **kwargs):
    logger = setup_logger(path, handler_name)
    log_str = '; '.join(f"{key}: {value}" for key, value in kwargs.items())
    logger.info(log_str)

def run_command(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def get_signal_info(net_type, os_type):
    command = {
        'windows': {'mbn': 'netsh mbn show interfaces', 'wlan': 'netsh wlan show interfaces'},
        'linux': {'mbn': 'nmcli device show', 'wlan': 'iwconfig'}
    }.get(os_type.lower(), {}).get(net_type, '')
    if not command:
        return None, None, "Unsupported OS/Network type"
    stdout, stderr = run_command(command)
    if stderr:
        return None, None, stderr
    signal_val = RSSI_val = None
    for line in stdout.split('\n'):
        if 'Signal' in line:
            signal_val = line.split(':')[-1].strip()
        elif 'RSSI' in line:
            RSSI_val = line.split(':')[-1].strip()
    return signal_val, RSSI_val, None

def sync_time(host, port):
    response_time = requests.post(f"http://{host}:{port}/time", json={'time': datetime.datetime.utcnow().isoformat()})
    time_diff_ns = int(float(response_time.json().get('time_difference', 0)))
    start_time = datetime.datetime.utcnow()
    requests.get(f"http://{host}:{port}/transfer")
    transfer_time_ns = int((datetime.datetime.utcnow() - start_time).total_seconds() * 1e9)
    return time_diff_ns + transfer_time_ns

def main():
    host, port = '172.27.16.1', 51821
    net_type, os_type = 'wlan', sys.platform
    input_path, output_path = 'Input/', 'Output/'
    im_max, it_max = 0, 100
    iteration, image = 0, 0
    log_file = "log_files/combined_log.log"
    connected = False

    while iteration <= it_max:
        if not connected:
            try:
                client_socket = socket.create_connection((host, port), timeout=5)
                connection_time = time.perf_counter_ns()
                connected = True
                print("Connected to the server.")  
            except Exception as e:
                log_measurement(log_file, 'handler1', log_time=datetime.datetime.now(), iteration=iteration, error=str(e))
                time.sleep(5)
                continue

        try:
            while iteration <= it_max:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                image_path = f"{input_path}{image}_in.jpg"
                save_path = f"{output_path}{iteration}_{image}_out.jpg"

                time_start_ns = time.time_ns()
                image_size = send_data(client_socket, image_path)
                print(f"Sent {image_size} bytes to server.")  # Print statement added

                processing_time_ns = int.from_bytes(client_socket.recv(8), 'big')
                print(f"Processing time received: {processing_time_ns} ns")  # Print statement added

                data = receive_string(client_socket)
                time_end_ns = time.time_ns()
                signal_val, RSSI_val, _ = get_signal_info(net_type, os_type)

                log_measurement(log_file, 'handler1', log_time=timestamp, iteration=iteration, image=image,
                                image_size=image_size, connection_time=connection_time, time_start_ns=time_start_ns,
                                processing_time_ns=processing_time_ns, time_end_ns=time_end_ns,
                                signal_val=signal_val, RSSI_val=RSSI_val, data=data)
                
                if image == im_max:  
                    iteration += 1  # Increment iteration
                if iteration > it_max:
                    client_socket.sendall(b"STOP")
                    print("Stopping iteration, sending STOP to server.")
                    break  
                else:
                    client_socket.sendall(b"CONT")
                    print(f"Iteration {iteration} completed, continuing to next iteration.")
            else:
                image += 1
                client_socket.sendall(b"CONT")
                print(f"Processed image {image}, continuing.")
        except KeyboardInterrupt:
            print("KeyboardInterrupt detected. Stopping process.")
            it_max = iteration
        except Exception as e:
            log_measurement(log_file, 'handler1', log_time=timestamp, iteration=iteration, error=str(e))
        finally:
            if iteration >= it_max:
                break
            send_data(client_socket, "STOP")
            client_socket.close()
            connected = False
            print("Closing connection with server.") 
            time.sleep(5)

if __name__ == '__main__':
    main()
