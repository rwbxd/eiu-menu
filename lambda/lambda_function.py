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
        hallSlot = ask_utils.get_slot(handler_input=handler_input, slot_name="hall")
        try:
            hallID = hallSlot.resolutions.resolutions_per_authority[0].values[0].value.id
        except:
            hallID = "ALL"
        
        dateValue = ask_utils.get_slot_value(handler_input=handler_input, slot_name="menuDate")
        if not dateValue:
            dateValue = date.today().strftime("%Y-%m-%d")
            
        menuName = ask_utils.get_intent_name(handler_input)
        if menuName == "BreakfastMenu":
            meal = 1
        elif menuName == "LunchMenu":
            meal = 2
        elif menuName == "DinnerMenu":
            meal = 3
        #Column to be scraped

        menuObj = self.pullMenus(dateValue)
        hallIndex = self.findMenus(hallID)
        
        if hallIndex:
            output = "; ".join(self.genOutput(menuObj, hallIndex, meal))
        else:
            output = "; ".join(self.allMenus(menuObj, meal))
        
        return (
            handler_input.response_builder
                .speak(output)
                .response
        )
        
    
    def pullMenus(self, dateValue):
        url = "https://www.eiu.edu/dining/dining_menu.php?date=" + dateValue
        webpage = urllib.request.urlopen(url)
        soup = BeautifulSoup(webpage, "html.parser")
        body = soup.find("tbody")
        menus = body.findAll("tr")
        return menus
            
    def findMenus(self, hall):
        if "STEVO" in hall:
            if hall == "STEVOGRILL":
                return [0]
            elif hall == "STEVODELI":
                return [1]
            else:
                return [0,1]
        elif hall in ["TAYLOR", "LAWSON"]:
            return [2]
        elif hall in ["THOMAS", "ANDREWS"]:
            return [3]
        elif hall in ["FOODCOURT"]:
            return [4]
        else:
            return None
            
    def genOutput(self, menuObj, indexList, meal):
        outputList = []
        for i in range(len(indexList)):
            outputList.append(self.scrapeMenu(menuObj, indexList[i], meal))
        
        return outputList
            
    def scrapeMenu(self, menuObj, menuIndex, meal):
        selectedMenu = menuObj[menuIndex]
        selectedMenuMeals = selectedMenu.findAll("td")
        returnvalue = selectedMenuMeals[meal].getText()
        
        returnvalue = returnvalue.replace("\r", ", ")
        for replaceText in ["\t", "\n", "\xa0", 
        " - Bonici Brothers Pizza and Pasta"]:
            if replaceText in returnvalue:
                returnvalue = returnvalue.replace(replaceText, " ")
        returnvalue = returnvalue.replace("&", "&amp;")
        returnvalue = returnvalue.replace('"', "&quot;")
        returnvalue = returnvalue.replace("'", "&apos;")
        for replaceText in ["Thomas", "Lawson", "Dessert"]:
            if replaceText in returnvalue:
                returnvalue = returnvalue.replace(replaceText, (",; " + replaceText))
        
        returnvalue = returnvalue.replace(("Dining Center Entrance Guideline Please enter the Dining Center on the side you "
        "intend to get your meal from.  You must eat from the side you enter. Thank you."), " ")
        
        return returnvalue
        
    def allMenus(self, menuObj, meal):
        outputList = self.genOutput(menuObj, [2,3,1,0,4], meal)
        outputList.insert(2, "Stevenson Deli: ")
        outputList.insert(4, "Stevenson Grill: ")
        outputList.insert(6, "Food Court: ")
        return outputList


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