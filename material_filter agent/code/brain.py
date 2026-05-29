from dataclasses import dataclass
from llm_client import *
from prompts import *
from function import *
import os
@dataclass
class Decision:
    action: str
    say: str
    file_output: str
def _safe_json(raw):
    try:
        s = (raw or "").strip()
        i, j = s.find("{"), s.rfind("}")
        if i != -1 and j != -1 and j > i:
            import json
            return json.loads(s[i:j+1])
    except Exception:
        pass
    return None
class Brain:
    def __init__(self, client):
        self.client = client
        self.states_list = ["_FILTER","_FDA","_NANO","_PREDICT"]

    def _FILTER(self, msg):
        prompt = prompt_download(msg)
        answer = self.client.chat(prompt)
        data = _safe_json(answer)

        if data is None:
            return Decision(
                action="_FILTER",
                say="Failed to extract parameters. Please re-upload or check the input!",
                file_output=None
            )

        # 提取参数
        include_elements = data.get("include_elements", None)
        may_include_elements = data.get("may_include_elements", None)
        elements_exclude = data.get("elements_exclude", None)
        has_toxicity = data.get("has_toxicity", False)
        is_stable = data.get("is_stable", None)
        base_output = data.get("output_file", "output.csv")

        if base_output.lower().endswith(".csv"):
            base_name = base_output[:-4]
        else:
            base_name = base_output
        el_names = [e.lower() for e in include_elements] if include_elements else ["materials"]
        project_dir = f"data/{'_'.join(el_names)}"
        os.makedirs(project_dir, exist_ok=True)
        cod_output = f"{project_dir}/{base_name}_cod.csv"
        mj_output = f"{project_dir}/{base_name}_mj.csv"

        try:
            download_cod(
                include_elements=include_elements,
                may_include_elements=may_include_elements,
                has_toxicity=has_toxicity,
                output_file=cod_output
            )

            get_materials_data(
                api_key="VDf8uPu9uEYdjVQtXghUSrDNs3cPaVet",
                elements_include=include_elements,
                elements_exclude=elements_exclude,
                is_stable=is_stable,
                output_file=mj_output
            )

            action = "_FDA"
            say = (
                f"✅ Step 1/4 — Database download complete.\n"
                f"Downloaded materials from COD and Materials Project:\n"
                f"  • COD: {cod_output}\n"
                f"  • Materials Project: {mj_output}\n\n"
                f"Next: FDA screening — filter materials by FDA approval status.\n"
                f"Proceed with FDA screening? (yes / no)"
            )
            file_output = [cod_output, mj_output]

        except Exception as e:
            action = "_FILTER"
            say = f"Error during processing: {e}"
            file_output = None

        return Decision(action=action, say=say, file_output=file_output)


    def _FDA(self, msg, file_paths=None):
        prompt = prompt_yes(msg, step="Proceed with FDA screening? (yes / no)")
        answer = self.client.chat(prompt)
        data = _safe_json(answer)

        if data is None:
            return Decision(
                action="_FDA",
                say="Could not understand your response.",
                file_output=None
            )

        output = data.get("Answer")

        if output == "Yes":
            if not file_paths:
                say = "Could not find files from the previous step. Please restart the screening."
                action = "_FILTER"
                return Decision(action=action, say=say, file_output=None)

            cod_output, mj_output = file_paths
            neo4j_db = Neo4jFDA(
                    uri="bolt://localhost:7687",
                    user="neo4j",
                    password="12345678"
            )
            cod_outfile, mj_outfile = process_files(cod_output, mj_output, self.client, neo4j_db)

            if cod_outfile or mj_outfile:
                say = (
                    f"✅ Step 2/4 — FDA screening complete.\n"
                    f"Filtered results (FDA-approved only):\n"
                    f"  • COD: {cod_outfile}\n"
                    f"  • Materials Project: {mj_outfile}\n\n"
                    f"Next: Nano screening — identify materials with plausible nano forms.\n"
                    f"Proceed with nano screening? (yes / no)"
                ) 
                action = "_NANO"
                file_output = [cod_outfile, mj_outfile]
            else:
                say = "File processing failed. Please check the input file format."
                action = "_FDA"
                file_output = None

        elif output == "No":
            action = "_FILTER"
            say = "FDA screening cancelled. To start a new screening, upload a requirements document."
            file_output = None

        else:
            action = "_FDA"
            say = "Could not determine your intent. Proceed with FDA screening? (yes / no)"
            file_output = None

        return Decision(action=action, say=say, file_output=file_output)

    def _NANO(self, msg, file_paths=None):
        prompt = prompt_yes(msg, step="Proceed with nano screening? (yes / no)")
        answer = self.client.chat(prompt)
        data = _safe_json(answer)
        if data is None:
            return Decision(
                action="_NANO",
                say="Could not understand your response.",
                file_output=None
            )

        output = data.get("Answer")

        if output == "Yes":
            if not file_paths:
                say = "Could not find files from the previous step. Please restart the screening."
                action = "_NANO"
                return Decision(action=action, say=say, file_output=None)

            cod_output, mj_output = file_paths

            cod_outfile, mj_outfile = process_nano(cod_output, mj_output, self.client)

            if cod_outfile or mj_outfile:
                say = (
                    f"✅ Step 3/4 — Nano screening complete.\n"
                    f"Filtered results (nano-materials only):\n"
                    f"  • COD: {cod_outfile}\n"
                    f"  • Materials Project: {mj_outfile}\n\n"
                    f"Next: Band gap prediction — use ML model to predict CBM/VBM.\n"
                    f"Proceed with band gap prediction? (yes / no)"
                )
                action = "_PREDICT"
                file_output = [cod_outfile, mj_outfile]
            else:
                say = "File processing failed. Please check the input file format."
                action = "_NANO"
                file_output = None

        elif output == "No":
            action = "_FILTER"
            say = "Nano screening cancelled. To start a new screening, upload a requirements document."
            file_output = None

        else:
            action = "_NANO"
            say = "Could not determine your intent. Proceed with nano screening? (yes / no)"
            file_output = None

        return Decision(action=action, say=say, file_output=file_output)

    def _PREDICT(self, msg, file_paths=None):
        prompt = prompt_yes(msg, step="Proceed with band gap prediction? (yes / no)")
        answer = self.client.chat(prompt)
        data = _safe_json(answer)
        if data is None:
            return Decision(
                action="_PREDICT",
                say="Could not understand your response.",
                file_output=None
            )

        output = data.get("Answer")

        if output == "Yes":
            if not file_paths:
                say = "Could not find files from the previous step. Please restart the screening."
                action = "_NANO"
                return Decision(action=action, say=say, file_output=None)

            cod_output, mj_output = file_paths

            out_dir = os.path.dirname(cod_output or mj_output) or "data"
            project_name = os.path.basename(out_dir)
            os.makedirs("result", exist_ok=True)
            pred_results = run_prediction(
                cod_nano_file=cod_output,
                mj_nano_file=mj_output,
                merged_output=f"result/{project_name}_predicted_results.csv",
            )

            if pred_results:
                say = (
                    f"✅ Step 4/4 — Band gap prediction complete.\n"
                    f"Merged result (MJ priority for duplicate formulas):\n"
                    f"  • {pred_results}\n\n"
                    f"All 4 steps finished. Download the result file above.\n"
                    f"To start a new screening, enter new database download requirements."
                )
                action = "_FILTER"
                file_output = [pred_results]
            else:
                say = "Prediction failed. Please check the input file format."
                action = "_PREDICT"
                file_output = None

        elif output == "No":
            action = "_FILTER"
            say = "Band gap prediction cancelled. Start a new screening? Upload a requirements document."
            file_output = None

        else:
            action = "_PREDICT"
            say = "Could not determine your intent. Proceed with band gap prediction? (yes / no)"
            file_output = None

        return Decision(action=action, say=say, file_output=file_output)


    def decide(self, msg, arg_paras):
            mode = arg_paras.get("mode")
            if mode == "_FILTER":
                decision = self._FILTER(msg)
            if mode == "_FDA":
                decision = self._FDA(msg)
            if mode == "_Nano":
                decision = self._NANO(msg)
            if mode == "_PREDICT":
                decision = self._PREDICT(msg)
            return decision
