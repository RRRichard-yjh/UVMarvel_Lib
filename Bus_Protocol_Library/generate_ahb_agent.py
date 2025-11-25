# @File    : generate_ahb_agent.py
# @desc    : AHB agent file generator (sanitised skeleton for open source).

import os
import json
import argparse
import requests
import re

# NOTE: API key string has been sanitised for open-source release.
os.environ["OPENAI_API_BASE"] = "api base"
os.environ["OPENAI_API_KEY"] = "api key"

model = "gpt-4.1"


def get_request(prompt, temperature=0.2, max_new_tokens=4096, model=model):
    """Placeholder for the actual LLM HTTP request.

    You need to fill in:
      - the URL of your model endpoint
      - request payload / headers
      - how to parse the response and return the generated text
    """
    raise NotImplementedError("Fill this function with your own HTTP call.")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='AHB File Generator (skeleton)')
    parser.add_argument(
        '-req',
        default='./PATH_TO_REQ_FILE.md',
        type=str,
        help='Path to requirements/specification file (placeholder)'
    )
    parser.add_argument(
        '-temp',
        default='./PATH_TO_AHB_TEMPLATE.sv',
        type=str,
        help='Path to AHB template skeleton (placeholder)'
    )
    parser.add_argument(
        '-interface',
        default='./PATH_TO_INTERFACE_FILE.sv',
        type=str,
        help='Path to interface description file (placeholder)'
    )

    args = parser.parse_args()

    with open(args.req, 'r', encoding='utf-8') as reqf:
        req_content = reqf.read()
    with open(args.temp, 'r', encoding='utf-8') as tempf:
        temp_content = tempf.read()
    with open(args.interface, 'r', encoding='utf-8') as interf:
        interface_content = interf.read()

    prompt = f"""
Generate code based on the template and requirements:  
1. Template file: {temp_content}, actual requirements file: {req_content}.  
2. Search for the 'ahb Interface Signals' section in {req_content} to confirm the specific signal names of the ahb interface.  
3. Check the content in {temp_content} to determine whether the existing interface naming matches that in {req_content}.  
   - If they are consistent, directly output the complete {temp_content} without any modifications.  
   - If they are inconsistent, replace all corresponding interface names and bit widths in {temp_content} with those from {req_content}, while keeping the rest of the logic unchanged, then output the complete modified code.
4. Replace all instances of 'ahb_interface_name' in {temp_content} with the specific interface name (including modport specification) obtained from {interface_content}.

Note: 
1. Signal name variations that only differ in letter case (e.g., "clk" vs "CLK") should also be considered inconsistent.
2. If the bit-width of any interface signal changes, the corresponding transaction fields in ahb_trans and all subsequent usage of those transactions must also be updated to match the new bit-width.
"""
    answer1 = get_request(prompt)
    print(answer1)

    with open(r"./answer1.md", "w", encoding='utf-8') as wf:
        wf.write(answer1)

    content = re.findall(
        r'```systemverilog([\s\S]+?)```',
        answer1,
        re.IGNORECASE
    )

    if content:
        output_file_name = "./PATH_TO_OUTPUT_AGENT_FILE.sv"
        with open(output_file_name, 'w', encoding='utf-8') as output_file:
            if len(content) > 0:
                output_file.write(content[0].strip())

            for code_block in content[1:]:
                output_file.write("\n\n" + code_block.strip())

        with open(output_file_name, 'r', encoding='utf-8') as f:
            ahb_agent_content = f.read()

        agent_output_dir = "./PATH_TO_AGENT_OUTPUT_DIR"
        os.makedirs(agent_output_dir, exist_ok=True)

        class_pattern = r'class (\w+).*?endclass : \1'
        class_matches = re.finditer(class_pattern, ahb_agent_content, re.DOTALL)

        for match in class_matches:
            class_name = match.group(1)
            class_content = match.group(0)
            class_content = f"import uvm_pkg::*;\n\n{class_content}"
            with open(os.path.join(agent_output_dir, f'{class_name}.sv'), 'w', encoding='utf-8') as f:
                f.write(class_content)

        # Remove the original combined agent file once split
        os.remove(output_file_name)


