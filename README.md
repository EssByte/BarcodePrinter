---

# **Project Overview**

The **Barcode Printer** application is a Python-based solution designed to manage, configure, and print barcodes efficiently. It offers a user-friendly interface powered by PyQt5, making it suitable for users with varying technical expertise. The application integrates advanced functionalities like database management, dynamic UI updates, and printer configuration to streamline barcode printing operations.

### **Key Features**

1. **Database Configuration**  
   * Configure and test database connectivity seamlessly through the UI.  
2. **Printer Management**  
   * Auto-detect connected printers.  
   * Configure and manage USB or wireless printers with ease.  
3. **Driver Installation**  
   * Install required drivers, including generic and custom drivers, directly from the application.  
4. **Command Execution**  
   * Send ZPL or TPSL commands to printers for precise barcode printing.  
5. **Dynamic UI Updates**  
   * Automatically refresh UI elements when configuration changes are detected.  
6. **Error Handling and Logging**  
   * Comprehensive error handling ensures minimal disruption.  
   * Detailed logs help with monitoring and troubleshooting.  
7. **Cross-Driver Compatibility**  
   * Supports both generic drivers (via PyUSB) and custom drivers (via Win32Print).

---

**Prerequisites**

Before proceeding with the setup and installation of the **Barcode Printer** application, ensure your system meets the necessary requirements. This section outlines both hardware and software prerequisites and the dependencies required for successful execution.

---

## **System Requirements**

* **Operating System**: Windows 10 or later (64-bit preferred for better compatibility).  
* **Processor**: Intel Core i3 or equivalent (minimum); Intel Core i5 or higher recommended for better performance.  
* **RAM**: 4GB minimum (8GB or higher recommended for smooth multitasking).  
* **Storage**: At least 500MB of free disk space for the application, plus additional space for drivers and dependencies.

---

## **Software Requirements**

