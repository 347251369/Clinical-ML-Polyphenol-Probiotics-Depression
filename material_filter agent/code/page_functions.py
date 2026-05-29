def text_submit(chat, user_msg, arg_brain, arg_paras):
    user_msg = user_msg.strip()

    if not user_msg:
        chat.append((user_msg, "Please input text."))
        return chat, "", arg_brain, arg_paras, None

    brain = arg_brain.get("brain")
    mode = arg_paras.get("mode", "_FILTER")

    if mode == "_FDA":
        file_paths = arg_paras.get("file_output")
        result = brain._FDA(user_msg, file_paths=file_paths)
    elif mode == "_NANO":
        file_paths = arg_paras.get("file_output")
        result = brain._NANO(user_msg, file_paths=file_paths)
    elif mode == "_PREDICT":
        file_paths = arg_paras.get("file_output")
        result = brain._PREDICT(user_msg, file_paths=file_paths)
    else:
        result = brain.decide(user_msg, arg_paras)

    arg_paras["mode"] = result.action
    if getattr(result, "file_output", None):
        arg_paras["file_output"] = result.file_output

    chat.append((user_msg, result.say))

    return chat, "", arg_brain, arg_paras, getattr(result, "file_output", None)
