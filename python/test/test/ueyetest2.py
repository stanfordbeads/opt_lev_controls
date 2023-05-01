from pyueye import ueye
import numpy as np
import cv2
import sys, os

# probably closer to working comp. to ueyetest.py
#---------------------------------------------------------------------------------------------------------------------------------------

#Variables
hCam = ueye.HIDS(0)             #0: first available camera;  1-254: The camera with the specified camera ID
sInfo = ueye.SENSORINFO()
cInfo = ueye.CAMINFO()
pcImageMemory = ueye.c_mem_p()
MemID = ueye.int()
rectAOI = ueye.IS_RECT()
pitch = ueye.INT()
nBitsPerPixel = ueye.INT(24)    #24: bits per pixel for color mode; take 8 bits per pixel for monochrome
channels = 3                    #3: channels for color mode(RGB); take 1 channel for monochrome
m_nColorMode = ueye.INT()		# Y8/RGB16/RGB24/REG32
bytes_per_pixel = int(nBitsPerPixel / 8)
#---------------------------------------------------------------------------------------------------------------------------------------
print("START")


# Starts the driver and establishes the connection to the camera
nRet = ueye.is_InitCamera(hCam, None)
if nRet != ueye.IS_SUCCESS:
    print("is_InitCamera ERROR")

# Reads out the data hard-coded in the non-volatile camera memory and writes it to the data structure that cInfo points to
nRet = ueye.is_GetCameraInfo(hCam, cInfo)
if nRet != ueye.IS_SUCCESS:
    print("is_GetCameraInfo ERROR")

# You can query additional information about the sensor type used in the camera
nRet = ueye.is_GetSensorInfo(hCam, sInfo)
if nRet != ueye.IS_SUCCESS:
    print("is_GetSensorInfo ERROR")


#Ret = ueye.is_ResetToDefault( hCam)
#if nRet != ueye.IS_SUCCESS:
#    print("is_ResetToDefault ERROR")


# Set display mode to DIB
nRet = ueye.is_SetDisplayMode(hCam, ueye.IS_SET_DM_DIB)

 

if nRet != ueye.IS_SUCCESS:
    print("IS_PIXELCLOCK_CMD_GET_NUMBER ERROR")

