from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import uvicorn
app = FastAPI()

# Global variable to store WebSocket connection
websocket_connection = None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global websocket_connection
    await websocket.accept()
    websocket_connection = websocket  # Store the connection
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message from client: {data}")
            await websocket.send_text(f"Message received: {data}")  # Send a response back to the client
    except WebSocketDisconnect:
        print("Client disconnected")
        websocket_connection = None  # Clear the connection when the client disconnects


# Function to send message from another function
async def send_message_to_client(message: str):
    global websocket_connection
    if websocket_connection:
        await websocket_connection.send_text(message)



@app.get("/send-message")
async def send_message():
    await send_message_to_client("Hello from another function!")
    return {"message": "Message sent to client"}

if __name__ == "__main__":
    print('server is stablished')
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    print('server is stablished')