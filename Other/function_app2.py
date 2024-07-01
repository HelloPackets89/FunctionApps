import azure.functions as azfunc
#This imported the Azure Functions SDK. I've always visualised SDKs as a sort of Ikea flatpack box, except for programmers. I didn't think using an SDK would be this simple though. 
#The original template imports this as 'func' but I've changed it to 'azfunc' just to make it more clear that its the SDK and not a python shorthand. 
import logging
#straight forward

app = azfunc.FunctionApp(http_auth_level=azfunc.AuthLevel.FUNCTION)
#This creates an instance of the 'FunctionApp' class within the code. FunctionApp is basically a blueprint from the SDK for creating a "function app object". 
#The section in brackets () defines what level of authentication is needed. ANONYMOUS is no auth, FUNCTION requires the function key and ADMIN requires the master key. 
#What is a class? A class is the blueprint, it defines how an object is created. Providing structure and methods for performing a specific task.  
#What is an object? It is something that is built based on a blueprint. The objects below are HttpRequest and HttpResponse.
#By creating this instance, I don't need to define what those two objects actually are. Which is good because I wouldn't know how. 

@app.route(route="http_trigger1")
#This uses app.route as a decorator to define a route for the function app. So if a HTTP request is made to my function app followed by the trigger /http_trigger1, the below function will activate.
#What is a route? A route is a pathway that can be taken within an application. The route is functionappurl.com/http_trigger1
#What is a decorator? Decorators are sort've layered functions. Do this but also do that with it. E.g You can have 'Hello World!' and create a decorator for it that converts all letters to uppercase to produce 'HELLO WORLD!'.

def http_trigger1(req: azfunc.HttpRequest) -> azfunc.HttpResponse: 
#this defines the http_trigger1 function. It notes that it requires the HttpRequest object to function. 
#"-> azfunc.HttpResponse:" is something that is referred to as 'type hinting'. It advises that the expected response here is a HttpResponse
#What is Type Hinting? Type Hinting is something you add to your code to improve readability and to know what the intention of the code is. 
#The difference between commenting and Type Hinting is that Type Hinting can be used by some tools for error checking and debugging. They're kind of like comments but for your tools. 
#Imagine an interesting future where the Natural Language from comments could be used for Type Hinting.
#I expressed the above idea to Bing and then it showed me an example of a Natural Language comment being interpreted as a type hint. 
#Bing is just showing off now. 
    logging.info('Python HTTP trigger function processed a request.')
#Straight forward, performs a logging action. I assume the .info refers to the fact that this is just information, not an error message or anything. 
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')
#This script is trying to get the ‘name’ value from the request parameters. If ‘name’ is not provided in the parameters, it then tries to get ‘name’ from the JSON body of the request.
#If ‘name’ is not in the JSON body or if the body is not valid JSON, name will be None.
#If ‘name’ is found in either the parameters or the JSON body, it will be assigned to the name variable. If ‘name’ is not found in either place, name will be None.
#So basically when a HTTP request is made to the function app url, it needs to include a parameter that defines a name. E.g "Name=Brandon". If there is no name then it'll check if there is one in the JSON body. If not found then nothing happens. 
    if name:
        return azfunc.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return azfunc.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
#The above is straight forward. The previous block was looking for a name because it wants to pass that name into this block. So it takes that parameter and places it into the {name} field.
#If there is no name then it tells you to include a name in the query string. 

#Running this code 
#HTTP Method : Get / POST (If using JSON body)
#Key = The URL of my functionapp
#Query parameters 'name:brandon' or no name
#Headers. None / Content-Type:application/json (If using JSON body)