class OPCUAConnectionManager:
    _instance = None
    _is_connected = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OPCUAConnectionManager, cls).__new__(cls)
            cls._instance.connection = None  # Replace with actual connection object
        return cls._instance

    def connect(self):
        try:
            if not self._is_connected:
                # Add logic to establish connection
                self.connection = "Simulated OPC-UA Connection"  # Simulate connection
                self._is_connected = True
                print("Connected to OPC-UA server.")
            else:
                print("Already connected.")
        except Exception as e:
            self._is_connected = False
            print(f"Connection failed: {e}")

    def disconnect(self):
        try:
            if self._is_connected:
                # Add logic to close connection
                self.connection = None
                self._is_connected = False
                print("Disconnected from OPC-UA server.")
            else:
                print("No active connection to disconnect.")
        except Exception as e:
            print(f"Disconnection failed: {e}")

    def get_connection(self):
        return self.connection if self._is_connected else None

    def is_connected(self):
        return self._is_connected

    def _reconnect(self):
        print("Attempting to reconnect...")
        self.disconnect()
        self.connect()  # Simply attempt to connect again. More robust logic should be added.

    def connection_state(self):
        return "Connected" if self._is_connected else "Disconnected"