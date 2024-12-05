import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import asyncio
import threading
from conf_client import ConferenceClient
from util import *


def display_image(img, frame_label):
    """ Display PIL image on Tkinter label. """
    img_tk = ImageTk.PhotoImage(img)
    frame_label.img_tk = img_tk  # Keep a reference!
    frame_label.config(image=img_tk)


class ConferenceClientGUI:
    def __init__(self, root):
        self.root = root
        self.client = ConferenceClient()  # Assuming this class already exists

        # Setup UI elements
        self.root.title("Video Conference Client")
        self.root.geometry("800x600")

        self.status_label = tk.Label(root, text="Status: Not connected", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # Buttons for meeting actions
        self.create_button = tk.Button(root, text="Create Conference", command=self.create_conference)
        self.create_button.pack(pady=5)

        self.join_button = tk.Button(root, text="Join Conference", command=self.join_conference)
        self.join_button.pack(pady=5)

        self.quit_button = tk.Button(root, text="Quit Conference", command=self.quit_conference)
        self.quit_button.pack(pady=5)

        self.cancel_button = tk.Button(root, text="Cancel Conference", command=self.cancel_conference)
        self.cancel_button.pack(pady=5)

        # Camera Stream Display
        self.camera_frame = tk.Label(root)
        self.camera_frame.pack(pady=10)

        # Screen Stream Display
        self.screen_frame = tk.Label(root)
        self.screen_frame.pack(pady=10)

        self.camera_stream = None
        self.screen_stream = None
        self.running = False

        # Start the asyncio event loop in a separate thread
        self.asyncio_thread = threading.Thread(target=self.start_asyncio_loop, daemon=True)
        self.asyncio_thread.start()

        # Schedule the update function periodically to update the UI
        self.root.after(100, self.update_video_stream)

    def update_status(self, status):
        self.status_label.config(text=f"Status: {status}")

    def update_video_stream(self):
        """ Update camera and screen streams. """
        if self.running:
            # Capture and display the camera feed
            camera_img = self.capture_camera()
            if camera_img:
                display_image(camera_img, self.camera_frame)

            # Capture and display the screen
            screen_img = self.capture_screen()
            if screen_img:
                display_image(screen_img, self.screen_frame)

            # Schedule next frame update
            self.root.after(100, self.update_video_stream)

    async def capture_camera(self):
        """ Capture a frame from the camera. """
        if self.client.on_meeting:
            ret, frame = capture_camera()  # Assuming capture_camera() is an async method
            if ret:
                return Image.fromarray(frame)
        return None

    async def capture_screen(self):
        """ Capture a screenshot of the screen. """
        if self.client.on_meeting:
            screen_img = capture_screen()  # Assuming capture_screen() is an async method
            return screen_img
        return None

    def create_conference(self):
        """ Handle create conference action. """
        async def create():
            await self.client.create_conference()
            self.update_status("Conference created. You have already joined.")
        # Run asyncio method in the background
        asyncio.run(create())

    def join_conference(self):
        """ Handle join conference action. """
        conference_id = self.get_conference_id()
        if conference_id:
            async def join():
                await self.client.join_conference(conference_id)
                self.update_status(f"Joined Conference {conference_id}")
                self.start_video_stream()

            asyncio.run(join())

    def quit_conference(self):
        """ Handle quit conference action. """
        conference_id = self.get_conference_id()
        if conference_id:
            async def quit():
                await self.client.quit_conference(conference_id)
                self.update_status(f"Left Conference {conference_id}")
                self.stop_video_stream()
            asyncio.run(quit())

    def cancel_conference(self):
        """ Handle cancel conference action. """
        conference_id = self.get_conference_id()
        if conference_id:
            async def cancel():
                await self.client.cancel_conference(conference_id)
                self.update_status(f"Canceled Conference {conference_id}")
            asyncio.run(cancel())

    def start_video_stream(self):
        """ Start capturing and displaying video streams. """
        self.running = True
        self.update_video_stream()

    def stop_video_stream(self):
        """ Stop capturing and displaying video streams. """
        self.running = False

    def get_conference_id(self):
        """ Prompt for conference ID. """
        conference_id = simpledialog.askstring("Conference ID", "Enter Conference ID:")
        return conference_id

    def start_asyncio_loop(self):
        """ Start the asyncio event loop in a separate thread. """
        asyncio.run(self.client.main())  # Run the asyncio-based conference client


if __name__ == "__main__":
    root = tk.Tk()
    app = ConferenceClientGUI(root)
    root.mainloop()
