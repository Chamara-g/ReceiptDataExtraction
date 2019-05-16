import io
import os

import re

import json

from google.cloud.vision import types
from google.cloud import vision

from PIL import Image, ImageDraw
# 530516 551791 551838.PNG
GOOGLE_API_KEY = "F:/project/CNN_test/data/google_cloud_api_key.txt"
IMG_FILE = "F:/project/CNN_test/data/receipts/4/crop/534727.png"

# Provide authentication credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_API_KEY

def detect_words(path):
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    momsList = searchMoms(texts)

    vat_value_col = []
    precentage_value_col = []

    result_vat = []
    result_precentage = []

    if( len(momsList) == 0 or not momsList ):
        print('havent moms values')
    else:    
        vat_value_list,precentage_value_list = extract_vat_and_precentage(momsList,texts)
        
        if( len(vat_value_list) == 1 and vat_value_list == precentage_value_list):
            print('+len(vat_value_list)(1)')
            vat_value_col = vat_value_list
            precentage_value_col = precentage_value_list
        else:
            for i in range(0,len(vat_value_list)):
                if( vat_value_list[i] != precentage_value_list[i] ):       
                    vat_value_col = vat_value_list[i]
                    precentage_value_col = precentage_value_list[i]

        for i in range(0,len(vat_value_col)):
            if( precentage_value_col[i] == 'Tot' or precentage_value_col[i] == 'Total' or precentage_value_col[i] == 'TOTAL'):
                print('+')
            else:
                print(precentage_value_col[i])
                result_vat.append(vat_value_col[i])
                result_precentage.append(precentage_value_col[i])
        print(result_vat)
        print(result_precentage)

def extract_vat_and_precentage(momsList,texts):
    vat_value_list = []
    precentage_value_list = []

    for moms in momsList:
        print('-------start-------')
        moms = moms.bounding_poly

        bottomLeft = (moms.vertices[0].x,moms.vertices[0].y)
        bottomRight = (moms.vertices[1].x,moms.vertices[1].y)
        topRight = (moms.vertices[2].x,moms.vertices[2].y)
        topLeft = (moms.vertices[3].x,moms.vertices[3].y) 

        # draw_square(topLeft,topRight,bottomLeft,bottomRight)

        im = Image.open("drawn_grid.png")
        xmax, ymax = im.size

        verticalWordList = find_vertical_words(texts, topLeft, topRight, bottomLeft, ymax)
        print("verticalWordList len " + "{}".format(len(verticalWordList)) )
        
        if( len(verticalWordList) == 0 ):
            print('+havent vertical values')
        else:    
            sortVerticalList = sort_list(verticalWordList)
            print('sort')
            
            most_prob_vat_values = find_near_by_values(topLeft, sortVerticalList)
            print("most_prob_vat_values len " + "{}".format(len(most_prob_vat_values)) )

            if( len(most_prob_vat_values) == 0 ):
                print('havent vat value(most_prob_vat_values)')
            else:
                vat_value,percentage_values = percentage_and_vat_filter(texts, most_prob_vat_values)
                print("percentage_values len " + "{}".format(len(percentage_values)) )

                # print(vat_value)
                # print(percentage_values)    
                vat_value_list.append(vat_value)
                precentage_value_list.append(percentage_values)

    return vat_value_list,precentage_value_list            

# search moms word in receipt
# def searchMoms(texts):
#     momsList = []
#     for text in texts:
#         # print(text.description)
#         if (text.description == "MOMS" or text.description == "Moms" or text.description == "moms" or text.description == "Mom" or text.description == "Belopp"):
#             momsList.append(text)
#     return momsList

def searchMoms(texts):
    momsList = []
    for text in texts:
        # print(text.description)
        if ( re.search( r'(m|n|r)o(m|n|r)s', text.description, re.I) or text.description == "Belopp"):
            momsList.append(text)
    return momsList

