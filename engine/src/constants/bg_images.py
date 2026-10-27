# File for background image constants. This is where we will store the url's of the background images. They'll be on local disk for now. Leaving space for a "api" url in the future when we switch up the arhitecture and run remotely.
# BG_FOLDER_PATH is the path your bg images are stored.
BG_FOLDER_PATH = {
    "local": "/Users/joseph/Documents/workspace/bg_images",
}

# BG_IMG_URL_MAP is a dictionary with Image Codes as keys and a dictionary and locatio of the images as values of the size selected.
# usa: Image Code
# 2_3: Size Code
# local: Local path to the image
# api: Remote path to the image (future s3 bucket)
BG_IMG_URL_MAP = {
    "usa": {
        "2_3": {
            "local": "/usa/2_3_usa_landscape.png",
            "api": "",
        }
    },
    "usa-ripple": {
        "2_3": {
            "local": "/usa/2_3_usa_rippled.png",
            "api": "",
        }
    },
}

# Convert actual size of the map to ratio size for bg image lookup in BG_IMG_URL_MAP
BG_SIZE_RATIO = {
    "_24_36": "2_3",
}
