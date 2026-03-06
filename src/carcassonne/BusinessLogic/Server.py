import sys
import time
import socket
import select

class Server:
    SERVER_TIMEOUT = 30

    def __init__(self):
        self.server_name = ""
        self.client = None
        self.server = None
        self.running = False
        self.available_servers: dict[str, tuple[int, float]] = {}

    def list_available_servers(self, timeout: float = 5.0) -> list[str]:
        """
        Listen for available servers via UDP broadcasts for a specified timeout period.
        Returns a list of server names that responded within the timeout.
        """
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        try:
            s.bind(('', 12346))
            s.settimeout(timeout)  # Set socket timeout
        except Exception as e:
            print(f"Error binding socket: {e}")
            return []

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                ready = select.select([s], [], [], timeout - (time.time() - start_time))
                if ready[0]:
                    message, addr = s.recvfrom(1500)
                    message_part = message.decode()
                    if ":" in message_part:
                        name, port_str = message_part.split(":", 1)
                        try:
                            port = int(port_str)
                            self.available_servers[name] = (port, time.time())
                        except ValueError:
                            print(f"Invalid port in message: {message_part}")
                    else:
                        print(f"Invalid message format: {message_part}")
                else:
                    break  # Timeout reached
            except socket.timeout:
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

        s.close()
        self.check_servers_last_time_sent()
        return list(self.available_servers.keys())

    def check_servers_last_time_sent(self):
        """
        Remove servers from available_servers if they haven't sent a message
        within SERVER_TIMEOUT seconds.
        """
        current_time = time.time()
        to_remove = []
        for name, (port, last_time) in self.available_servers.items():
            if current_time - last_time >= self.SERVER_TIMEOUT:
                to_remove.append(name)
        for name in to_remove:
            del self.available_servers[name]
        return self.available_servers

    def server_start(self, port: int = 12345):
        """
        Start the TCP server on the specified port.
        Handles multiple clients concurrently using threading.
        """
        import threading  # Import here or at top

        self.server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind(('', port))
            self.server.listen(5)  # Allow up to 5 pending connections
            print(f"Server started on port {port}")
        except Exception as e:
            print(f"Error starting server: {e}")
            return

        self.running = True
        while self.running:
            try:
                self.server.settimeout(1.0)  # Timeout to check self.running periodically
                client_socket, addr = self.server.accept()
                print(f"Accepted connection from {addr}")
                # Handle client in a new thread
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
            except socket.timeout:
                continue  # Check self.running again
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                break

        self.server.close()
        print("Server stopped")

    def handle_client(self, client_socket):
        """
        Handle communication with a single client.
        """

        # should have a way to quit the server
        try:
            while True:
                data = client_socket.recv(1500)
                if len(data) == 0:
                    break
                # Process data (e.g., echo back for now; replace with game logic)
                response = self.process_message(data.decode())
                client_socket.send(response.encode())
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def process_message(self, message: str) -> str:
        """
        Process incoming message and return response.
        Placeholder: currently echoes the message.
        """
        # TODO: Integrate with game logic, e.g., handle moves, queries
        return f"Echo: {message}"

    def server_stop(self):
        """
        Stop the server gracefully.
        """
        self.running = False
        if self.server:
            self.server.close()

    def server_quit(self, server_name: str):
        """
        Quit the server and clean up resources.
        """
        if self.client == None:
            print("Error: no client socket found.")
            return -1
        data = "quit".encode()
        self.client.sendall(data)
        self.server_stop()
        # Additional cleanup if needed

    def ping(self) -> float:
        """
        Send a ping or check server status.
        Placeholder implementation.
        """
        start = time.time()
        self.send_to_server("ping")
        if self.client == None:
            print("Error: no client socket found.")
            return -1
        data = self.client.recv(1500)
        if data.decode() == "pong":
            end = time.time()
            return start - end

        return -1  # Or implement actual ping logic
    
    def join_server(self, server_name: str, port: int | None = None, timeout: float = 5.0) -> bool:
        """
        Connect to a remote server identified by name (and optional port).

        - If port is None, the method looks up the port from
          `available_servers` which is populated by `list_available_servers`.
        - Returns True if the connection is successfully established.
        - Once connected a background thread is started to receive messages
          from the server and dispatch them to `handle_server_message`.
        """
        # refresh discovery cache first
        self.list_available_servers()

        if server_name not in self.available_servers:
            print("Error: There is no server with such a name.")
            return False

        server_port, _ = self.available_servers[server_name]
        if port is None:
            port = server_port

        self.client = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.client.settimeout(timeout)
        try:
            self.client.connect((server_name, port))
        except Exception as e:
            print(f"Unable to connect to {server_name}:{port} -> {e}")
            self.client.close()
            self.client = None
            return False

        # clear the timeout for normal operation
        self.client.settimeout(None)

        # start a listener thread so the caller can interact without blocking
        import threading
        self._recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._recv_thread.start()
        return True

    def _receive_loop(self):
        """
        Internal helper that runs in a thread to read data from the server and
        dispatch it to `handle_server_message`.
        """
        try:
            while self.client:
                data = self.client.recv(1500)
                if not data or data.decode('utf-8') == "Server Shutdown":
                    print("Server closed the connection")
                    break
                self.handle_server_message(data.decode())
        except Exception as e:
            print(f"Error receiving from server: {e}")
        finally:
            if self.client:
                self.client.close()
            self.client = None

    def handle_server_message(self, message: str):
        """
        Override or extend this method to process messages received from the
        server. The default implementation simply prints the message.
        """
        print(message, end="")

    def send_to_server(self, text: str) -> bool:
        """
        Send a message to the connected server. Returns False if not
        connected.
        """
        if not self.client:
            print("Not connected to any server")
            return False
        try:
            self.client.sendall(text.encode())
            return True
        except Exception as e:
            print(f"Failed to send: {e}")
            return False


            
            
