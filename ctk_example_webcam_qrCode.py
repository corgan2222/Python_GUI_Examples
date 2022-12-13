import tkinter as tk # pip install tk
import customtkinter # pip install customtkinter
import PIL.Image, PIL.ImageTk # pip install pillow
import cv2 # pip install opencv-python
from pygrabber.dshow_graph import FilterGraph # pip install pygrabber
import numpy as np
import pyzbar.pyzbar as pyzbar

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Webcam with customtkinter and TK.Canvas")
        self.geometry('1100x580')

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=350, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Video Source", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        #get the available video devices
        self.graph = FilterGraph()
 
        # fill combobox with availible video devices
        self.combobox = customtkinter.CTkOptionMenu(self.sidebar_frame, values=self.graph.get_input_devices())
        self.combobox.grid(row=1, column=0, padx=20, pady=(20, 10))

        # connect button
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Connect Camera", command=self.sidebar_button_event)
        self.sidebar_button_1.grid(row=2, column=0, padx=20, pady=10)

        # QR Code Label
        self.qr_label = customtkinter.CTkLabel(self, text="QR")
        self.qr_label.grid(row=2, column=1, padx=20, pady=(10, 0))


    def sidebar_button_event(self):
        print("try to open camera: " + self.combobox.get())   

        for i, device in enumerate(self.graph.get_input_devices() ):   
            if device == self.combobox.get():
                self.video_source = i

        # main window
        self.vid = MyVideoCapture(self.video_source)

        # Create a canvas that can fit the above video source size
        self.canvas = tk.Canvas(self, width = self.vid.width, height = self.vid.height)
        self.canvas.grid(row=0, rowspan=4, column=1)

        self.delay = 15
        self.update()        


    # Get a frame from the video source
    def update(self):        
        return_value, frame = self.vid.get_frame()        

        if return_value:
            try:
                #analyze Frame and check for QR Code
                frame = self.analyzeFrame(frame)

                self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
                self.canvas.create_image(0, 0, image = self.photo, anchor = tk.NW)

            except BaseException:
                    import sys
                    print(sys.exc_info()[0])
                    import traceback
                    print(traceback.format_exc())                
            finally:
                pass    

        self.after(self.delay, self.update)

    #search for QR Code in frame
    def analyzeFrame(self, frame):
        font = cv2.FONT_HERSHEY_SIMPLEX
        image_cv = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        decodedObjects = pyzbar.decode(image_cv)

        for decodedObject in decodedObjects: 
            return self.decodedObjects(decodedObject, frame, font)
        return frame

    #find the QR Code and draw a rectangle around it
    def decodedObjects(self, decodedObject, frame, font):
        points = decodedObject.polygon

        # If the points do not form a quad, find convex hull
        if len(points) > 4 : 
            hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
            hull = list(map(tuple, np.squeeze(hull)))
        else : 
            hull = points;

        # Number of points in the convex hull
        n = len(hull)
            # Draw the convext hull
        for j in range(n):
            cv2.line(frame, hull[j], hull[ (j+1) % n], (255,0,0), 3)

        x = decodedObject.rect.left
        y = decodedObject.rect.top

        barCode: bytes = decodedObject.data
        barCode = barCode.decode()
        cv2.putText(frame, barCode, (x, y), font, 0.5, (0,255,255), 2, cv2.LINE_AA)

        #show the QR Code in the GUI
        self.qr_label.configure(text=barCode)

        return frame 

class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if not self.vid.isOpened():
            return (return_value, None)

        return_value, frame = self.vid.read()
        if return_value:
            # Return a boolean success flag and the current frame converted to BGR
            return (return_value, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            return (return_value, None)

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()


if __name__ == "__main__":
    app = App()
    app.mainloop()
