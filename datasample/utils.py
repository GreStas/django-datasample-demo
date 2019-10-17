def add_message(messages: dict, key, message):
    try:
        messages[key].append(message)
    except KeyError:
        messages[key] = [message]
