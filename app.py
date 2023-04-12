import os
import json
import openai
from flask import Flask, redirect, render_template, request, url_for
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
openai.api_key = os.getenv("OPENAI_API_KEY")


@app.route("/", methods=("GET", "POST"))
@cross_origin()
def index():
    if request.method == "POST":
        data = json.loads(request.data)
        statement = data['statement']
        bookingDetails = json.loads(data['details'])
        chat_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are an assistant that only speaks JSON. Do not write normal text. 
                For my following statements, give me a JSON response telling me whether the statement is a question or not. 
                The output should be in this format:
                {{
                “is_question”: true/false
                }}"""},
                {"role": "assistant",
                    "content": "I can provide you with the requested JSON response. Please provide me with the statement(s) you want me to analyze."},
                {"role": "user", "content": statement}
            ],
            # temperature=0.6,
            max_tokens=1000
        )

        json_val = {"is_question": False}

        try:
            json_val = json.loads(chat_response.choices[0].message.content)
            print(json_val)
        except:
            print("could not determine question")

        if json_val["is_question"] == True:
            messages = data['message_history']
            messages.append({"role": "user", "content": statement})
            chat_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                # temperature=0.6,
                max_tokens=1000
            )
            output = chat_response.choices[0].message.content
            message = {"role": "assistant", "content": output}
            messages.append(message)
            return {
                "message": chat_response.choices[0].message.content,
                "is_booking": False,
                "details": bookingDetails,
                "message_history": messages
            }
            # return redirect(url_for("index", result=chat_response.choices[0].message.content))
        messages = data['message_history']
        message_hist = data['message_h']
        try:
            message_hist.append({"role": "user", "content": statement})
            messages.append({"role": "user", "content": statement})

            dv_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=message_hist,
                # temperature=0.6,
                max_tokens=1000
            )

            print(dv_response.choices[0].message.content)

            output_dict = json.loads(dv_response.choices[0].message.content)
            # if None not in output_dict.values():
            message_hist.append(
                {"role": "assistant", "content": dv_response.choices[0].message.content})
            messages.append(
                {"role": "assistant", "content": output_dict['follow_up_question']})

            # print(dv_response.choices[0].message.content)

            return {
                # "message": output_dict['follow_up_question'],
                "message": output_dict['follow_up_question'],
                "is_booking": True,
                "details": {
                    "start_date": output_dict['start_date'],
                    "end_date": output_dict['end_date'],
                    "budget": output_dict['budget'],
                    "location": output_dict['location']
                },
                "message_h": message_hist,
                "message_history": messages
            }
        except:
            return {
                "message": "Sorry, I don't understand. Please try again.",
                "is_booking": True,
                "details": bookingDetails,
                "message_h": message_hist,
                "message_history": messages
            }

        dv_response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_prompt(statement, bookingDetails),
            temperature=0,
            max_tokens=1000
        )
        print(dv_response.choices)
        data = dv_response.choices[0].text[2:]
        data = json.loads(data)

        for key in data:
            if data[key] is not None:
                bookingDetails[key] = data[key]

        print(data)

        print(bookingDetails)

        if None not in bookingDetails.values():
            return {
                "message": "Booking details: {}".format(bookingDetails),
                "is_booking": True,
                "details": bookingDetails
            }

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=follow_up_prompt(bookingDetails),
            temperature=0.6,
            max_tokens=1000
        )

        print(response.choices[0].text)

        return {
            "message": response.choices[0].text[2:],
            "is_booking": True,
            "details": bookingDetails
        }
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
    w = """Determine if the statement is a question. Your output should look like this: {{"is_question": true/false}}. Here is the statement: {}. """.format(
        statement)
    print(w)
    return w


def generate_prompt(statement, bookingDetails):
    # prompt = """Ask a question that retrieves all the data that is N/A in the following list:["start date":{}, "end date":{}, "price range":{}, "location":{} ]""".format(
    #     start_date,
    #     end_date,
    #     budget,
    #     location
    # )
    # return prompt

    prompt = """If provided, retrieve the start date, end date, budget, and location from the following sentence (Assume today's date is April 9th 2023): {}.
      Return the information in JSON format. Return the date in MM/DD/YYYY format; return the location as the airport code of the airport closest to the user's desired location.
      The values will default to null, but replace the values based on the input data given. Do not change a value if it is not null unless the user provides a new value for that field.
      The JSON output should look like this: {}. There must always be a JSON output in the required format. If any values are null, ask a follow up question to retrieve all null values.""".format(
        statement,
        json.dumps(bookingDetails)
    )
    print(prompt)
    return prompt


def follow_up_prompt(bookingDetails):
    prompt = """Ask a question that retrieves all missing data for this trip if it is null in the following JSON object:{}""".format(
        json.dumps(bookingDetails)
    )
    print(prompt)
    return prompt


# if __name__ == "__main__":
#     app.run(host='localhost', debug=True)
