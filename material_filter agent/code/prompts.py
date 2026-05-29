# -*- coding: utf-8 -*-
def prompt_download(msg):
    sys = (
        "You are an expert in determining document content. "
        "The user uploaded a file. "
        "Please analyze the file and determine the following parameters required for the functions "
        "`download_cod` and `get_materials_data`. "
        "Extract only the parameters that are relevant, with duplicates merged. "
        "The parameters to extract are: include_elements, may_include_elements, elements_exclude, "
        "has_toxicity, is_stable, and output_file. "
        "The output must be strict minified JSON only, in the following format: "
        "{\"include_elements\":[], \"may_include_elements\":[], \"elements_exclude\":[], "
        "\"has_toxicity\":false, \"is_stable\":true, \"output_file\":\"filtered_materials.csv\"}. "
        "Each parameter should be inferred from the document if possible; "
        "if unknown, use reasonable defaults (empty list, false, or null)."
    )
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": msg}
    ]

def prompt_yes(msg, step=""):
    context = f" The user was asked: '{step}'" if step else ""
    sys = (
        "You are a language understanding assistant."
        f"{context}"
        "Determine whether the user's message expresses affirmation, negation, or uncertainty. "
        "Be flexible: 'sure', 'go ahead', 'ok', 'continue', 'proceed', 'yes please' → Yes. "
        "'no', 'stop', 'cancel', 'skip', 'not now' → No. "
        "Anything else ambiguous → Uncertain. "
        "Respond with a strict JSON object only, in the exact format: {\"Answer\": \"Yes\"}. "
        "The value of 'Answer' must be one of: \"Yes\", \"No\", \"Uncertain\". "
        "Do not include any explanations, punctuation, or extra text outside the JSON object."
    )
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": msg}
    ]

def prompt_fda(msg):
    sys = (
        "You are an FDA compliance assistant. "
        "Based on the chemical name provided, determine whether this chemical substance "
        "is approved by the FDA. "
        "Respond with a strict JSON object only, in the exact format: {\"answer\": \"yes\"} or {\"answer\": \"no\"}. "
        "The value of 'answer' must be either \"yes\" or \"no\". "
        "Do not include any explanations, punctuation, or extra text outside the JSON object."
    )
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": msg}
    ]

def prompt_nano(msg):
    sys = (
        "You are a nanomaterials identification assistant. "
        "Based on the chemical formula provided, determine whether this substance could potentially exist in a nanomaterial form. "
        "If it has any known or plausible nano-sized or nanostructured forms (including nanoparticles, nanocrystals, nanotubes, nanosheets, nanocomposites, etc.), respond {\"answer\": \"yes\"}. "
        "If it has no known or plausible nano-sized forms, respond {\"answer\": \"no\"}. "
        "Your output must be a strict JSON object in exactly one of the following two formats: "
        "{\"answer\": \"yes\"} or {\"answer\": \"no\"}. "
        "Do not add any explanation, description, or additional text."
    )
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": msg}
    ]
