# NI Jam Information System Barcode Module
The Barcode Module for NIJIS is an additional Python application that is run on a local machine connected to a Brother QL-570 label printer.   
The application integrates with the inventory system in NIJIS to print inventory labels for equipment.   

The following is required for the application to work.
- An API key generated from NIJIS. This should be stored in secrets/config.py in the `nijis_api_key` field.
- A reel of 29mm wide continuous label paper loaded in the printer.
- If on Windows, the Brother driver may be required.
