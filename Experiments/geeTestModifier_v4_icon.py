import cv2
import os, random
import numpy as np
from time import sleep

def rotate(image, angle):
    rows, cols = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((cols/2, rows/2), angle, 1)
    rotated = cv2.warpAffine(image, matrix, (cols, rows))

    return rotated

def flip(image, mode):
    # mode0 : 수직 / mode1 : 수평 / mode-1 : 다"줘"
    flip = cv2.flip(image, mode)

    return flip

def shear(image, x, y):
    rows, cols = image.shape[:2]
    matrix = np.float32([[1, x, 0], [y, 1, 0]])
    sheared = cv2.warpAffine(image, matrix, (cols, rows))

    return sheared

def stretch(image, x, y):
    stretched = cv2.resize(image, None, fx = x, fy = y, interpolation = cv2.INTER_LINEAR)

    return stretched

'''
colors = {
    "red": [255,0,0],
    "orange": [255,127,0],
    "yellow": [255,255,0],
    "green": [0,255,0],
    "blue": [0,0,255],
    "indigo": [75,0,130],
    "violet": [148,0,211]
}
'''
colors = {
    "red" : [255, 0, 0]
}

modifiers = {
    "type0": [[]],
    "type1": [["rotate", "+"]],
    "type2": [["rotate", "-"]],
    "type3": [["shear", "+"]],
    "type4": [["shear", "-"]],
    "type5": [["rotate", "+"], ["shear", "+"]],
    "type6": [["rotate", "+"], ["shear", "-"]],
    "type7": [["rotate", "-"], ["shear", "+"]],
    "type8": [["rotate", "-"], ["shear", "-"]],
    "type9": [["rotate", "+"], ["stretch"]],
    "type10": [["rotate", "-"], ["stretch"]]
}

path_icon = "imgFiles/geeTest/icons"
path_background = "imgFiles/geeTest/backgrounds"

length = len(os.listdir(path_icon))

count = 0
for icon in os.listdir(path_icon):
    count += 1
    print(f"작업 중 {count}/{length} : {icon}")

    name = icon.split(".")[0]
    os.makedirs(f"trainDataNew/{name}", exist_ok = True)

    img = cv2.imread(f"{path_icon}/{icon}", cv2.IMREAD_UNCHANGED)
    img_edge = cv2.Canny(img, 300, 400)
    img_bgra = cv2.cvtColor(img_edge, cv2.COLOR_GRAY2BGRA)

    img_bgra[:, :, 3] = img_edge
    img_bgra[:, :, 0:3] = 255

    kernel = [[0, 0, 1, 0], [0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]]
    img_bgra[:, :, 3] = cv2.dilate(img_bgra[:, :, 3], np.array(kernel, dtype = np.uint8), iterations = 1)

    for c in range(len(colors)):
        img_colored = np.zeros_like(img_bgra)
        img_colored[:, :, 0] = colors[list(colors.keys())[c]][2]
        img_colored[:, :, 1] = colors[list(colors.keys())[c]][1]
        img_colored[:, :, 2] = colors[list(colors.keys())[c]][0]
        img_colored[:, :, 3] = img_bgra[:, :, 3]

        keys = list(modifiers.keys())
        for m in range(len(modifiers)):
            key = keys[m]

            for i in range(12):
                result = img_colored.copy()

                for commande in modifiers[key]:
                    if(len(commande) == 0): pass
                    elif(commande[0] == "rotate"):
                        if(commande[1] == "+"):
                            result = rotate(result, random.randint(15, 45))
                        else:
                            result = rotate(result, random.randint(-45, -15))
                    elif(commande[0] == "shear"):
                        if(commande[1] == "+"):
                            result = shear(result, random.uniform(0.1, 0.2), 0)
                        else:
                            result = shear(result, random.uniform(-0.2, -0.1), 0)
                    elif(commande[0] == "stretch"):
                        result = stretch(result, random.uniform(1.2, 1.4), 1.0)

                num = (i + 1) % 6 if (i + 1) % 6 != 0 else 6
                bg = cv2.imread(f"{path_background}/background{num}.png", cv2.IMREAD_UNCHANGED)
                height, width = map(lambda x: x-50, bg.shape[:2])

                height_random, width_random = random.randint(0, height - 1), random.randint(0, width - 1)
                bg_morceau = bg[height_random : height_random + 50, width_random : width_random + 50]

                for h in range(48):
                    for w in range(48):
                        if(result[h, w, 3] != 0):
                            bg_morceau[h+1, w+1, 0:3] = result[h, w, 0:3]

                bg_morceau_edge = cv2.Canny(bg_morceau, 50, 150)

                cv2.imwrite(f"trainDataNew/{name}/{c}_{m}_{i}.png", bg_morceau_edge)

path_background = "imgFiles/geeTest/backgrounds"
for i in range(6):
    img = cv2.imread(f"{path_background}/background{i+1}.png")
    img = cv2.Canny(img, 300, 400)
    cv2.imwrite(f"trainDataNew/background/{i+1}.png", img)
    height, width = img.shape[:2]

    for h in range(0, height - 50, 10):
        for w in range(0, width - 50, 10):
            morceau = img[h : h + 50, w : w + 50]

            cv2.imwrite(f"trainDataNew/background/{i+1}_{h}_{w}.png", morceau)
