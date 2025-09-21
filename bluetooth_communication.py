#!/usr/bin/env python3
import asyncio
import logging
from typing import Any, Dict

from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(name=__name__)

# UUIDs - must match Android app
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

class BLEServer:
    def __init__(self):
        self.server = BlessServer(name="RPi-BLE-Server")
        self.response_message = "READY"
        
    def read_request(self, characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
        """Handle read requests"""
        logger.debug(f"Reading: {self.response_message}")
        return self.response_message.encode()
    
    def write_request(self, characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
        """Handle write requests"""
        message = value.decode('utf-8').strip()
        logger.debug(f"Received: {message}")
        
        if message == "SRT":
            print("Start command received!")
            self.response_message = "SRT_ACK"
            # Add your start logic here
            
        elif message == "END":
            print("End command received!")
            self.response_message = "END_ACK"
            # Add your end logic here
        else:
            self.response_message = f"Echo: {message}"
    
    async def run(self):
        # Add service
        await self.server.add_new_service(SERVICE_UUID)
        
        # Add characteristic
        char_flags = (
            GATTCharacteristicProperties.read |
            GATTCharacteristicProperties.write |
            GATTCharacteristicProperties.indicate
        )
        
        char_permissions = (
            GATTAttributePermissions.readable |
            GATTAttributePermissions.writeable
        )
        
        await self.server.add_new_characteristic(
            SERVICE_UUID,
            CHAR_UUID,
            char_flags,
            None,  # Initial value
            char_permissions
        )
        
        # Set callbacks
        characteristic = self.server.get_characteristic(CHAR_UUID)
        characteristic.set_read_callback(self.read_request)
        characteristic.set_write_callback(self.write_request)
        
        # Start server
        await self.server.start()
        logger.info("BLE Server started")
        
        # Keep running
        await asyncio.Event().wait()

async def main():
    server = BLEServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
