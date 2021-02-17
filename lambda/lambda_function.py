# -*- coding: utf-8 -*-

import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

from datetime import date

import urllib.request
from bs4 import BeautifulSoup#, SoupStrainer
from html import escape

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Ask me what's for lunch or dinner and I'll read off the menu for you. You can specify dining hall if you wish."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class MenuIntentHandler(AbstractRequestHandler):
    """Handler for Menu Intents."""
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("LunchMenu")(handler_input) 
                or ask_utils.is_intent_name("DinnerMenu")(handler_input))
    
    def handle(self, handler_input):
        #What hall?
        hallSlot = ask_utils.get_slot(handler_input=handler_input, slot_name="hall")
        try:
            hallID = hallSlot.resolutions.resolutions_per_authority[0].values[0].value.id
        except:
            hallID = "ALL"
        
        #What day?
        dateValue = ask_utils.get_slot_value(handler_input=handler_input, slot_name="menuDate")
        if not dateValue:
            dateValue = ""
            
        #What meal?
        menuName = ask_utils.get_intent_name(handler_input)
        if menuName == "BreakfastMenu":
            meal = 0
        elif menuName == "LunchMenu":
            meal = 1
        elif menuName == "DinnerMenu":
            meal = 2

        if hallID == "ALL":
            page = self.pullA(dateValue, meal)
            output = [self.scrape(hall) for hall in page.findAll(class_="meal row")]
            print("initial output complete")
            output = ["In Taylor Dining:", output[2], "In Thomas Dining:", output[3],
            "At Stevenson Deli: ", output[1], "At Stevenson Grill: ", output[0],
            "At the Union: ", output[4]]
            print("output sorting complete")
            output = ";".join(output)
            print("output complete")
        else:
            page = self.pullH(hallID, dateValue, meal)
            output = self.scrape(page)
        
        return (
            handler_input.response_builder
                .speak(output)
                .response
        )
        
    def pullA(self, dateValue, meal):
        menu = self.pullMain(dateValue)
        menu = menu.findAll(class_="date-container")[0]
        menu = menu.findAll(class_="date-event")[meal]
        print("pullA complete")
        return menu
    
    def pullH(self, hallID, dateValue, meal):
        menu = self.pullMain(dateValue)
        menu = menu.findAll(class_="date-container")[1]
        menu = menu.findAll(class_="date-event")[self.numHall(hallID)]
        return menu.findAll(class_="meal row")[meal]
    
    def pullMain(self, dateValue):
        url = "https://www.eiu.edu/dining/dining_menu.php?date=" + dateValue
        webpage = urllib.request.urlopen(url)
        soup = BeautifulSoup(webpage, "html.parser")
        main = soup.find(class_="mainbodywrapper")
        print("pullMain complete")
        return main
    
    def numHall(self, hallID):
        hallDict = {"STEVOGRILL": 0, "STEVODELI": 1, "TAYLOR": 2, "LAWSON": 2,
                    "THOMAS": 3, "ANDREWS": 3, "FOODCOURT": 4}
        return hallDict[hallID]
    
    def scrape(self, page):
        list = [p.getText() for p in page.findAll("p")]
        list = [self.clean(item) for item in list]
        print("scrape complete")
        return "".join(list)
    
    def clean(self, item):
        item = item.replace("\r", ", ")
        for replaceText in ("\t", "\n", "\xa0",
        " - Bonici Brothers Pizza and Pasta", "- V"):
            if replaceText in item:
                item = item.replace(replaceText, " ")
        item = escape(item)
        for replaceText in ("Thomas Side", "Lawson Side", "Dessert", "Out Front"):
            if replaceText in item:
                item = item.replace(replaceText, (",; " + replaceText))
        print("clean complete")
        return item


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Ask me what's for lunch or dinner and I'll read off the menu for you. You can specify dining hall if you wish."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "See you later!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(MenuIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()