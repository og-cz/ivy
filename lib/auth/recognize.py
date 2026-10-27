import time
import cv2

TRAINER_PATH = "lib/auth/trainer/trainer.yml"
CASCADE_PATH = "lib/auth/haarcascade_frontalface_default.xml"

# LBPH distance: 0 is a perfect match, lower is stricter
MATCH_THRESHOLD = 100
TIMEOUT_SECONDS = 30


def AuthenticateFace():

    flag = 0
    # Local Binary Patterns Histograms
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    recognizer.read(TRAINER_PATH)  # load trained model
    # initializing haar cascade for object detection approach
    faceCascade = cv2.CascadeClassifier(CASCADE_PATH)

    font = cv2.FONT_HERSHEY_SIMPLEX  # denotes the font type

    names = [
        "",
        "Carl Zeus",
    ]  # names, leave first empty bcz counter starts from 0

    # cv2.CAP_DSHOW removes a warning on Windows; other platforms use the default backend
    backend = cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else cv2.CAP_ANY
    cam = cv2.VideoCapture(0, backend)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Define min window size to be recognized as a face
    minW = 0.1 * cam.get(cv2.CAP_PROP_FRAME_WIDTH)
    minH = 0.1 * cam.get(cv2.CAP_PROP_FRAME_HEIGHT)

    deadline = time.time() + TIMEOUT_SECONDS

    try:
        while time.time() < deadline:

            ret, img = cam.read()  # read the frames using the above created object
            if not ret or img is None:
                # camera busy or not ready yet
                cv2.waitKey(50)
                continue

            # The function converts an input image from one color space to another
            converted_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            faces = faceCascade.detectMultiScale(
                converted_image,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(int(minW), int(minH)),
            )

            for x, y, w, h in faces:

                # used to draw a rectangle on any image
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # to predict on every single image
                id, distance = recognizer.predict(converted_image[y : y + h, x : x + w])

                if distance < MATCH_THRESHOLD and id < len(names):
                    label = names[id]
                    flag = 1
                else:
                    label = "unknown"
                accuracy = "  {0}%".format(round(100 - distance))

                cv2.putText(img, label, (x + 5, y - 5), font, 1, (255, 255, 255), 2)
                cv2.putText(
                    img, accuracy, (x + 5, y + h - 5), font, 1, (255, 255, 0), 1
                )

            cv2.imshow("camera", img)

            k = cv2.waitKey(10) & 0xFF  # Press 'ESC' for exiting video
            if k == 27 or flag == 1:
                break
    finally:
        # Do a bit of cleanup
        cam.release()
        cv2.destroyAllWindows()

    return flag