1. **Python**: Version 3.10 or higher is required to run the application.  
   * [Download Python](https://www.python.org/) and ensure the `pip` package manager is included during installation.  
   * Add Python to your system’s `PATH` environment variable.  
       
2. **Microsoft SQL Server Management Studio (SSMS)**:  
    Installing only the ODBC Driver may not work for database connectivity (not yet figured out). We recommend installing **SQL Server Management Studio (SSMS)**, which includes the required ODBC drivers and management tools.  
   * [Download SQL Server Management Studio (SSMS)](https://learn.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms).  
       
3. **Visual C++ Redistributable**:  
    The application requires Visual C++ Redistributable for PyUSB and database connectivity.  
   * Download the latest version of the Visual C++ Redistributable from [Microsoft's official site](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).

4\.  **Auto-py-to-exe** (optional for developers):  
 If you plan to compile the Python scripts into an executable, install the **auto-py-to-exe** GUI tool. You can install it using pip:

 	***$ pip install auto-py-to-exe***

---

## **Dependencies**

This project requires the following Python libraries to run:

* **PyQt5**: For creating the graphical user interface (GUI).  
* **pyodbc**: For connecting to SQL Server databases.  
* **pyusb**: For sending commands to USB-connected barcode printers.  
* **win32print**: For printing via printers using Windows drivers.  
* **logging**: For logging application activities and errors.  
* **json**: For handling configuration files.  
* **socket** and **subprocess**: For network and command-line operations.

Install all the required Python libraries using the `requirements.txt` file included in the project directory. Run the following command in your terminal:

***$ pip install \-r requirements.txt***

---

## **Hardware Requirements**

1. **Barcode Printer**:

   * Compatible with either **ZPL** or **TPSL** command protocols.  
   * Ensure the printer supports both USB and wireless modes (if applicable).  
2. **USB Port**:

   * A functional USB port is required for connecting barcode printers.  
   * If using a wireless printer, ensure the network configuration allows connectivity.

---

## **Access Permissions**

### **Administrator Privileges**

Some operations in this project require administrative privileges:

* Installing drivers such as **ODBC Driver** or other Windows executables.  
* Configuring USB devices with generic drivers (e.g., **WinUSB**, **libusb**, or **libusbK**).  
* Accessing the system registry for printer driver detection.

To ensure smooth execution, always run the application or its compiled executable as an administrator.

**Project Structure**

The **Barcode Printer** application is organized into a structured directory format for easy navigation and modularity. Below is an overview of the project’s structure, with descriptions of each folder and file:

.  
![][image1]  
---

## **Root Files**

1. **barcode.json**  
   * Stores the application’s configuration settings (e.g., database credentials, printer settings, templates, etc.).  
   * This file is auto-updated when changes are made via the settings UI.  
2. **main.py**  
   * The entry point of the application.  
   * Handles the initialization of the UI and navigation between different modules like dashboard and settings.  
3. **requirements.txt**  
   * Contains all the Python dependencies required for the project.  
4. **version.py**  
   * Stores the application version information, allowing easy management of version tracking.

---

## **Folders**

### **drivers/**

Contains the driver installation files required for the application, such as:

* `msodbcsql.msi`: Installer for Microsoft ODBC Driver 18 for SQL Server.

### **images/**

Holds all the images used in the application, including:

* Icons for the settings and dashboard (`settingsicon.png`, `dashboard.png`).  
* Background images (`background.jpg`).  
* Printer-related icons (`printer.png`, `zpl.png`, `tpsl.png`).

### **modules/**

Contains Python modules responsible for different functionalities:

* **CheckDriver.py**: Handles checking for installed ODBC and printer drivers.  
* **Configurations.py**: Manages reading and writing the application’s configuration from `barcode.json`.  
* **InstallDriver.py**: (WIP) module to install necessary drivers.  
* **logger\_config.py**: Provides logging functionality to track the application’s activities and errors.  
* **SendCommand.py**: Handles sending commands to printers (both USB and wireless).

### **trials/**

* This folder is used for experimentation or testing scripts.

### **ui/**

Contains the PyQt5 `.ui` files for designing the application’s user interfaces, such as:

* `dashboard.ui`: The UI layout for the dashboard.  
* `settings3.ui`: The UI layout for the settings screen (third version).

---

## **Executable Dependencies**

### **libusb-1.0.dll**

* Required for USB communication via the **PyUSB** library.  
* Ensure this file is present in the root directory for the application to function correctly with USB-connected printers.

---

## **Python Scripts**

1. **settings.py, settings2.py, settings3.py**

   * These scripts handle the settings UI logic and interactions. settings.py and settings2.py are the older versions.   
2. **dashboard.py**

   * Manages the dashboard functionality, including displaying database statistics and system information.  
3. **check\_password.py**

   * Provides functionality to verify user credentials for accessing restricted sections of the application.

---

# **Setup Instructions**

Follow these steps to set up the **Barcode Printer** application and get it running on your system.

---

## **Step 1: Clone or Download the Project**

Clone the repository from GitHub or download the ZIP file.  
 git clone \<repository-url\>

1.   
2. Extract the ZIP file (if downloaded) into a directory of your choice.

---

## **Step 2: Install Python**

Ensure Python 3.10 or above is installed on your system.

1. Download the latest version of Python from the [official website](https://www.python.org/downloads/).  
2. During installation:  
   * Select **Add Python to PATH**.  
   * Choose the option to install pip.

Verify installation:

***$ python \--version***  
***$ pip \--version***

---

## **Step 3: Install Microsoft SQL Server Management Studio (SSMS)**

To manage the database connection and avoid errors:

1. Download the [SQL Server Management Studio (SSMS)](https://learn.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms).  
2. Install it on your system, which includes the required **ODBC drivers**.

---

## **Step 4: Install Dependencies**

Navigate to the project directory and install Python dependencies:

pip install \-r requirements.txt

---

## **Step 5: Verify libusb-1.0.dll Presence**

Ensure `libusb-1.0.dll` is in the root directory. This file is required for USB communication.

---

## **Step 6: Run the Application**

Execute the main script:

***$ python main.py***

This launches the application with the dashboard and settings interface.

---

## **Step 7: Configure the Application**

1. Open the **Settings** menu.  
2. The password for Settings is DD \* MM \* YYYY  
3. Enter the database credentials (server, database, username, password).  
4. Select or install the required driver from the **Drivers** tab.

---

## **Step 8: Compile the Project (Optional)**

To distribute the project as an executable:

1. Install **auto-py-to-exe if have not**:  
    ***$ pip install auto-py-to-exe***  
2. Run the GUI:  
    ***$ auto-py-to-exe***  
3. Configure auto-py-to-exe:  
   * Select `main.py` as the script to package.  
   * Add `libusb-1.0.dll` and the `images/, ui/` folder as additional files.  
   * Under hidden-imports add `libusb, libusb1, pyodbc, PyQt5`  
   * Set the output directory.  
   * Click **Convert .py to .exe**.

The resulting `.exe` file will be generated in the specified directory.

---

# **Configuration Details**

This section explains the configurable elements of the **Barcode Printer** application and how to modify them effectively.

---

## **Configuration File: `barcode.json`**

The `barcode.json` file is the central configuration file that contains all the application settings. Below is a breakdown of its contents:

### **Default Configuration**

***{***

    ***"server": "localhost",***

    ***"database": "example\_db",***

    ***"username": "admin",***

    ***"password": "admin123",***

    ***"vid": "0x1234",***

    ***"pid": "0x5678",***

    ***"endpoint": "0x01",***

    ***"companyName": "Example Corp",***

    ***"location": "HQ",***

    ***"useZPL": true,***

    ***"ip\_address": "192.168.1.100",***

    ***"wireless\_mode": false,***

    ***"zplTemplate": "^XA ... ^XZ",***

    ***"tpslTemplate": "SPEED 2.0 ... EOP",***

    ***"logging": true,***

    ***"itemCount": 100,***

    ***"enterToSearch": true,***

    ***"useGenericDriver": true,***

    ***"printerName": "My Printer",***

    ***"databaseDriverName": "ODBC Driver 18 for SQL Server"***

***}***

---

## **Editable Fields**

Below are the fields in `barcode.json` and what they control:

![][image2]

---

## **Modifying the Configuration**

### **Using the Application Interface**

1. Navigate to the **Settings** tab.  
2. Modify the fields in the configuration sections (e.g., database credentials, printer settings).  
3. Click **Save** to apply changes.

### **Direct File Editing**

1. Open `barcode.json` in a text editor.  
2. Modify the desired fields (ensure valid JSON syntax).  
3. Save the file.  
   * **Note:** Use this method cautiously to avoid breaking the configuration.

---

## **How Configuration Works**

1. **Loading Configuration:** The application reads `barcode.json` on startup to initialize settings.  
2. **Updating Configuration:**  
   * Changes made through the UI automatically save back to `barcode.json`.  
   * Changes are monitored in real-time using `QFileSystemWatcher`.

---

# **Features**

The **Barcode Printer** application is designed to streamline the process of managing and printing barcodes while offering flexibility and robust functionality. Below are the key features of the application:

---

## **1\. Printer Integration**

* Supports **USB printers** via generic drivers (WinUSB, libusb, etc.) and custom drivers like Seagull.  
* Includes **wireless printer support** for IP-based communication.  
* Automatically detects and lists available printers in the system.

---

## **2\. Label Printing**

* Compatible with **ZPL** (Zebra Programming Language) and **TPSL** (Third-Party Scripting Language).  
* Customizable label templates for different printing requirements.  
* Allows multiple copies and detailed formatting for labels.

---

## **3\. Database Connectivity**

* Seamlessly connects to databases using **ODBC drivers** (e.g., ODBC Driver 18 for SQL Server).  
* Supports fetching product details such as Item Code, Description, Unit Price, and Barcode.  
* Real-time item display and filtering from the connected database.

---

## **4\. Dynamic Configuration Management**

* Real-time updates of configuration via a **QFileSystemWatcher** to monitor changes in `barcode.json`.  
* Comprehensive settings for:  
  * Database credentials  
  * Printer settings (VID, PID, Endpoint, IP address, etc.)  
  * Application logging

---

## **5\. Intuitive User Interface**

* Designed with **PyQt5**, offering a clean and user-friendly interface.  
* Includes tabs for:  
  * Dashboard: Displays system and printer statuses.  
  * Settings: Manage application and printer configurations.

---

## **6\. Search and Filtering**

* Quick search functionality to locate items by Item Code or Description.  
* Supports both **binary search** for exact matches and **keyword search** for broader filtering.

---

## **7\. Logging and Error Reporting**

* Detailed logs are generated for every application action:  
  * Configuration changes  
  * Printer connectivity  
  * Database operations  
* Errors are logged and displayed using **QMessageBox** for user awareness.

---

## **8\. Driver Installation (WIP)**

* Integrated feature to install drivers directly from the application.  
* Includes the ability to install:  
  * Generic USB drivers using **Zadig** (WinUSB, libusb, or libusbK).  
  * Database drivers via MSI or EXE packages (e.g., SQL Management Studio).

---

## **9\. Real-Time Status Updates**

* Displays the current system and printer status on the **Dashboard**:  
  * Printer connectivity  
  * Database connection  
  * Logging status

---

## **10\. Cross-Platform Barcode Management**

* Customizable barcode formats that fall back to **Item Code** if no barcode is available.  
* Handles edge cases like null or empty barcodes during database fetching.

---

Certainly\! Here’s the updated **Compilation Instructions** section tailored to your specifications. This guide will walk you through using **auto-py-to-exe** to compile your **Barcode Printer** application into a standalone executable, ensuring all necessary files and dependencies are included.

---

# **Compilation Instructions**

This section provides detailed steps to compile the **Barcode Printer** application into a standalone executable using **auto-py-to-exe**. This process ensures that all necessary files, dependencies, and hidden imports are bundled correctly, resulting in a seamless user experience.

---

## **Step 1: Install auto-py-to-exe**

**auto-py-to-exe** is a graphical interface for **PyInstaller** that simplifies the process of converting Python scripts into executable files.

1. **Open a Terminal or Command Prompt**:

   * **Windows**: Press `Win + R`, type `cmd`, and press `Enter`.  
   * **macOS/Linux**: Open the Terminal application.

**Install auto-py-to-exe via pip**:

 pip install auto-py-to-exe

2.   
3. **Verify Installation**:

Run the following command to ensure **auto-py-to-exe** is installed correctly:  
 auto-py-to-exe

*   
  * This should launch the **auto-py-to-exe** graphical interface.

---

## **Step 2: Prepare the Application for Compilation**

Before compiling, ensure that your project is properly structured and all necessary files are in place.

1. **Project Structure Verification**:

Ensure your project directory includes the following essential components:  
 .

├── barcode.json

├── drivers/

│   └── msodbcsql.msi

├── images/

├── libusb-1.0.dll

├── main.py

├── modules/

├── requirements.txt

├── settings.py

├── ui/

└── version.py

*   
2. **Install Dependencies**:

Navigate to your project directory and install all required Python libraries using `requirements.txt`:  
 pip install \-r requirements.txt

*   
3. **Verify Additional Files**:

   * Ensure that the following files and folders are present:  
     * `libusb-1.0.dll`: Required for USB communication.  
     * `drivers/`: Contains driver installation packages (`msodbcsql.msi`).  
     * `ui/`: Contains PyQt5 `.ui` files for the user interface.  
     * `images/`: Contains all image assets used in the application.

---

## **Step 3: Launch auto-py-to-exe**

1. **Start the Tool**:

Run the following command to launch the **auto-py-to-exe** interface:  
 auto-py-to-exe

*   
  * The graphical interface will open, guiding you through the compilation process.

---

## **Step 4: Configure Compilation Settings**

Follow these steps within the **auto-py-to-exe** interface to set up the compilation parameters correctly:

### **A. Script Location**

1. **Select Script**:  
   * Click the **Browse** button next to **Script Location**.  
   * Navigate to and select `main.py` from your project directory.

### **B. Output Settings**

1. **Onefile**:

   * Check the **Onefile** option to bundle the application into a single executable file.  
2. **Console Window**:

   * Uncheck the **Console Window** option to hide the console when running the application, providing a cleaner user interface.

### **C. Additional Files**

1. **Add Required Files and Folders**:

   * Under the **Additional Files** section, include the necessary files and directories to ensure the executable functions correctly.  
2. **Add `libusb-1.0.dll`**:

   * Click **Add Files**.  
   * Navigate to `libusb-1.0.dll` in your project root and add it.  
3. **Add `ui/` Folder**:

   * Click **Add Folder**.  
   * Select the entire `ui/` directory to include all `.ui` files.  
4. **Add `images/` Folder**:

   * Click **Add Folder**.  
   * Select the entire `images/` directory to include all image assets.  
5. **Add `drivers/` Folder**:

   * Click **Add Folder**.  
   * Select the entire `drivers/` directory to include driver installation packages.

### **D. Hidden Imports**

1. **Specify Hidden Imports**:  
   * Scroll to the **Advanced** section within **auto-py-to-exe**.

In the **Hidden Imports** field, add the following modules, separated by commas:  
 pyodbc, libusb, libusb1, PyQt5

*   
  * This ensures that these modules are included in the executable, preventing runtime errors related to missing imports.

### **E. Icon (Optional)**

1. **Set Application Icon**:  
   * Click the **Browse** button next to the **Icon** field.  
   * Select `images/logo.ico` to assign a custom icon to your executable.

### **F. Other Settings (Optional)**

1. **Additional Options**:  
   * Explore other settings such as **Runtime Hooks**, **Environment Variables**, etc., if your application requires them.

---

## **Step 5: Start the Compilation Process**

1. **Review Settings**:

   * Double-check all the configurations to ensure that all necessary files, folders, and hidden imports are correctly specified.  
2. **Begin Compilation**:

   * Click the **Convert .py to .exe** button at the bottom of the **auto-py-to-exe** interface.  
   * The compilation process will start, displaying real-time progress in the **Output** window.  
3. **Wait for Completion**:

   * Depending on your system and the size of the application, this process may take several minutes.  
   * Upon successful completion, a notification will appear, and the executable will be located in the **`output/`** directory specified during setup.

---

## **Step 6: Locate and Test the Executable**

1. **Navigate to Output Folder**:

   * By default, the compiled executable is saved in the `output/` folder within your project directory.

Example path:  
 /your-project-directory/output/main.exe

*   
2. **Run the Executable**:

   * Locate `main.exe` (or the name you provided during compilation).  
   * Double-click the executable to launch the **Barcode Printer** application.  
3. **Verify Functionality**:

   * **Configuration Loading**: Ensure `barcode.json` is correctly read and applied.  
   * **UI Elements**: Confirm that all UI components (from `ui/` and `images/` folders) are displayed properly.  
   * **Driver Installation**: Test driver installation functionality if applicable.  
   * **Printing**: Verify that the printing features work as expected.  
   * **Logging**: Check if logs are being generated and updated appropriately.  
4. **Administrator Privileges**:

   * If certain functionalities (like driver installation) require elevated permissions, right-click the executable and select **Run as Administrator**.

---

## **Step 7: Troubleshooting Compilation Issues**

If you encounter issues during or after the compilation process, follow these troubleshooting steps:

### **A. Missing Modules or Imports**

1. **Issue**:

   * The executable fails to start or crashes, indicating missing modules.  
2. **Solution**:

   * Ensure all required modules (`pyodbc`, `libusb`, `libusb1`, `PyQt5`) are listed under **Hidden Imports**.  
   * Recompile the application after verifying the hidden imports.

### **B. Missing Files or Folders**

1. **Issue**:

   * UI elements or images do not load correctly in the executable.  
2. **Solution**:

   * Verify that `libusb-1.0.dll`, `ui/`, `images/`, and `drivers/` folders are included under **Additional Files**.  
   * Recompile to ensure all necessary files are bundled.

### **C. Driver Installation Failures**

1. **Issue**:

   * Drivers fail to install or are not detected by the application.  
2. **Solution**:

   * Ensure `msodbcsql.msi` is correctly included in the `drivers/` folder.  
   * Confirm that the executable has the necessary permissions by running it as an administrator.

### **D. Permissions Issues**

1. **Issue**:

   * Certain functionalities require elevated permissions, leading to failures.  
2. **Solution**:

   * Always run the compiled executable with administrative privileges by right-clicking and selecting **Run as Administrator**.

### **E. Log File Analysis**

1. **Issue**:

   * Application crashes or behaves unexpectedly without clear error messages.  
2. **Solution**:

   * Check the log files generated by the application for detailed error messages.  
   * Logs are typically stored in a designated directory or within the application’s data folder.

### **F. Recompile with Debugging**

1. **Issue**:

   * Persistent errors that are hard to trace.  
2. **Solution**:

   * Recompile the executable without the **Onefile** option and with the **Console Window** enabled to view real-time error messages in the terminal.  
   * Adjust the **auto-py-to-exe** settings accordingly and identify the source of the issue.

---

## **Step 8: Finalizing the Executable for Distribution**

1. **Test on Multiple Systems**:

   * Before distributing, test the executable on different Windows systems to ensure compatibility and functionality.  
2. **Include Necessary Files**:

   * When distributing the executable, include the `drivers/` folder, `barcode.json`, and any other necessary directories or files that the application relies on.  
3. **Create an Installer (Optional)**:

   * For a more professional distribution, consider using an installer creation tool (e.g., **Inno Setup**, **NSIS**) to package the executable along with necessary dependencies and create a seamless installation experience for users.

---

## **Example auto-py-to-exe Configuration Summary**

* **Script Location**: `main.py`  
* **Onefile**: Checked  
* **Console Window**: Unchecked  
* **Icon**: `images/logo.ico`  
* **Additional Files**:  
  * `libusb-1.0.dll`  
  * `ui/` folder  
  * `images/` folder  
  * `drivers/` folder  
* **Hidden Imports**:  
  * `pyodbc`  
  * `libusb`  
  * `libusb1`  
  * `PyQt5`

---

By following these comprehensive compilation instructions, you can successfully create a standalone executable of the **Barcode Printer** application, ensuring all necessary components and dependencies are included for optimal performance and user experience.
