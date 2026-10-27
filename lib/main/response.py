# responses for time/date queries
city_time_success = [
    "In {city}, it is {date} and the time is {time}.",
    "Right now in {city}, it's {date} and the time is {time}.",
    "The local time in {city} is {time} on {date}.",
    "Currently in {city}, it's {time} on {date}.",
    "{city}: {date}, {time} local time.",
]

city_time_fail = [
    "Sorry, I couldn't get the local time for {city}.",
    "I wasn't able to find the time for {city}.",
    "I couldn't retrieve the time for {city} right now.",
    "No time information available for {city}.",
    "I can't get the current time for {city} at the moment.",
]

local_time_success = [
    "In {city}, it is {date} and the time is {time} ({tz}).",
    "Right now in {city}, it's {date} and the time is {time} ({tz}).",
    "The local time here in {city} is {time} on {date} ({tz}).",
    "Currently in {city}, it's {time} on {date} ({tz}).",
    "{city}: {date}, {time} local time ({tz}).",
]

system_time_success = [
    "Today is {date} and the time is {time}.",
    "It's {date} and the time is {time} right now.",
    "The current date is {date} and the time is {time}.",
    "Right now, it's {time} on {date}.",
    "{date}, {time} local system time.",
]
# negative response for query that is not understandable
cannot_understand_user = [
    "Sorry, I didn't catch that",
    "I'm not sure if i understand",
    "Could you rephrase that?",
    "Hmm, I don't know about that",
    "I don't understand what you mean",
    "Im sorry, can you clarify?",
    "I didn't get that. Can you say it again?",
    "I’m not sure how to respond to that",
    "Sorry, I cannot process that request",
    "I don’t quite get it. Can you try again?",
]

# response when query is false in youtube search
cannot_understand_youtube = [
    "Sorry, I couldn't find that video on YouTube",
    "Hmm, I didn't understand which video to play",
    "I couldn't figure out what to play on YouTube",
    "Oops! That video doesn't seem to exist",
    "Sorry, I can't play that video right now",
    "I didn't get the video title, can you try again?",
    "Hmm, that request is unclear, please repeat",
    "I couldn't process your YouTube request",
    "That video seems unavailable or invalid",
    "Sorry, I don't know which video you mean",
]

cannot_find_app = [
    "Sorry, I couldn't find {app} in my database. Please check if it's added to the system",
    "I don't recognize the app '{app}'",
    "'{app}' is not available. Try another app or update my system commands",
    "I can't open '{app}' because it's not in my list",
]

cannot_understand_app_name = [
    "Sorry, which app did you mean?",
    "Could you repeat the app name for me?",
    "I didn’t quite catch the application you said",
    "What app should I open?",
    "Mind saying the app name again?",
]

cannot_find_whatsapp_contact = [
    "Sorry, I couldn't find a contact in your message. Please try again",
    "I wasn't able to identify a contact. Could you repeat the name or number?",
    "No contact found. Please specify who you want to message or call",
    "I need a contact name or number to proceed. Please try again",
]

cannot_send_whatsapp_message = [
    "Sorry, I couldn't send the WhatsApp message",
    "I was unable to deliver your WhatsApp message",
    "There was a problem sending your WhatsApp message",
    "I couldn't complete your WhatsApp request. Please try again",
]

welcome_back_user = [
    "Welcome back! Ivy is here to assist you 24/7 and 7 days a week",
    "Good to see you again. How can I help you today?",
    "Welcome back! Ready when you are",
]

ask_message_prompt_user = [
    "What message should I send?",
    "What would you like to say?",
    "Please tell me the message.",
    "What do you want to send?",
    "Okay, what's the message?",
    "Tell me the message to send.",
    "What should the message say?",
    "I'm ready. What's the message?",
]

city_not_found_user = [
    "Sorry, I couldn't find details for {city}. You can check the map: {map_url}",
    "I couldn't locate {city}. Try another city or see this map: {map_url}",
    "I couldn't get weather info for {city} right now. Map might help: {map_url}",
    "I can't find {city}. Would you like to open the map? {map_url}",
    "No results for {city}. Here's a map search you can use: {map_url}",
]

cannot_calculate = [
    "Sorry, I couldn't calculate that",
    "Hmm, I'm having trouble with that calculation",
    "I wasn't able to solve that math problem",
    "Oops, something went wrong with the calculation",
    "I can't figure out that math",
    "That calculation didn't work",
    "I'm unable to process that math expression",
    "Sorry, I encountered an error with that calculation",
]

error_in_allcommands = [
    "Oops, something went wrong on my end. Let's try that again!",
    "Unexpected error, I'm sorry, try again",
    "Sorry, there was a I.V.Y. error, please try again later",
    "Ivy will fix herself shortly, I.V.Y. system errored, my apologies for this",
    "It appears that I.V.Y. had a issue, please try again...",
    "I.V.Y. system malfunction, id: 8-4f6-9e6a-dasw5bc2",
    "Ivy Error id: 83196b-f063-4ff6-9e6a",
]

google_search_failures = [
    "I couldn't understand your Google search. Could you say it again?",
    "Sorry, I didn't catch that search. Please try rephrasing it",
    "Hmm, I'm not sure what you want me to look up. Can you say it again?",
    "I couldn't parse that search query. Try asking differently, please",
    "Sorry, I didn't understand the search. Could you repeat it?",
    "I’m not sure what to search for. Please tell me what you'd like me to look up",
    "That search wasn't clear to me. Can you try saying it another way?",
    "I couldn't get the search query. Mind repeating it?",
    "I'm having trouble understanding that search. Could you say it again more simply?",
    "I didn't understand your Google search. Can you try one more time?",
]

news_fetch_failures = [
    "Sorry, I couldn't get the news right now. Please try again in a moment",
    "I’m having trouble fetching the news. Try again shortly",
    "I can’t reach the news service at the moment. Please try later",
    "Oops — I couldn't load the headlines. Would you like me to try again?",
    "I couldn't get the latest news just now. Check your connection or try again",
    "The news feed is unavailable right now. I'll try again in a bit",
    "Sorry, I'm unable to fetch news at the moment. Please try again soon",
    "I couldn't retrieve today's headlines. Want me to retry?",
    "News isn't loading right now. Please give me a moment and try again",
    "I’m having trouble connecting to the news source. Please try again later",
]


copy_me_response = [
    "Got it, talk now",
    "Sure, go speak now",
    "Repeating after you",
    "Alright, i will listen carefully.",
]

copy_me_failed = [
    "I didn’t catch that. Try again, please",
    "Sorry, I didn’t catch that. Could you say it again?",
    "I couldn't hear you clearly. Please repeat",
    "Hmm, I missed that. Can you say it once more?",
    "I didn't get that. Could you repeat it, please?",
    "I’m not hearing you clearly. Try saying that again",
    "Pardon, I didn't catch that. Could you repeat?",
    "I didn't catch that last part. Please try again",
    "I couldn't hear that. Can you speak up and repeat?",
    "I missed what you said. Please try one more time",
]

cannot_find_wikipedia = [
    "I couldn't find any of that in Wikipedia ",
    "There doesn't appear to be a Wikipedia page for that",
    "Wikipedia appears to be unavailable right now",
]