def find_vertical_words(texts, topLeft, topRight, bottomLeft, ymax):
    verticalWordList = []
    
    for text in texts:
        boundry = text.bounding_poly

        tempBottomLeft = ( boundry.vertices[0].x, boundry.vertices[0].y )
        tempBottomRight = ( boundry.vertices[1].x, boundry.vertices[1].y )
        tempTopRight = ( boundry.vertices[2].x, boundry.vertices[2].y )
        tempTopLeft = ( boundry.vertices[3].x, boundry.vertices[3].y )     

        # draw_line( ((topLeft[0] - 15), 0 ) , ((topLeft[0] - 15), ymax ) )
        # draw_line( ((topRight[0] + 25), 0 ) , ((topRight[0] + 25), ymax ) )

        if( ( (topLeft[0] - 15) <= tempTopLeft[0]) and ( (topRight[0] + 25) >= tempTopRight[0]) and bottomLeft[1] <= tempBottomLeft[1] and vatFilter(text.description) ):            
            print(text.description)
            verticalWordList.append(text)
    return verticalWordList

def find_near_by_values(topLeft, verticalWordList):
    tempTopLeft = topLeft[1]
    margin = verticalWordList[0].bounding_poly.vertices[3].y - topLeft[1]
    
    most_prob_vat_values = []
    
    if( margin >= 40):
        print(margin)
        print('+margin not valid')
    else:
        for vatValue in verticalWordList:
            vatValueBoundry = vatValue.bounding_poly

            if( (vatValueBoundry.vertices[3].y - tempTopLeft) >= margin-5 and (vatValueBoundry.vertices[3].y -tempTopLeft) <= margin+5 ):
                print(vatValue.description)
                most_prob_vat_values.append(vatValue)
            tempTopLeft = vatValueBoundry.vertices[3].y    
    return most_prob_vat_values

def sort_list(verticalWordList):
    for i in range(len(verticalWordList)):
        for j in range(len(verticalWordList)):
            if( verticalWordList[i].bounding_poly.vertices[2].y <= verticalWordList[j].bounding_poly.vertices[2].y):
                temp = verticalWordList[i]
                verticalWordList[i] = verticalWordList[j]
                verticalWordList[j] = temp
    return verticalWordList

def vatFilter(word):
    i=0
    valid = True
    while(len(word) != i):
        if( word[i].isnumeric() or word[i] == ',' or word[i] == '.'):
            k=0
        else:
            # print("not valid")
            valid = False     
        i=i+1
    if( i<=1 ):
        valid = False
    return valid

def precentageFilter(word):
    valid = True
    if(len(word)==1):
        valid = False
    elif( word == 'MOMS'):
        valid = False
    return valid

def percentage_and_vat_filter(texts, most_prob_vat_values):
    tempLeft = 0
    value = ''
    percentageList = []
    vatList = []
    print('-------------')
    for vatValue in most_prob_vat_values:
        vatValueBoundry = vatValue.bounding_poly

        tempLeft = 0
        value = ''
                        
        # print(vatValue.description)
        for text in texts:
            boundry = text.bounding_poly

            BottomLeft = ( boundry.vertices[0].x, boundry.vertices[0].y )
            BottomRight = ( boundry.vertices[1].x, boundry.vertices[1].y )
            TopRight = ( boundry.vertices[2].x, boundry.vertices[2].y )
            TopLeft = ( boundry.vertices[3].x, boundry.vertices[3].y ) 
                
            if( (TopRight[1] - 8 <= vatValueBoundry.vertices[2].y) and (BottomRight[1] + 8 >= vatValueBoundry.vertices[1].y) and precentageFilter(text.description) ):
                # print(text.description)   
                if( tempLeft == 0 ):
                    tempLeft = TopLeft[0]
                    value = text.description
                else:                   
                    if( TopLeft[0] <= tempLeft ):
                        tempLeft = TopLeft[0]
                        value = text.description
                    else:
                        k=0        
        percentageList.append(value)
        vatList.append(vatValue.description)
    print('-------------')
    return vatList,percentageList    

def draw_square(tl, tr, bl, br):    
    im = Image.open(IMG_FILE)
    d = ImageDraw.Draw(im)

    line_color = (0, 0, 255)

    d.line([tl, tr, br, bl, tl], fill=line_color, width=2)

    im.save("drawn_grid.png")

def draw_line(spoint,epoint):
    im = Image.open("drawn_grid.png")
    d = ImageDraw.Draw(im)

    line_color = (247, 7, 7)
    d.line([spoint,epoint], fill=line_color, width=2)

    im.save("drawn_grid.png")

detect_words(IMG_FILE)            