from flask import Flask
from flask import render_template
from flask import Response, request, jsonify
app = Flask(__name__)

#for gpt
import os
import openai

import secrets
openai.api_key = secrets.SECRET_KEY



#for dalle
import json
from base64 import b64decode
from pathlib import Path



#Thid is the basic data representation
headline_data = {
  "headline":"",
  "summary":"",
  "keywords":[],
  "generations":[]
}

# This is what the representation looks like when there are keywords and images generated
# sample_headline_data_2 = {
#    "generations": [
#       {
#          "prompt": "Santos’s Lies Were Known to Some Well-Connected Republicans",
#          "url": "static/generated_images/Santo-1673801357/Santo-1673801357-0.png"
#       },
#       {
#          "prompt": "Santos’s Lies Were Known to Some Well-Connected Republicans",
#          "url": "static/generated_images/Santo-1673801375/Santo-1673801375-0.png"
#       }
#    ],
#    "headline": "Santos’s Lies Were Known to Some Well-Connected Republicans",
#    "keywords": [
#       "Santos",
#       "Lying",
#       "Republican",
#       "2022",
#       "Suspicion",
#       "Campaign",
#       "Upperechelons",
#       "Republicans",
#       "Turned a Blind Eye",
#       "Connection"
#    ],
#    "summary": "George Santos inspired no shortage of suspicion during his 2022 campaign, including in the upper echelons of his own party, yet many Republicans looked the other way."
# }



sample_headline_data_1 = {

    "headline": "See a new comet before it vanishes for 400 years",
    "summary": "CAPE CANAVERAL, Fla. (AP) — A newly discovered comet is swinging through our cosmic neighborhood for the first time in more than 400 years. Stargazers across the Northern Hemisphere should catch a glimpse as soon as possible — either this week or early next — because it will be another 400 years before the wandering ice ball returns. The comet, which is kilometer-sized (1/2-mile), will sweep safely past Earth on Sept. 12, passing within 78 million miles (125 million kilometers).",
    "keywords": [],
    "generations": [],
}



#### INIT with example data
# headline_data = sample_headline_data_1





@app.route('/submit_headline', methods=['GET', 'POST'])
def submit_headline():
    global headline_data
    data = request.get_json()   

    headline_data["headline"] = data["headline"]
    headline_data["summary"] = data["summary"]

    #send back the WHOLE array of data, so the client can redisplay it
    return jsonify(headline_data)


@app.route('/get_images', methods=['GET', 'POST'])
def get_images():
    global headline_data
    data = request.get_json()   
    # print(data)
    prompt = data["prompt"]
    new_images = generate_images(prompt)

    for i in new_images:
        headline_data["generations"].append(i) 

    #just send new images
    return jsonify(new_images)


def generate_images(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="256x256",
        response_format="b64_json",
    )

    #create json file for image
    DATA_DIR = Path.cwd() / "responses"
    DATA_DIR.mkdir(exist_ok=True)
    JSON_FILE = DATA_DIR / f"{prompt[:5]}-{response['created']}.json"
    with open(JSON_FILE, mode="w", encoding="utf-8") as file:
        json.dump(response, file)  


    #convert json image data file to png
    IMAGE_DIR = Path.cwd() / "static/generated_images" / JSON_FILE.stem

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    with open(JSON_FILE, mode="r", encoding="utf-8") as file:
        response = json.load(file)

    for index, image_dict in enumerate(response["data"]):
        image_data = b64decode(image_dict["b64_json"])
        image_file = IMAGE_DIR / f"{JSON_FILE.stem}-{index}.png"
        with open(image_file, mode="wb") as png:
            png.write(image_data)    

    full_path_to_image = image_file.as_posix()
    url_for_flask = full_path_to_image[full_path_to_image.find('static'):]

    print("url_for_flask")
    print(url_for_flask)

    images = [
        {
            "prompt": prompt,
            "url": url_for_flask, #image_file.as_posix(),
        }
    ]
    print(url_for_flask)
    return images


@app.route('/get_keywords', methods=['GET', 'POST'])
def get_keywords():
    global headline_data

    headline = headline_data["headline"]
    summary = headline_data["summary"]

    keywords = get_keywords_for_headline(headline, summary)
    headline_data["keywords"] = keywords 

    #send back the WHOLE array of data, so the client can redisplay it
    return jsonify(headline_data)


def parse_keywords_from_gpt_response(keyword_response):    
    keyword_list = keyword_response.splitlines()
    new_keyword_list = []
    for i, item in enumerate(keyword_list):
        item = item.strip()
        if item != "":
            item = item[item.index(".") + 1:]
            item = item.strip()
            new_keyword_list.append(item)
    return new_keyword_list
    

def get_keywords_for_headline(headline, summary):
    prompt = "Give me 10 keywords that represent this news headline and summary and format it like this: \n 1. keyword1 \n 2. keyword2 \n 3. keyword three. News headline: "+headline+". News summary: "+summary+"."
    print(prompt)
    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=256)["choices"][0]["text"]
    
    ### PARSE THEM HERE!
    keyword_list = []
    try:
        keyword_list = parse_keywords_from_gpt_response(response)
    except:        
        print("ERROR: gpt keyword response won't parse")
        print(response)

    return keyword_list


@app.route('/')
def home():
    # you can pass in an existing article or a blank one.
    return render_template('home.html', data=headline_data)   


if __name__ == '__main__':
    # app.run(debug = True, port = 4000)    
    app.run(debug = True)




