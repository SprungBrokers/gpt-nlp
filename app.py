import os
import json
import openai
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/", methods=("GET", "POST"))

def index():
    if request.method == "POST":
        statement = request.form["statement"]
        question_response = openai.Completion.create(
            model="text-davinci-003",
            prompt=check_question(statement),
            temperature=0.6,
            max_tokens=1000
        )
        boolean = question_response.choices[0].text[2:]
        print(boolean)
        if boolean == 'True':
            chat_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                {"role": "user", "content": """Respond to the user as if you were a travel reccomendation AI. Keep your responses short."""},
                {"role": "user", "content": statement}
                ],
                # temperature=0.6,
                max_tokens=1000
            )
            return redirect(url_for("index", result=chat_response.choices[0].message.content))
        
        dv_response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_prompt(statement),
            temperature=0.6,
            max_tokens=1000
        )
        data = dv_response.choices[0].text[2:]

        data = json.loads(data)
        print(data)
        if 'N/A' not in data.values():
            dv_response.choices[0].text = 'Please take a look at the following options:'
            return redirect(url_for("index", result=dv_response.choices[0].text))
        
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=follow_up_prompt(data['start_date'], data['end_date'], data['price_range'], data['location']),
            temperature=0.6,
            max_tokens=1000
        )

        return redirect(url_for("index", result=response.choices[0].text))
        # print(dv_response)
        # print (dv_response.choices[0].text)
        # print(response['choices'][3])
        # return redirect(url_for("index", result=chat_response.choices[0].message.content))

    result = request.args.get("result")
    # arr_result = result[2:]
    # print(arr_result)
    # print(len(result))
    return render_template("index.html", result=result)

# def make_arr(data):
#     return 0

def check_question(statement):
    w =  """Determine if the following statement is a question without punctuation. {}. Output True or False.""".format(statement)
    print (w)
    return w

def generate_prompt(statement, start_date='N/A', end_date='N/A', price_range='N/A', location='N/A'):
    # prompt = """Ask a question that retrieves all the data that is N/A in the following list:["start date":{}, "end date":{}, "price range":{}, "location":{} ]""".format(
    #     start_date,
    #     end_date,
    #     price_range,
    #     location
    # )
    # return prompt
    return """If provided, retrieve the start date, end date, price range, and location from the following sentence (Assume today's date is April 6th 2023, and change it according to the statement.): {}.
      Return the information in JSON format. Return the date in month/day/year format, the location in it's full address form.
      The values will default to N/A, but replace the values based on the input data given. 
      The JSON output should look like this: {{"start_date":"{}" , "end_date":"{}" , "price_range":"{}" , "location":"{}"}}. If any of the fields in this list are not filled, ask the user a follow up question to retreive the missing information.""".format(
        statement,
        start_date,
        end_date,
        price_range,
        location
    )

def follow_up_prompt(start_date='N/A', end_date='N/A', price_range='N/A', location='N/A'):
    prompt = """Ask a question that retrieves all the data that is N/A in the following list:["start date":{}, "end date":{}, "price range":{}, "location":{} ].""".format(
        start_date,
        end_date,
        price_range,
        location
    )
    return prompt
