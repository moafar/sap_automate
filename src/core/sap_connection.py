import win32com.client
import logging
import time

logger = logging.getLogger("SAP_Automation")

class SAPConnection:
    def __init__(self, connection_index=0, session_index=0, connection_mode="existing_session", 
                 connection_string=None, credentials=None):
        """
        Initialize SAP Connection.
        
        Args:
            connection_index: Index of existing connection (for existing_session mode)
            session_index: Index of session (for existing_session mode)
            connection_mode: "existing_session" or "credentials"
            connection_string: SAP connection string (for credentials mode, e.g., "SAP System Name")
            credentials: Dict with keys: username, password, client, system_id (optional)
        """
        self.connection_index = connection_index
        self.session_index = session_index
        self.connection_mode = connection_mode
        self.connection_string = connection_string
        self.credentials = credentials or {}
        self.session = None
        self.connection = None

    def connect(self):
        """
        Connects to SAP GUI session based on connection_mode.
        
        Returns:
            SAP session object
        """
        if self.connection_mode == "existing_session":
            return self._connect_existing_session()
        elif self.connection_mode == "credentials":
            return self._connect_with_credentials()
        else:
            raise ValueError(f"Invalid connection_mode: {self.connection_mode}. "
                           "Must be 'existing_session' or 'credentials'")

    def _connect_existing_session(self):
        """
        Connects to an already open SAP GUI session.
        """
        try:
            sap_gui_auto = win32com.client.GetObject("SAPGUI")
            if not sap_gui_auto:
                raise RuntimeError("SAPGUI Object not found.")
            
            application = sap_gui_auto.GetScriptingEngine
            if not application:
                raise RuntimeError("Scripting Engine not found.")

            if application.Children.Count == 0:
                raise RuntimeError("No open connections in SAP Logon.")

            if self.connection_index >= application.Children.Count:
                raise IndexError(f"Connection index {self.connection_index} out of range.")

            self.connection = application.Children(self.connection_index)

            if self.connection.Children.Count == 0:
                raise RuntimeError("Selected connection has no open sessions.")

            if self.session_index >= self.connection.Children.Count:
                raise IndexError(f"Session index {self.session_index} out of range.")

            self.session = self.connection.Children(self.session_index)
            logger.info(f"Connected to existing SAP Session: {self.session.Info.SystemName} "
                       f"Client: {self.session.Info.Client}")
            return self.session

        except Exception as e:
            logger.error(f"Failed to connect to existing SAP session: {e}")
            raise

    def _connect_with_credentials(self):
        """
        Opens a new SAP connection and logs in using credentials.
        """
        try:
            # Validate credentials
            required_creds = ["username", "password", "client"]
            for cred in required_creds:
                if not self.credentials.get(cred):
                    raise ValueError(f"Missing required credential: {cred}")
            
            if not self.connection_string:
                raise ValueError("connection_string is required for credentials mode")

            # Try to get SAP GUI Scripting Engine
            sap_gui_auto = None
            try:
                sap_gui_auto = win32com.client.GetObject("SAPGUI")
            except Exception:
                # SAP Logon is not running, try to start it
                logger.info("SAP Logon not running, attempting to start it...")
                self._start_sap_logon()
                time.sleep(3)  # Wait for SAP Logon to start
                try:
                    sap_gui_auto = win32com.client.GetObject("SAPGUI")
                except Exception as e:
                    raise RuntimeError(f"Could not start or connect to SAP Logon: {e}")
            
            if not sap_gui_auto:
                raise RuntimeError("SAPGUI Object not found. Make sure SAP GUI is installed.")
            
            application = sap_gui_auto.GetScriptingEngine
            if not application:
                raise RuntimeError("Scripting Engine not found.")

            logger.info(f"Opening new connection to: {self.connection_string}")
            
            # Open new connection
            self.connection = application.OpenConnection(self.connection_string, True)
            
            # Get the newly created session
            if self.connection.Children.Count == 0:
                raise RuntimeError("Connection opened but no session available.")
            
            self.session = self.connection.Children(0)
            
            # Perform login
            self._login()
            
            logger.info(f"Successfully logged in to SAP: {self.session.Info.SystemName} "
                       f"Client: {self.session.Info.Client}")
            return self.session

        except Exception as e:
            logger.error(f"Failed to connect with credentials: {e}")
            raise

    def _start_sap_logon(self):
        """
        Attempts to start SAP Logon if it's not running.
        """
        import subprocess
        import os
        
        # Common SAP Logon installation paths
        possible_paths = [
            r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe",
            r"C:\Program Files\SAP\FrontEnd\SAPgui\saplogon.exe",
            r"C:\Program Files (x86)\SAP\SAPGUI\saplogon.exe",
            r"C:\Program Files\SAP\SAPGUI\saplogon.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    subprocess.Popen([path])
                    logger.info(f"Started SAP Logon from: {path}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to start SAP Logon from {path}: {e}")
        
        logger.warning("Could not find SAP Logon executable. Please start it manually.")

    def _login(self):
        """
        Performs login by filling in credentials on the login screen.
        """
        try:
            # Wait for login screen to load
            time.sleep(1)
            
            # Find login window (usually wnd[0])
            wnd = self.session.findById("wnd[0]")
            
            # Fill in credentials
            # Client (Mandante)
            try:
                client_field = wnd.findById("wnd[0]/usr/txtRSYST-MANDT")
                client_field.Text = self.credentials["client"]
                logger.debug(f"Client set to: {self.credentials['client']}")
            except Exception as e:
                logger.warning(f"Could not set client field: {e}")
            
            # Username
            try:
                user_field = wnd.findById("wnd[0]/usr/txtRSYST-BNAME")
                user_field.Text = self.credentials["username"]
                logger.debug(f"Username set to: {self.credentials['username']}")
            except Exception as e:
                logger.error(f"Could not set username field: {e}")
                raise
            
            # Password
            try:
                pass_field = wnd.findById("wnd[0]/usr/pwdRSYST-BCODE")
                pass_field.Text = self.credentials["password"]
                logger.debug("Password set")
            except Exception as e:
                logger.error(f"Could not set password field: {e}")
                raise
            
            # Language (optional)
            if self.credentials.get("language"):
                try:
                    lang_field = wnd.findById("wnd[0]/usr/txtRSYST-LANGU")
                    lang_field.Text = self.credentials["language"]
                    logger.debug(f"Language set to: {self.credentials['language']}")
                except Exception as e:
                    logger.warning(f"Could not set language field: {e}")
            
            # Press Enter to login
            wnd.sendVKey(0)
            
            # Wait for login to complete
            time.sleep(2)
            
            # Check for error messages
            try:
                # Check if there's an error popup (wnd[1])
                error_wnd = self.session.findById("wnd[1]")
                if error_wnd:
                    # Try to get error message text
                    try:
                        error_text = error_wnd.findById("wnd[1]/usr/txtMESSTXT1").Text
                        logger.error(f"Login failed with error: {error_text}")
                        raise RuntimeError(f"SAP Login failed: {error_text}")
                    except:
                        logger.error("Login failed with unknown error")
                        raise RuntimeError("SAP Login failed with unknown error")
            except:
                # No error window found, login likely successful
                pass
            
            logger.info("Login successful")

        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    def get_session(self):
        """
        Returns the current session, connecting if necessary.
        """
        if self.session is None:
            return self.connect()
        return self.session

    def disconnect(self):
        """
        Closes the connection (only for credential mode).
        """
        if self.connection_mode == "credentials" and self.connection:
            try:
                self.connection.CloseConnection()
                logger.info("Connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
