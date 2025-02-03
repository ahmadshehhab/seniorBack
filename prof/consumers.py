import asyncio
from channels.generic.http import AsyncHttpConsumer
import json

class LongPollingConsumer(AsyncHttpConsumer):
    async def handle(self, body):
        # Simulate a delay to wait for new data
        await asyncio.sleep(5)  # Wait for 5 seconds (simulate polling interval)

        # Example response data
        response_data = {
            "message": "New updates available!",
            "status": "success"
        }

        # Send the response back to the client
        await self.send_response(200, json.dumps(response_data).encode('utf-8'), headers=[
            (b"Content-Type", b"application/json"),
        ])