# Set the right color mode
if int.from_bytes(sInfo.nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_BAYER:
    # setup the color depth to the current windows setting
    ueye.is_GetColorDepth(hCam, nBitsPerPixel, m_nColorMode)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print("IS_COLORMODE_BAYER: ", )
    print("\tm_nColorMode: \t\t", m_nColorMode)
    print("\tnBitsPerPixel: \t\t", nBitsPerPixel)
    print("\tbytes_per_pixel: \t\t", bytes_per_pixel)
    print()

elif int.from_bytes(sInfo.nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_CBYCRY:
    # for color camera models use RGB32 mode
    m_nColorMode = ueye.IS_CM_BGRA8_PACKED
    nBitsPerPixel = ueye.INT(32)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print("IS_COLORMODE_CBYCRY: ", ) 
    print("\tm_nColorMode: \t\t", m_nColorMode)
    print("\tnBitsPerPixel: \t\t", nBitsPerPixel)
    print("\tbytes_per_pixel: \t\t", bytes_per_pixel)
    print()

elif int.from_bytes(sInfo.nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_MONOCHROME:
    # for color camera models use RGB32 mode
    m_nColorMode = ueye.IS_CM_MONO8
    nBitsPerPixel = ueye.INT(8)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print("IS_COLORMODE_MONOCHROME: ", )
    print("\tm_nColorMode: \t\t", m_nColorMode)
    print("\tnBitsPerPixel: \t\t", nBitsPerPixel)
    print("\tbytes_per_pixel: \t\t", bytes_per_pixel)
    print()

else:
    # for monochrome camera models use Y8 mode
    m_nColorMode = ueye.IS_CM_MONO8
    nBitsPerPixel = ueye.INT(8)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print("else")

# set region of interest
# max width = 752
# max height = 480
widthdummy = ueye.int(752)
heightdummy = ueye.int(480)
rect_aoi = ueye.IS_RECT()
rect_aoi.s32X = ueye.int(0)
print(ueye.int(0))
rect_aoi.s32Y = ueye.int(0)
rect_aoi.s32Width = ueye.int(widthdummy)
print(ueye.int(widthdummy))
rect_aoi.s32Height = ueye.int(heightdummy)
# Can be used to set the size and position of an "area of interest"(AOI) within an image
nRet = ueye.is_AOI(hCam, ueye.IS_AOI_IMAGE_GET_AOI, rect_aoi, ueye.sizeof(rect_aoi))
if nRet != ueye.IS_SUCCESS:
    print("is_AOI ERROR")


x = ueye.int()
nRet = ueye.is_PixelClock(hCam, ueye.IS_PIXELCLOCK_CMD_GET, x, ueye.sizeof(rect_aoi))
print(f"is_PixelClock ERROR {nRet}")
# max pixel clock 40 MHz, optimized 14 MHz
nRet = ueye.is_Exposure(hCam, ueye.IS_EXPOSURE_CMD_GET_CAPS, ueye.int(2), ueye.sizeof(rect_aoi))
if nRet != ueye.IS_SUCCESS:
    print(f"exposure ERROR {nRet}")
else:
    print(ueye.IS_EXPOSURE_CMD_GET_CAPS)
    print('exp?')


# use full frame
#nRet = ueye.is_AOI(hCam, ueye.IS_AOI_IMAGE_GET_AOI, rectAOI, ueye.sizeof(rectAOI))
#width = rectAOI.s32Width
#height = rectAOI.s32Height
width = rect_aoi.s32Width
height = rect_aoi.s32Height

# Prints out some information about the camera and the sensor
print("Camera model:\t\t", sInfo.strSensorName.decode('utf-8'))
print("Camera serial no.:\t", cInfo.SerNo.decode('utf-8'))
print("Maximum image width:\t", width)
print("Maximum image height:\t", height)
print()

#---------------------------------------------------------------------------------------------------------------------------------------

# Allocates an image memory for an image having its dimensions defined by width and height and its color depth defined by nBitsPerPixel
nRet = ueye.is_AllocImageMem(hCam, width, height, nBitsPerPixel, pcImageMemory, MemID)
if nRet != ueye.IS_SUCCESS:
    print("is_AllocImageMem ERROR")
else:
    # Makes the specified image memory the active memory
    nRet = ueye.is_SetImageMem(hCam, pcImageMemory, MemID)
    if nRet != ueye.IS_SUCCESS:
        print("is_SetImageMem ERROR")
    else:
        # Set the desired color mode
        nRet = ueye.is_SetColorMode(hCam, m_nColorMode)

# get frame rate?
fps = ueye.c_double()
nRet = ueye.is_GetFramesPerSecond(hCam, fps)
#print(f"is_GetFramesPerSecond {nRet}")
#print(fps)

#fps2 = ueye.double(2000)
#nRet =ueye.is_SetFrameRate(hCam, fps, fps2)
#print(f"is_SetFramesPerSecond {nRet}")

# Activates the camera's live video mode (free run mode) ueye.IS_DONT_WAIT
t=40
nRet = ueye.is_CaptureVideo(hCam, t)
#print(f"is_CaptureVideo {nRet}")


# Enables the queue mode for existing image memory sequences
nRet = ueye.is_InquireImageMem(hCam, pcImageMemory, MemID, width, height, nBitsPerPixel, pitch)
if nRet != ueye.IS_SUCCESS:
    print("is_Inquir eImageMem ERROR")
else:
    print("Press q to leave the programm")

#---------------------------------------------------------------------------------------------------------------------------------------
i=0
# Continuous image display
while(nRet == ueye.IS_SUCCESS) and i< 10:

    # In order to display the image in an OpenCV window we need to...
    # ...extract the data of our image memory
    array = ueye.get_data(pcImageMemory, width, height, nBitsPerPixel, pitch, copy=False)

    # bytes_per_pixel = int(nBitsPerPixel / 8)

    # ...reshape it in an numpy array...
    frame = np.reshape(array,(height.value, width.value, bytes_per_pixel))

    # ...resize the image by a half
    frame = cv2.resize(frame, (0, 0),fx=.5, fy=.5) 

    i=i+1
    #print(np.shape(frame))
    #print(np.mean(frame))
    #(240, 376, 4) for fx=fy=.5
    
#---------------------------------------------------------------------------------------------------------------------------------------
    #Include image data processing here

#---------------------------------------------------------------------------------------------------------------------------------------

    #...and finally display it
    cv2.imshow("SimpleLive_Python_uEye_OpenCV", frame)

    # Press q if you want to end the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
#---------------------------------------------------------------------------------------------------------------------------------------
print(np.shape(frame[:,:,1]))
#print(frame[:,:,1])
print(np.amax(frame))
print(np.argmax(frame[:,:,2], axis=1))
print(np.shape(np.argmax(frame[:,:,2], axis=0)))

# Releases an image memory that was allocated using is_AllocImageMem() and removes it from the driver management
ueye.is_FreeImageMem(hCam, pcImageMemory, MemID)

# Disables the hCam camera handle and releases the data structures and memory areas taken up by the uEye camera
ueye.is_ExitCamera(hCam)

# Destroys the OpenCv windows
cv2.destroyAllWindows()

print()
print("END")

#frame[:,:,1] max ind
#[413 412 413 399 378 313 371 434 391 403 402 333 373 393 392 392 413 358
# 381 381 381 368 351 399 389 417 388 388 388 396 370 369 391 376 382 382
# 440 439 402 398 443 351 391 398 391 392 393 405 387 387 389 384 355 388
# 389 401 396 368 399 396 394 393 376 376 416 429 354 392 393 395 407 390
# 390 404 405 400 389 389 401 401 386 385 385 374 374 373 402 396 397 368
# 369 398 398 379 379 406 377 410 411 392 392 385 411 385 373 373 381 382
# 385 385 395 380 380 392 392 390 391 391 396 396 390 389 376 376 397 393
# 393 385 382 397 377 375 388 375 372 372 379 389 388 379 372 371 369 368
# 368 368 368 365 364 361 361 361 360 357 356 355 354 353 352 350 350 350
# 350 347 347 347 346 346 316 315 346 346 347 313 313 327 324 323 323 343
# 342 319 316 315 314 313 312 311 309 310 311 311 309 310 311 311 310 310
# 310 310 311 311 310 310 310 310 310 310 311 314 314 313 312 310 310 310
# 315 307 306 300 300 300 300 299 298 297 296 296 296 296 296 295 295 295
# 295 296 297 297 296 296 297 298 299 300 301 301 301 301 300 299 298 298
# 298 297 296 294 294 292 293 296 296 296 296 291 290 289 295 296 296 296
# 296 296 296 296 301 301 302 301 300 299 298 298 301 301 303 303 302 302
# 303 304 305 311 313 308 315 304 316 318 318 320 321 322 322 322 322 322
# 325 326 327 330 330 330 335 347 346 345 344 343 349 353 353 353 352 351
# 350 350 350 350 350 349 360 359 358 357 356 356 357 358 361 361 359 360
# 361 362 362 362 363 363 365 365 365 365 364 363 363 367 366 366 367 367
# 367 368 368 374 375 375 375 375 375 376 379 382 382 381 380 383 383 384
# 391 392 393 394 395 412 392 406 409 410 410 410 408 408 408 408 414 413
# 414 413 401 415 395 396 418 418 399 425 424 395 403 390 391 392 401 401
# 390 414 383 393 397 391 407 407 391 376 390 389 430 383 382 383 383 375
# 385 383 399 399 389 389 415 416 420 386 387 385 385 402 379 385 379 421
# 384 384 385 398 398 398 398 394 395 396 396 390 391 391 353 354 370 416
# 416 415 368 358 359 346 374 378 423 416 371 371]

#frame[:,:,2] max ind
#[371 379 380 347 344 344 391 391 391 403 403 404 393 411 412 412 391 403
# 390 389 389 399 399 370 369 379 407 389 390 389 367 368 367 391 383 383
# 383 390 391 389 389 389 389 389 388 379 379 387 388 388 388 389 389 389
# 389 389 393 393 393 403 402 390 393 392 392 380 380 379 391 391 390 389
# 389 389 389 389 389 402 402 387 387 387 377 374 374 397 397 396 397 398
# 397 383 383 379 379 407 407 397 397 396 395 410 410 385 384 384 384 385
# 385 380 379 379 379 392 392 385 385 396 397 391 391 376 376 386 386 385
# 377 376 375 374 359 360 362 369 366 366 360 360 360 360 360 360 360 353
# 351 353 353 353 353 352 352 351 346 345 346 347 348 347 344 343 343 343
# 342 340 326 339 319 318 304 303 314 313 310 310 312 312 312 312 312 311
# 310 310 309 308 308 307 306 306 305 305 306 306 306 306 306 305 304 305
# 306 306 306 306 306 305 305 305 301 305 305 298 296 296 296 295 294 294
# 294 293 293 294 293 293 292 290 290 289 289 290 290 290 290 290 290 291
# 291 290 290 291 291 291 291 291 291 291 291 291 290 289 289 288 288 288
# 287 287 286 286 285 285 285 284 285 286 286 286 286 285 285 285 286 287
# 288 289 289 288 288 288 288 288 288 289 289 289 291 292 292 293 293 293
# 293 293 293 295 297 298 298 298 299 300 300 300 301 303 304 304 313 314
# 314 313 312 312 312 314 317 318 320 323 324 324 324 327 328 333 333 332
# 332 333 334 337 338 338 338 338 341 342 342 343 343 344 344 347 347 346
# 349 349 349 349 349 350 350 349 349 350 350 350 350 350 351 351 352 353
# 354 355 356 356 356 357 358 359 361 362 363 364 364 363 363 367 369 370
# 370 370 371 371 372 372 379 378 378 377 377 381 377 393 394 394 400 413
# 413 423 412 406 406 418 418 418 417 408 393 404 404 392 397 398 398 399
# 399 394 395 395 395 395 392 390 407 417 416 407 407 378 381 381 398 384
# 383 383 395 395 389 389 389 403 385 385 386 401 401 387 387 386 385 389
# 389 384 384 387 394 393 393 396 395 393 393 412 413 412 413 400 415 415
# 415 387 387 359 359 379 379 392 400 359 359 359]

# max ind 1/4 sized
#[178 174 180 173 180 194 191 195 195 195 195 199 184 190 184 184 201 195
# 182 195 195 195 189 189 194 194 194 202 196 196 196 195 190 190 195 195
# 194 193 193 193 193 192 197 197 199 184 191 189 203 198 197 205 192 192
# 192 190 196 195 195 198 195 193 193 189 188 186 186 184 183 180 181 181
# 177 177 177 176 173 174 174 173 172 172 171 160 158 157 155 157 158 158
# 156 155 154 153 153 153 153 153 153 153 153 153 153 153 153 148 152 150
# 147 147 148 147 145 147 147 145 146 146 146 146 147 147 146 146 145 144
# 144 144 143 143 143 143 143 143 144 145 145 145 146 145 145 146 147 147
# 147 148 149 149 150 150 152 152 157 157 156 159 162 162 163 164 167 167
# 167 169 169 170 171 172 173 174 174 175 175 175 175 177 177 176 176 179
# 179 178 179 180 181 182 182 184 185 187 190 190 190 189 191 197 197 200
# 206 206 209 209 199 196 202 199 199 198 197 198 203 203 202 189 190 191
# 191 200 195 195 195 193 193 193 193 194 192 192 197 196 196 203 194 194
# 193 197 196 196 196 180]