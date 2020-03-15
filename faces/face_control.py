from PIL import Image
import cv2
import logging
import numpy


def find_faces():
    imagePath = 'faces/image.png'
    cascPath = "faces/haarcascade_frontalface_default.xml"

    # Create the haar cascade
    faceCascade = cv2.CascadeClassifier(cascPath)

    # Read the image
    image = cv2.imread(imagePath)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect faces in the image
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(30, 30)
        #flags = cv2.cv.CV_HAAR_SCALE_IMAGE
    )

    logging.info("Found {0} faces!".format(len(faces)))

    # Draw a rectangle around the faces
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imwrite('faces/image_rect.png', image)
    return faces

def add_goblin_face(faces):
    img = Image.open('faces/image.png')
    rand_number = numpy.random.randint(low=1, high=5, size=len(faces))
    for i in range(len(faces)):
        goblin_name = 'faces/goblin_face/goblin_face-'+str(rand_number[i])+'.png'
        goblin_img = Image.open(goblin_name)
        x, y, w, h = faces[i] 
        goblin_img = goblin_img.resize((int(w*1.18), int(h*1.4)))
        img.paste(goblin_img, (x-int(w*0.09), y-int(h*0.2)), goblin_img)

    img.save('faces/goblin_image.png')